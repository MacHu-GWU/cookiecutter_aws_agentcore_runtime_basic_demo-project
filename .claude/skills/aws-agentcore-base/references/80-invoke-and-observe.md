---
description: "OP-8 Invoke and Observe: calling the deployed runtimes from a client program (find the runtime ARN, InvokeAgentRuntime for an agent, MCP over SigV4), runtime sessions and how they map to microVMs, where the time of one invocation goes (cold vs warm) and how to keep it warm, the logs of a runtime and how to read them, QUICK_LINKS.md with the console of every resource, the integration tests against a deployed environment, and the invocation failures met so far. Read before writing a client that calls a deployed runtime, when an invocation is slow or fails, or to read a runtime's logs."
---

# Invoke and Observe

Implements **OP-8**. The quick checks after a deploy are the generated `ac-status`, `ac-invoke`, and `ac-test` tasks (`60-deploy.md`, section 4); this file is about calling the runtimes from code, and about what happens inside.

| | |
| :--- | :--- |
| EP | `<package_name>/devtools/agentcore_client.py` |
| FP | `<package_name>/devtools/agentcore_client.py`, `<package_name>/devtools/mcp_client.py` (its `auth`), `get_deployed_mcp_connection` of `<package_name>/runtimes/mcp_connection.py`, `<package_name>/devtools/quick_links.py`, `.mise/tasks/gen-quick-links.py`, `QUICK_LINKS.md`, the console URL helpers of `config_01_name.py`, the AgentCore clients of `<package_name>/one/one_02_boto_ses.py`, the `ac-logs` step of `<package_name>/agentcore_project/mise_tasks.py`, `tests_int/test_agentcore_runtimes.py`, `tests/devtools/test_devtools_agentcore_client.py` |
| CMD | `mise run int-test` (needs a deploy; calls the model); `mise run gen-quick-links` (reads AWS); `mise run ac-logs-<env>-<slug>`; `mise run ac-invoke-<env>-<slug>`; unit tests below |

---

## 1. Calling a deployed runtime from code

`<package_name>/devtools/agentcore_client.py`; every function takes its AWS clients or session as arguments (from `one`: `one.bedrock_agentcore_client`, `one.bedrock_agentcore_control_client`, `one.boto_ses`):

| Step | Function | How |
| :--- | :--- | :--- |
| Find the runtime | `find_runtime_arn(control_client, physical_name)` | `ListAgentRuntimes`, matched on `agentRuntimeName` = `agentcore_runtime_physical_name_<x>` of the config. The ARN ends in an ID assigned at deploy time, so it is looked up, never built |
| Call an agent | `invoke_agent_runtime(client, arn, payload, session_id=None)` | `InvokeAgentRuntime` with the JSON payload, qualifier `DEFAULT`; returns the JSON answer and the runtime session ID it ran in |
| Call an MCP runtime | `get_deployed_mcp_connection(arn, boto_session)` of `runtimes/mcp_connection.py`, then `list_tools(url, auth=auth)` / `call_tool(url, name, arguments, auth=auth)` of `mcp_client.py` | the invocation URL of the ARN, every request signed with SigV4, exactly as an agent runtime calls it (`40-agent-runtime.md`, section 4) |
| Start a conversation | `new_session_id(prefix)` | `<prefix>-<uuid4>`, at least 33 characters |

The caller needs `bedrock-agentcore:InvokeAgentRuntime` on the runtime and `bedrock-agentcore:ListAgentRuntimes`; a developer's profile of the environment usually has both.

The AgentCore CLI does the same without code: `agentcore invoke --target <env> --runtime <Runtime> --payload '<json>' [--session-id <id>]`, which the `ac-invoke` tasks wrap.

---

## 2. Runtime sessions

**One runtime session, one microVM.** The session ID decides which microVM a request goes to:

- a new session ID is a new microVM: a cold start;
- the same session ID goes back to the microVM already running: warm.

| Fact | Value (defaults) |
| :--- | :--- |
| Session ID length | at least 33 characters |
| Idle timeout (`idleRuntimeSessionTimeout`) | 900 s; each invocation resets it |
| Max lifetime of a microVM (`maxLifetime`) | 28800 s (8 h); cannot be reset |
| After either timeout | the microVM stops, the session ID stays valid; the next request starts a new microVM (cold again) |
| Code version | a microVM keeps the code it started with; a deploy reaches new microVMs only |

| Protocol | Session carried by | Who picks the ID |
| :--- | :--- | :--- |
| HTTP (agent) | `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id`, the `runtimeSessionId` of `InvokeAgentRuntime` | the caller |
| MCP | `Mcp-Session-Id` | the platform, on the first request; the client sends it back on every later one |

**The caller's rules:**

- One session ID per conversation, kept on the client, sent with every message of that conversation; a new conversation gets a new ID.
- Never share a session ID between users: AgentCore does not map sessions to users, the caller does.
- One process serves one session, so an agent runtime keeps one agent per process (`40-agent-runtime.md`, section 3): it remembers the conversation, and keeps its MCP session open.

Sources, through the docs MCP (`00-agentcore-docs-mcp.md`): `runtime-sessions.md`, `runtime-lifecycle-settings.md`, `runtime-mcp-protocol-contract.md`.

---

## 3. Where the time of one invocation goes

A caller sends one prompt to an agent runtime, which calls an MCP runtime and its model:

| # | Segment | Cold | Warm |
| :--- | :--- | :--- | :--- |
| T1 | the agent's microVM: a new session gets one, restored from a snapshot | 1–3 s | ~0 |
| T2 | the agent's process starts: imports, framework, telemetry | 1–3 s | ~0 |
| T3 | MCP connect (`initialize`, `tools/list`); a new MCP session pays the MCP runtime's own T1 + T2 | 3–6 s | 0.1–0.3 s |
| T4 | the agent loop: model calls, tool calls | 2–4 s | 2–4 s |
| T5 | the answer back to the caller | 0.2–1 s | 0.2–1 s |

The numbers show the order of magnitude, not a benchmark. Three ways to call:

| Scenario | Agent session | MCP session | Roughly |
| :--- | :--- | :--- | :--- |
| A. nothing reused | new each call | new each call | ~12 s: two cold starts in a row, every call |
| B. the caller reuses its session | same | new each call | ~8 s: the MCP runtime is cold every time |
| C. the agent also keeps its MCP session | same | same | ~4 s from the second message: local speed |

This template is C, as long as the caller reuses its session ID. To make the first message cheaper: keep the `agentcore` dependency group small and import heavy libraries lazily; warm up with a cheap call when a user opens the chat; set the lifecycle timeouts to the use case, and keep the MCP runtime's idle timeout at least the agent's.

**Measure it:** call the same prompt three times with one session ID (`SESSION_ID=<id> mise run ac-invoke-<env>-<slug>`, or `invoke_agent_runtime` with the same ID). The first is cold. If the second and third are still much slower than a local run, the MCP session is not reused. A new log stream per call means a new session.

---

## 4. Logs

| What | Where |
| :--- | :--- |
| A runtime's log group | `/aws/bedrock-agentcore/runtimes/<runtime ID>-DEFAULT` (`get_runtime_log_group(arn)`); the runtime ID is the last part of the ARN |
| A session | its own log stream in that group |
| A healthy start | the line `main()` prints: `Loaded the config of '<env>' on runtime 'agentcore'`, plus what that `main()` prints about its own dependencies |
| A failed call | the traceback, in the stream of that session |

```bash
mise run ac-logs-<env>-<slug>
```

```bash
SINCE=2h mise run ac-logs-<env>-<slug>
```

The task runs `agentcore logs runtime --name <Runtime> --target <env> --since ${SINCE:-30m}`; the CLI also takes `--tail`, `--level`, `--query`. The runtime ID is known only after a deploy: `ac-status-<env>`, the stack's console URL, or `aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/<physical name>`.

To read where the time went: process start (T2), request received, first MCP response (T3), answer returned (T4). A long gap before the first MCP response is a cold MCP microVM.

### 4.1 `QUICK_LINKS.md`: the console of every resource

```bash
mise run gen-quick-links
```

`<package_name>/devtools/quick_links.py` (through the thin `.mise/tasks/gen-quick-links.py`) writes `QUICK_LINKS.md` at the repo root, one table per environment, only when it changed:

| Rows | Built from |
| :--- | :--- |
| every CDK stack, the AgentCore stack, the config parameter | the local config files, no AWS call |
| per runtime: its console page (`get_agentcore_runtime_url`), its execution role (`get_iam_role_url`), its log group (`get_cloudwatch_log_group_url`) | AWS, read only, with the environment's profile: `find_deployed_runtimes` of `agentcore_client.py` (`ListAgentRuntimes`, then `GetAgentRuntime` for the role) |

A runtime that is not deployed is one row saying so; an environment whose runtimes cannot be read (no profile, no access) says `not read (<error type>)`; an environment whose config does not load gets an error line. The file is committed, so it holds no account ID and no error message (both may be private): every link is built from a name or an ID. Run it again after a deploy or a teardown, since a redeploy can change a runtime's ID and role.

---

## 5. Integration tests

`tests_int/test_agentcore_runtimes.py`, run with the other integration tests against the environment of `ENV_NAME`:

```bash
mise run int-test
```

```bash
ENV_NAME=tst mise run int-test
```

One test per runtime of the registry, from its `sample_payload`, so a new runtime is covered without a new test:

- **An MCP runtime**, found by its physical name: lists its tools over SigV4, and answers its sample `tools/call`; a tool error fails the test.
- **An agent runtime**: answers its sample prompt and then a follow-up in one new session, and both run in that session.

They need the environment deployed, and the agent tests call the models: ask before relying on them. A runtime whose sample payload does not suit a deployed environment (it writes data, say) gets its own check here instead.

---

## 6. Invocation failures met so far

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `400` with `{"error": [{"loc": ["prompt"], ...}]}` | the payload does not match the agent's request model | send the fields of `<Agent>Request` (`40-agent-runtime.md`, section 2) |
| `Received error (500) from runtime` | an exception in the runtime | read the session's log stream (section 4): the traceback is there |
| `config SSM parameter ... does not exist` in the log, at startup | the config was never deployed, or was deleted | `mise run config-deploy-<env>` |
| `AccessDeniedException` for a Bedrock model, `agreementAvailability` `NOT_AVAILABLE` | the model's agreement is not available in the account, whatever the console's model access page shows | use a model the account can call (check with `aws bedrock get-foundation-model-availability`); never accept a Marketplace agreement for the user |
| `ValidationException: ... Access to Bedrock models is not allowed for this account` | the profile signs in to another account than the config's | point `AWS_PROFILE_FOR_<ENV>` in `.env` at the config's account; run through mise |
| an MCP call returns 403 | the `bind()` grant is missing, or the signature is wrong | check the `bind()` line (`50-agentcore-project-layout.md`, section 4) and the region of the signer |
| an MCP call returns 404 | the URL is wrong | check `get_runtime_mcp_url`: the URL-quoted ARN and `qualifier=DEFAULT` |
| `no deployed runtime named ...` | not deployed in that account and region, or another environment | `mise run ac-status-<env>` |
| a deploy does not change the answers | a running session keeps its code | a new session ID gets the new code |

---

## 7. Unit tests

| Test file | Covers |
| :--- | :--- |
| `tests/devtools/test_devtools_agentcore_client.py` | session IDs; the ARN lookup over pages, and a missing runtime (botocore `Stubber`); the log group; `invoke_agent_runtime` with its session |
| `tests/devtools/test_devtools_mcp_client.py` | the client against a real local server, with and without an auth on every request |
| `tests/agentcore_project/test_agentcore_project_mise_tasks.py` | the generated `ac-invoke` and `ac-logs` tasks |

```bash
.venv/bin/python tests/devtools/test_devtools_agentcore_client.py
.venv/bin/python tests/devtools/test_devtools_mcp_client.py
```
