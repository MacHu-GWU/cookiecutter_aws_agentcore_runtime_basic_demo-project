---
description: "How AgentCore Runtime sessions map to microVMs, where the time of one agent invocation goes (cold vs warm), and how to keep both the agent's and its MCP server's microVMs warm: reuse runtimeSessionId per conversation, and one MCP session per agent session. Read when an invocation is slow, when writing a client that invokes a runtime, or when an agent connects to an MCP server on AgentCore Runtime."
---

# Runtime Sessions and Cold Starts

---

## 1. The rule: one session, one microVM

AgentCore Runtime gives each **runtime session** its own microVM. The session ID decides which microVM a request goes to:

- **A new session ID** means a new microVM, so a cold start.
- **The same session ID** goes back to the microVM that is already running, so it is warm.

| Fact | Value (defaults) |
| :--- | :--- |
| Session ID length | at least 33 characters |
| Idle timeout (`idleRuntimeSessionTimeout`) | 900 s (15 min); each invocation resets it |
| Max lifetime of one microVM (`maxLifetime`) | 28800 s (8 h); cannot be reset |
| After either timeout | the microVM is stopped, but the session ID stays valid; the next request starts a new microVM (cold again) |
| Code version | a microVM keeps the code it started with; a deploy reaches only new microVMs |

Which header carries the session depends on the runtime's protocol:

| Protocol | Session header | Who picks the ID |
| :--- | :--- | :--- |
| HTTP, A2A, AG-UI | `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id` (the `runtimeSessionId` parameter of `InvokeAgentRuntime`) | the caller |
| MCP | `Mcp-Session-Id` | the platform, on the first request; the client must send it back on every later request |

Sources (look up through the docs MCP, see `01`):
- `runtime-sessions.md`
- `runtime-lifecycle-settings.md`
- `runtime-mcp-protocol-contract.md` (section "MCP session management and microVM stickiness")

---

## 2. Where the time of one agent invocation goes

The setup: a caller sends one prompt to an agent runtime. The agent connects to an MCP server, which runs as a second runtime, and answers with the LLM. Split the wall-clock time into five segments:

| # | Segment | What happens | Cold | Warm |
| :--- | :--- | :--- | :--- | :--- |
| T1 | Agent microVM | AgentCore routes the request; a new session gets a microVM (restored from a snapshot) | 1–3 s | ~0 s |
| T2 | Agent process start | Python starts: imports, framework, OpenTelemetry init, then the app is ready | 1–3 s | ~0 s |
| T3 | MCP connect | `initialize` + `tools/list` to the MCP runtime. A new MCP session pays that runtime's own T1 + T2 here | 3–6 s | 0.1–0.3 s |
| T4 | Agent loop | LLM calls, tool calls (each MCP tool call is one more round trip to the MCP microVM) | 2–4 s | 2–4 s |
| T5 | Return | the answer goes back to the caller (plus the client's own startup, such as a CLI) | 0.2–1 s | 0.2–1 s |

The numbers are a **general illustration** of the order of magnitude, not a benchmark. Measure your own runtime by comparing log timestamps; section 5 says how.

T4 is the real work, and it costs the same everywhere. Run locally, an invocation is roughly T4 + T5, which is why it feels fast.

---

## 3. Three ways to call it, compared

| Scenario | Agent session | MCP session | T1 | T2 | T3 | T4 | T5 | Total |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A.** Nothing reused (the default) | new on every call | new on every call | 2 | 2 | 5 | 3 | 0.5 | **~12.5 s** |
| **B.** Caller reuses the agent session | same | new on every call | 0 | 0 | 5 | 3 | 0.5 | **~8.5 s** |
| **C.** Agent also reuses its MCP session | same | same | 0 | 0 | 0.2 | 3 | 0.5 | **~3.7 s** |

What the table shows:

- **A** is what you get from a quick test: every call is two cold starts in a row, first the agent's and then the MCP server's. Calling twice in a row does not help, because each call is a new session.
- **B** is the common trap. The caller did its part, and the agent microVM is warm, but the agent opens a new MCP connection on every call. That makes a new MCP session, so the MCP runtime pays a cold start every time.
- **C** reaches local speed from the second message on. Only the first message of a conversation pays the cold starts.

---

## 4. The playbook

### 4.1 Caller: one `runtimeSessionId` per conversation

- Make one session ID per user conversation (such as `f"{user_id}-{uuid4()}"`, at least 33 characters), keep it on the client side, and send it with every message of that conversation.
- Never share a session ID between users. AgentCore does not map sessions to users; the caller owns that mapping.
- With the AgentCore CLI, pass `--session-id <id>` to `agentcore invoke`. Without it, every invoke is a new session (scenario A).

### 4.2 Agent → MCP: one MCP session per agent session

Since one agent microVM serves exactly one runtime session, **"one MCP connection per agent process" is the same thing as "one MCP session per agent session"**. Use that:

- Create the MCP client once per process, lazily on the first invocation, and keep it open. Do not create it inside each invocation and close it at the end. The MCP client library captures the `Mcp-Session-Id` from the first response and sends it on every later request, so every call of the conversation lands on the same MCP microVM.
- Create it inside the handler (lazily), not at import time. A session's microVM is restored from a snapshot taken before any session existed. A boto3 session or credentials object made at import time holds pre-snapshot credentials. This applies to the SigV4 signer that authenticates to the MCP runtime.
- Reconnect on failure. If the MCP side was stopped (idle timeout, max lifetime, unhealthy), the session ID stays valid and the next request just starts a new MCP microVM (a cold T3 once). If the connection itself errors, drop the cached client and make a new one.
- If several requests can run at once in one agent microVM, make sure the shared MCP client is safe to share, or guard it with a lock.
- Keep the MCP runtime's `idleRuntimeSessionTimeout` at least as long as the agent's. Otherwise the MCP microVM stops while the agent's conversation is still alive, and the next message pays a cold T3.

Stateless MCP servers (`stateless_http=True`, the default this repo uses) still get microVM stickiness from `Mcp-Session-Id`. Reusing the session is about speed, not about server state.

### 4.3 Making the first message cheaper

The first message of a conversation always pays T1 + T2 (+ a cold T3). To make that smaller:

- Keep the deployment package small and the imports light. Import heavy libraries lazily, in the code path that needs them.
- Warm up ahead: when a user opens the chat UI, send a cheap invocation (or a ping) with the new session ID before they type.
- Set the lifecycle settings to the use case (`runtime-lifecycle-settings.md` has a table: interactive chat 10–15 min idle, development about 5 min). A longer idle timeout keeps more warm hits, but the microVM stays up longer.

---

## 5. How to check where the time goes

- Each runtime session writes its own CloudWatch log stream under `/aws/bedrock-agentcore/runtimes/<runtime>-DEFAULT`. **A new log stream per invocation means a new session (cold).**
- Read the agent's log timestamps: process start (T2) → request received → first MCP response (T3) → answer returned (T4). A long gap before the first MCP response is a cold MCP microVM.
- Time the same prompt three times with the same `--session-id`. The first call is cold. If calls 2 and 3 are still much slower than a local run, the MCP session is not reused (scenario B).
