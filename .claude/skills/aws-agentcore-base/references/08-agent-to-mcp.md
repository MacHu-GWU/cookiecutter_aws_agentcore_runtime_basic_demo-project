---
description: "How an agent runtime finds and calls an MCP runtime: bind() in cdk-stack.ts grants the call and sets AGENTCORE_RUNTIME_<NAME>_ARN, the agent turns the ARN into the invocation URL and signs every request with SigV4 (AWS_IAM), and locally MCP_URL points at a local server instead. Read when an agent should use a new MCP runtime, when the agent cannot reach its MCP server, or when changing how the agent connects."
---

# Agent to MCP

Code: `<pkg>/runtimes/site_agent.py`, `agentcore/cdk/lib/cdk-stack.ts`.

---

## 1. The three steps

1. **Declare** in `cdk-stack.ts`: `this.application.runtime('<Mcp>').bind(this.application.runtime('<Agent>'))`.
2. **`bind()` does two things** (`AgentCoreRuntime.bind` in `@aws/agentcore-cdk`): grants the agent's execution role `bedrock-agentcore:InvokeAgentRuntime` on the MCP runtime, and sets the agent's env var `AGENTCORE_RUNTIME_<MCP NAME IN UPPER CASE>_ARN` to its ARN.
3. **The agent reads it**: `get_mcp_connection()` returns `(url, auth)`, and `make_agent()` passes both to Strands' `MCPClient(url=..., auth_provider=...)`.

There is no service discovery: CloudFormation fills the ARN in at deploy time, and the code turns it into a URL.

---

## 2. Where to connect, in order

`get_mcp_connection()`:

| # | When | URL | Auth |
| :--- | :--- | :--- | :--- |
| 1 | `MCP_URL` is set (the `ac-local-agent` and `ac-dev-agent` tasks: `http://localhost:$LOCAL_MCP_PORT/mcp`) | `MCP_URL` | none |
| 2 | `AGENTCORE_RUNTIME_<NAME>_ARN` is set (deployed) | `get_runtime_mcp_url(arn)` | `AwsSigV4Auth(region)` |
| 3 | otherwise | `LOCAL_MCP_URL` (`http://localhost:8000/mcp`) | none |

The deployed URL:

```text
https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<URL-quoted ARN>/invocations?qualifier=DEFAULT
```

The region is the 4th field of the ARN.

---

## 3. SigV4

A runtime without an authorizer configuration uses `AWS_IAM`: every request must be signed with SigV4 for the service `bedrock-agentcore`. `AwsSigV4Auth` is an `httpx.Auth` (`requires_request_body = True`, since the body is signed): it builds a botocore `AWSRequest` from the httpx request, signs it with `SigV4Auth(credentials, "bedrock-agentcore", region)`, and copies the headers back.

It takes its credentials from `boto3.Session()` when it is created, on the first invocation, never at import time: a session's microVM is restored from a snapshot, and credentials made at import time would be stale (`02`, section 4.2).

To check the signing works, read the MCP runtime's log: a signed `POST /mcp` with 200 means the URL, the grant, and the signature are right. A 403 is the grant or the signature; a 404 is the URL.

---

## 4. One agent per process

`invoke()` does not build an agent per request. `get_agent()` builds one on the first invocation and keeps it for the life of the process, which on AgentCore is one runtime session (`02`):

- **The MCP session stays open.** Strands' `MCPClient` closes its connection as soon as no `Agent` uses it, so keeping the MCP connection means keeping the agent. Every request of the session then lands on the same, warm MCP microVM (scenario C in `02`, section 3). Locally, two invocations in a row make one `ListToolsRequest` on the MCP server.
- **The agent remembers the conversation.** A follow-up such as "which of the two is also at S-04?" works within a session. Callers continue a conversation by sending the same runtime session ID, and start a new one with a new ID.
- **One invocation at a time.** `_agent_lock` serializes them: a Strands agent cannot run two calls at once, and the requests of a session are one conversation.
- **Start over on failure.** If a call raises (such as a broken MCP connection), `reset_agent()` closes and drops the agent, and the next invocation builds a new one with a new MCP connection; the conversation so far is lost.
- **Credentials** are taken when the agent is built, on the first invocation; botocore refreshes them for the life of the process.

---

## 5. Adding a second MCP runtime to an agent

1. A `bind()` line in `cdk-stack.ts`.
2. A constant for its env var name next to `MCP_ARN_ENV_VAR`, and a `get_<x>_connection()` with the same three cases, with its own local URL variable.
3. A second `MCPClient` in the agent's tools.
4. `test_cdk_stack_ts_uses_the_runtime_names` already checks every runtime name appears in `cdk-stack.ts`.
