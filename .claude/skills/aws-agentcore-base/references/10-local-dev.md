---
description: "The two ways to run the runtimes on a developer machine (ac-local-*: the package from the repo; ac-dev-*: the packaged copy under agentcore dev), the dedicated local ports 18731/18732, the free-port tool that stops only this repo's leftover servers, and the agentcore dev behaviors that matter. Read before running a runtime locally, when a local port is taken, or when a local call reaches the wrong server."
---

# Local Development

---

## 1. Two ways to run locally

| | `ac-local-*` | `ac-dev-*` |
| :--- | :--- | :--- |
| Runs | the package from the repo (`python -m <pkg>.runtimes.<x>`, uvicorn for the agent) | `app/<Runtime>/` as packaged, under `agentcore dev` |
| Runtime (`06`) | `local` | `agentcore_local` |
| Config | `config/*.json5` | SSM: run `config-deploy-<env>` first |
| Python env | the repo's `.venv` | `app/<Runtime>/.venv`, made by the CLI from the generated `pyproject.toml` |
| Checks | the business logic and wiring, fastest loop | the packaging and the config path, as close to deployed as it gets locally |

Both use the same ports, so either kind of MCP server works with either kind of agent and with the same callers. A typical session:

```bash
mise run ac-local-mcp          # terminal 1 (or ac-dev-mcp)
mise run ac-local-agent        # terminal 2 (or ac-dev-agent), needs Bedrock access with the dev profile
mise run ac-local-mcp-call     # terminal 3: list tools, get site S-03
mise run ac-local-agent-call   # terminal 3: the demo question
```

---

## 2. Ports

Defined once in `mise.toml` `[env]`:

| Variable | Port | Used by |
| :--- | :--- | :--- |
| `LOCAL_MCP_PORT` | 18731 | the MCP server, `MCP_URL` of the agent, `ac-local-mcp-call` |
| `LOCAL_AGENT_PORT` | 18732 | the agent, `ac-local-agent-call` |

Unusual on purpose, so a listener there is almost surely a leftover server of this repo; below the Linux ephemeral range (32768+), so no outgoing connection takes them by chance. Deployed runtimes always listen on AgentCore's 8000 (MCP) and 8080 (HTTP); no deploy code knows about these ports.

`agentcore invoke --local` needs `--port 18731` or `--port 18732` to reach them.

---

## 3. `free-port`

Every server task first runs `.mise/tasks/free-port.py --port <port>` (`agentcore_project/local_port.py`); it is also `mise run free-port --port <port>`.

- A listener counts as this repo's when its working directory is inside the repo root (`agentcore dev` runs its servers in `app/<Runtime>/`, which is inside).
- If any listener is not this repo's, nothing is stopped: it exits 1 and prints each pid and command line. Other clones and worktrees of the same project are not "this repo".
- Otherwise `SIGTERM`, a 5 s wait, then `SIGKILL` for what still listens.
- It uses `lsof`, which sees only the current user's processes.
- The terminal whose server was stopped prints `ERROR task failed`: expected.

---

## 4. `agentcore dev` behaviors that matter

- **Always pass `--port`.** Without it, when the default port is taken, the CLI silently moves to the next free one (8001, 8002, ...), and callers reach the old server instead. The `ac-dev-*` tasks pass `$LOCAL_MCP_PORT` / `$LOCAL_AGENT_PORT`.
- It sets `PORT`, `LOCAL_DEV=1`, `FASTMCP_PORT` (MCP), applies `envVars` from `agentcore.json`, then `agentcore/.env.local` if present (git-ignored; this repo does not need one).
- It inherits the shell's environment, so `.env` values from mise (`ENV_NAME`, `AWS_PROFILE_FOR_<ENV>`) reach the server.
- An MCP runtime runs as `python main.py`; an HTTP runtime as `uvicorn main:app --reload`, which reloads when `ac-gen` rewrites the package copy. Stopping the uvicorn process ends `agentcore dev` too; it does not respawn it.
- `--no-traces` disables the local OpenTelemetry trace collection.

---

## 5. What local runs cannot show

Cold starts, the SigV4 path between runtimes, the execution role's permissions, and the CodeZip dependency install (`04`, section 3; check it with `ac-check-wheels.py`). Those need a deploy (`11`).
