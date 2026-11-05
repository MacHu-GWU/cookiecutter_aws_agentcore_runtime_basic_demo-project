---
description: "OP-5 AgentCore Runtime, layer 4: running the packaged runtimes on a developer machine with the AgentCore CLI (agentcore dev, the ac-dev-* tasks), how that differs from the ac-local-* tasks, what it needs (the config deployed to SSM), the CLI behaviors that matter (always --port, LOCAL_DEV, envVars, uvicorn reload), and what only a deploy can show. Read before running a runtime with agentcore dev, or when an agentcore dev server starts on the wrong port or cannot load its config."
---

# Running the Package with `agentcore dev`

Implements **OP-5**, layer 4.

| | |
| :--- | :--- |
| EP | the `ac-dev-*` tasks of `mise.toml` |
| FP | the `ac-dev-*` tasks and their comment in `mise.toml`, `app/<Runtime>/.venv` (made by the CLI) |
| CMD | `mise run ac-dev-mcp`, `mise run ac-dev-agent`; call them with the `-call` tasks of `30-mcp-runtime.md` and `40-agent-runtime.md` |

---

## 1. Two ways to run locally

| | `ac-local-*` (`30-mcp-runtime.md`, `40-agent-runtime.md`) | `ac-dev-*` (this file) |
| :--- | :--- | :--- |
| Runs | the package from the repo | the packaged copy in `app/<Runtime>/`, under `agentcore dev` |
| Runtime (`10-code-runtime.md`) | `local` | `agentcore_local` |
| Config | `config/*.json5` | the SSM parameter: `config-deploy-<env>` must have run (it changes AWS: the user's yes) |
| Python env | the repo's `.venv` | `app/<Runtime>/.venv`, made by the CLI from the generated `pyproject.toml` |
| Checks | the business logic and the wiring: the fastest loop | the packaging, the shim, the import rule, the config from SSM: as close to deployed as it gets on a laptop |

Both use the same local ports, so a packaged MCP server works with a repo agent and the other way round, and the same `-call` tasks reach either.

```bash
mise run ac-dev-mcp
```

```bash
mise run ac-dev-agent
```

Each frees its port, runs `ac-gen` first (through `depends`), then `agentcore dev --agent <Runtime> --no-traces --port $LOCAL_<NAME>_PORT`.

---

## 2. What the server gets

- **The runtime signals and the config location**: `agentcore dev` applies `envVars` of `agentcore.json` (`51-agentcore-config.md`), then `agentcore/.env.local` if present (git-ignored; not needed here), and sets `LOCAL_DEV=1`, `PORT`, and for an MCP runtime `FASTMCP_PORT`. So the code sees `agentcore_local`.
- **The shell's environment**: `agentcore dev` passes it on, so the values mise loads from `.env` (`ENV_NAME`, `AWS_PROFILE_FOR_<ENV>`) reach the server, and `one.bsm` / `one.new_boto_ses()` use the environment's local profile.
- **The region**: on `agentcore_local` the session takes it from `AWS_REGION`, because the config is read through that session; the `ac-dev-*` tasks set it.
- **The agent's MCP server**: `MCP_URL` pointing at the local MCP port, as for `ac-local-agent`.

---

## 3. CLI behaviors that matter

| Behavior | Consequence |
| :--- | :--- |
| Without `--port`, when the default port is taken, the CLI silently moves to the next free one (8001, 8002, ...) | callers reach the old server: the tasks always pass `--port` |
| It sets `LOCAL_DEV=1` on the server | how the code tells `agentcore_local` from `agentcore` (`10-code-runtime.md`) |
| An MCP runtime runs as `python main.py`; an `HTTP` runtime as `uvicorn main:app --reload` | the shim exposes `app` (`52-agentcore-packaging.md`); `main()` is not called, so an agent loads its config on the first request; the server reloads when `ac-gen` rewrites the copy |
| Stopping the uvicorn process ends `agentcore dev` too | it does not respawn it |
| `--no-traces` | no local OpenTelemetry collection |
| `agentcore invoke --local` | needs `--port $LOCAL_<NAME>_PORT` to reach these servers; the `-call` tasks are simpler |

Each was read from the CLI's source (1.0.1), not the docs: check them again after a CLI upgrade.

---

## 4. What a local run cannot show

Cold starts, SigV4 between runtimes, the execution role's permissions, the CodeZip install on Linux aarch64 (`mise run ac-check-wheels` checks that one), and `bind()`. Those need a deploy.
