---
description: "OP-4 Agent Runtime, in three layers, each with its own files, tests, and commands: what the agent is in plain Python (prompt, own tools); the thin Strands agent served by BedrockAgentCoreApp in <package_name>/runtimes/, with one agent per process and its MCP connections (local URL, or the deployed ARN from bind() signed with SigV4); running it locally against a local MCP server and calling it. Read before writing or changing an agent, its prompt, its own tools, its model, or how it reaches an MCP server, or before running or calling an agent locally."
---

# Agent Runtime

Implements **OP-4**. It builds on the MCP runtime of `30-mcp-runtime.md`; packaging and deploying it are later OPs.

| | |
| :--- | :--- |
| EP | `<package_name>/runtimes/<runtime_name>.py`, or `<package_name>/runtimes/<runtime_name>/main.py` |
| FP | layer 1: `<package_name>/<domain>/<agent_name>.py` and the tool functions it lists, `tests/<domain>/**`; layer 2: the runtime module, `<package_name>/runtimes/common.py`, `<package_name>/runtimes/mcp_connection.py`, `one.new_boto_ses` in `<package_name>/one/one_02_boto_ses.py`, `tests/runtimes/**`; layer 3: `<package_name>/devtools/{agent_client,local_run}.py`, the generated `ac-local-<slug>*` tasks, `tests/devtools/**`, the fixtures of `tests/conftest.py` |
| CMD | per layer, in each section; all: `mise run cov` |

---

## 1. An agent is a prompt, tools, a model, and MCP servers

Like an MCP server (`30-mcp-runtime.md`, section 1), an agent is split so that everything but the framework is plain Python:

| Layer | What | Knows about | Tested with |
| :--- | :--- | :--- | :--- |
| 1. The agent's definition | its request and response models, the system prompt, and the agent's own tool functions | only Python and Pydantic | plain unit tests |
| 2. The agent runtime | a factory that builds the Strands agent from what it is given, the dependencies of the process, one agent per process, the HTTP app, `main()` | layer 1, Strands, `BedrockAgentCoreApp`, `one` | a real local MCP server, fake agents; no model call |
| 3. Local run | the agent on a local port, pointed at a local MCP server, and a client to call it | layer 2 | by hand (calls the model), and the client's tests against the real app with a fake agent |

The model ID is a config value (`20-centralized-config.md`), not code.

---

## 2. Layer 1: what the agent is

**Where:** a module next to the business it serves, `<package_name>/<domain>/<agent_name>.py`. It imports no agent framework.

| Name | What |
| :--- | :--- |
| `<Agent>Request` | the payload a caller sends, a Pydantic model with `Field(description=...)` on every field, such as `prompt: str = Field(min_length=1)` |
| `<Agent>Response` | what the agent answers, such as `result: str` |
| `SYSTEM_PROMPT` | what the agent is for and how it answers |
| `TOOLS` | the agent's own tools, as plain functions |

The two models are the agent's contract with its callers, as the result models are an MCP tool's: written down, validated, and changed on purpose. A new field of the request (a user ID, a site to focus on) is a field here, read in `invoke`.

**A tool function** follows the rules of an MCP tool function (`30-mcp-runtime.md`, section 2): stateless, dependencies as arguments, a docstring written for the LLM (its description), type hints on every parameter (its input schema), a Pydantic result model. It needs no dependency injected when it takes none; one that needs a client gets it from layer 2, like an MCP tool.

The tools of the agent's MCP servers come on top of `TOOLS`, at layer 2.

**Tests and CMD:** `tests/<domain>/test_<domain>_<agent_name>.py` checks what the request accepts and refuses, that every model field has a description, the prompt, and that every tool has a docstring, a type hint per parameter, and a Pydantic result; the tool functions' own modules have their own tests.

```bash
.venv/bin/python tests/<domain>/test_<domain>_<agent_name>.py
```

---

## 3. Layer 2: the agent runtime

**Where:** `<package_name>/runtimes/<runtime_name>.py`, or `<runtime_name>/main.py`, with a `main()`.

```python
def make_agent(model_id, boto_session, mcp_url, mcp_auth=None) -> Agent:
    return Agent(
        model=BedrockModel(model_id=model_id, boto_session=boto_session),
        system_prompt=SYSTEM_PROMPT,
        tools=[*[tool(func) for func in TOOLS], MCPClient(url=mcp_url, auth_provider=mcp_auth)],
        callback_handler=None,
    )


def build_agent() -> Agent:
    boto_session = one.new_boto_ses()
    mcp_url, mcp_auth = get_mcp_connection(one.config.agentcore_runtime_name_<mcp>, boto_session)
    return make_agent(one.config.<agent>_model_id, boto_session, mcp_url, mcp_auth)


agent = ProcessAgent(build_agent)
app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: dict) -> dict:
    try:
        request = <Agent>Request.model_validate(payload)
    except pydantic.ValidationError as e:
        errors = e.errors(include_url=False, include_context=False, include_input=False)
        raise HTTPException(status_code=400, detail=errors)  # starlette's
    answer = strip_thinking(agent(request.prompt))
    return <Agent>Response(result=answer).model_dump()


def main():
    print_config_source()
    app.run()
```

**`make_agent`** assembles the agent from its arguments only, so a test builds it against a local MCP server with a plain boto3 session. One `MCPClient` per MCP server the agent uses.

**`build_agent`** gives it the dependencies of this process:

- **The boto session** is `one.new_boto_ses()`: a new session with the region and credential rules of `one.bsm` (the environment's local profile; the execution role when deployed), resolved on the first invocation. Never at import time, nor reused from startup: an AgentCore microVM is restored from a snapshot, and credentials resolved before it would be stale. The model and the SigV4 signer use the same session.
- **The model ID** comes from the config.
- **The MCP connection** comes from `get_mcp_connection` (section 4).

**One agent per process**, `ProcessAgent(build_agent)` of `runtimes/common.py`:

- Built on the first invocation, kept for the life of the process. On AgentCore one process serves one runtime session, so the agent serves one conversation: it remembers earlier turns, and its MCP connections, so its MCP sessions, stay open, so the MCP microVMs stay warm. A caller continues a conversation by sending the same runtime session ID, and starts a new one with a new ID.
- Strands' `MCPClient` closes its connection when no agent uses it, so keeping the MCP session means keeping the agent.
- One call at a time (a lock): an agent cannot run two calls at once.
- A call that raises (such as on a broken MCP connection) drops the agent; the next call builds a new one, and the conversation so far is lost.

**The HTTP app:** `BedrockAgentCoreApp` serves `POST /invocations` (the `@app.entrypoint` function, with the request's JSON payload) and `GET /ping` on port 8080: the AgentCore HTTP contract. `invoke` validates the payload against the request model first: a wrong one is the caller's mistake, so it raises starlette's `HTTPException(400)`, which `BedrockAgentCoreApp` answers as `{"error": <pydantic's errors>}` with that status, before the agent is built or the model called; any other exception is a 500. It returns the response model as a dict. `strip_thinking` (in `runtimes/common.py`) removes the `<thinking>` blocks and `<response>` tags some models (such as Nova) put around the answer.

**`main()`** prints the config source (a runtime that cannot load its config fails at startup), then `app.run()`. `agentcore dev` serves `app` with uvicorn instead of calling `main()`, so there the config loads on the first request.

**Tests and CMD:** `tests/runtimes/test_runtimes_<runtime_name>.py`: the ARN variable name of each MCP runtime; `make_agent` loads the own tools and the MCP tools from the real local MCP server (fixture `mcp_url`), without a model call; `build_agent` with `MCP_URL_<MCP NAME>` set; `invoke` with a fake agent, and a bad payload (400, no agent built); `main()`. `test_runtimes_common.py` covers `ProcessAgent` (built once, reused, dropped after a failure) and `strip_thinking`.

```bash
.venv/bin/python tests/runtimes/test_runtimes_<runtime_name>.py
.venv/bin/python tests/runtimes/test_runtimes_common.py
.venv/bin/python tests/runtimes/test_runtimes_mcp_connection.py
```

---

## 4. Layer 2: reaching an MCP server

`<package_name>/runtimes/mcp_connection.py`. There is no service discovery: the deploy fills in the MCP runtime's ARN, and the code turns it into a URL.

**`bind()`** in `agentcore/cdk/lib/cdk-stack.ts`, one line per agent-to-MCP pair:

```typescript
this.application.runtime('<Mcp>').bind(this.application.runtime('<Agent>'));
```

It grants the agent's execution role `bedrock-agentcore:InvokeAgentRuntime` on the MCP runtime, and sets the agent's environment variable `AGENTCORE_RUNTIME_<MCP NAME IN UPPER CASE>_ARN` to its ARN: `get_runtime_arn_env_var(<Mcp>)`. That name is undocumented AgentCore CLI behavior; a test pins it.

**`get_mcp_connection(runtime_name, boto_session)`** returns `(url, auth)` for the MCP runtime of that name:

| # | When | URL | Auth |
| :--- | :--- | :--- | :--- |
| 1 | `MCP_URL_<NAME>` (`get_local_mcp_url_env_var`) is set: the local tasks point the agent at a local server of that MCP runtime | its value | none |
| 2 | `AGENTCORE_RUNTIME_<NAME>_ARN` is set: deployed | `get_runtime_mcp_url(arn)` | `AwsSigV4Auth` |
| 3 | otherwise | none: `ValueError`, naming both variables and the missing `bind()` line | |

Each MCP runtime has its own two variables, so an agent with several MCP servers calls it once per server, by name. There is no default URL on purpose: a missing `bind()` line fails at the first invocation with that message, not as a connection error to a server that is not there. Row 2 is `get_deployed_mcp_connection(arn, boto_session)`, which a client of a deployed MCP runtime uses too.

**The deployed URL**, the region being the 4th field of the ARN:

```text
https://bedrock-agentcore.<region>.amazonaws.com/runtimes/<URL-quoted ARN>/invocations?qualifier=DEFAULT
```

**SigV4:** a runtime with no authorizer accepts only requests signed with SigV4 for `bedrock-agentcore` (`AWS_IAM`). `AwsSigV4Auth(credentials, region)` is an `httpx.Auth` that signs each request, body included, with credentials frozen again per request (so they refresh).

---

## 5. Layer 3: run and call it locally

The same generated tasks as an MCP runtime (`30-mcp-runtime.md`, section 4), from the agent's registry entry. Start its MCP servers first, then the agent:

```bash
mise run ac-local-<mcp slug>
```

```bash
mise run ac-local-<slug>
```

It frees the agent's local port, then serves `<package_name>.runtimes.<runtime_name>:app` with uvicorn on it, with one `MCP_URL_<NAME>=http://localhost:<its port>/mcp` per MCP runtime the agent calls (its `mcp_runtimes` in the registry). Runtime `local`: the config from the files, and the model called with the environment's profile and region (`AWS_PROFILE_FOR_<ENV>` of `.env`, through `one.new_boto_ses`), so `ENV_NAME` alone picks the account. **It calls Bedrock**: the account needs access to the model.

**Call:**

```bash
mise run ac-local-<slug>-call
```

It sends the agent's sample `{"prompt": ...}` through `<package_name>/devtools/agent_client.py` to `http://localhost:<port>/invocations`. By hand, with a session ID (at least 33 characters on AgentCore), which travels in `X-Amzn-Bedrock-AgentCore-Runtime-Session-Id`, the header AgentCore sets from `runtimeSessionId`:

```bash
.venv/bin/python -c "from <package_name>.devtools.agent_client import main; main()" --url http://localhost:<port> --prompt '<question>' --session-id <id>
```

Locally there is one process, so every call is the same conversation until the server restarts. As a library: `invoke_agent(url, payload, session_id=None)`.

**Tests and CMD:** `tests/devtools/test_devtools_agent_client.py` calls the real app, served on a free port by the fixture `agent_url` of `tests/conftest.py` with a fake agent (no model call): the answer, the session ID reaching the agent, an error status. `serve(asgi_app)` of `tests/conftest.py` serves any app on a free port for a test.

```bash
.venv/bin/python tests/devtools/test_devtools_agent_client.py
```

---

## 6. Adding an agent runtime, this OP's part

1. Its model ID as a config field, and its runtime names (`20-centralized-config.md`, section 5).
2. Layer 1: `<package_name>/<domain>/<agent_name>.py` with its request and response models, `SYSTEM_PROMPT`, and `TOOLS`, the tool functions, and their tests.
3. Layer 2: `<package_name>/runtimes/<runtime_name>.py` as in section 3, with one `get_mcp_connection(<Mcp>, ...)` per MCP server, and its test. Reuse `common.py` and `mcp_connection.py`; never copy them.
4. A `bind()` line per MCP server in `cdk-stack.ts` (section 4).
5. Layer 3: an entry in the runtime registry with the next free local port, a sample prompt, and its `mcp_runtimes`; then `mise run gen-env-tasks` for its `ac-local-<slug>` tasks.
6. `mise run cov`, then run its MCP servers and the agent, and call it (a model call: say so first).

Packaging and deploying it are later OPs.
