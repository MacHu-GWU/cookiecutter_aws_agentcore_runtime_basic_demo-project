---
description: "OP-5 AgentCore Runtime, layer 4: running the packaged runtimes on a developer machine with the AgentCore CLI (agentcore dev, the ac-dev-* tasks), how that differs from the ac-local-* tasks, what it needs (the config deployed to SSM), the CLI behaviors that matter (always --port, LOCAL_DEV, envVars, uvicorn reload), and what only a deploy can show. Read before running a runtime with agentcore dev, or when an agentcore dev server starts on the wrong port or cannot load its config."
---

# Running the Package with `agentcore dev`

Implements **OP-5**, layer 4.

| | |
| :--- | :--- |
| EP | `get_dev_command` of `<package_name>/devtools/local_run.py`, run by the generated `ac-dev-<slug>` |
| FP | `<package_name>/devtools/local_run.py`, the `local_port` and `mcp_runtimes` of the registry, `app/<Runtime>/.venv` (made by the CLI) |
| CMD | `mise run ac-dev-<slug>`; call it with `mise run ac-local-<slug>-call` |

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
mise run ac-dev-<slug>
```

It runs `ac-gen` first (through `depends`), frees the runtime's local port, then `AWS_REGION=<region of the config> agentcore dev --agent <Runtime> --no-traces --port <port>` (`.mise/tasks/ac-run.py --mode dev`). Start an agent's MCP runtimes first, with `ac-dev-<slug>` or `ac-local-<slug>`.

---

## 2. What the server gets

- **The runtime signals and the config location**: `agentcore dev` applies `envVars` of `agentcore.json` (`51-agentcore-config.md`), then `agentcore/.env.local` if present (git-ignored; not needed here), and sets `LOCAL_DEV=1`, `PORT`, and for an MCP runtime `FASTMCP_PORT`. So the code sees `agentcore_local`.
- **The shell's environment**: `agentcore dev` passes it on, so the values mise loads from `.env` (`ENV_NAME`, `AWS_PROFILE_FOR_<ENV>`) reach the server, and `one.bsm` / `one.new_boto_ses()` use the environment's local profile.
- **The region**: on `agentcore_local` the session takes it from `AWS_REGION`, because the config is read through that session; the task sets it to the config's region of `ENV_NAME`.
- **The agent's MCP servers**: one `MCP_URL_<NAME>` per MCP runtime it calls, pointing at that runtime's local port, as for `ac-local-<slug>` (`40-agent-runtime.md`, section 5).

---

## 3. CLI behaviors that matter

| Behavior | Consequence |
| :--- | :--- |
| Without `--port`, when the default port is taken, the CLI silently moves to the next free one (8001, 8002, ...) | callers reach the old server: `local_run` always passes `--port` |
| It sets `LOCAL_DEV=1` on the server | how the code tells `agentcore_local` from `agentcore` (`10-code-runtime.md`) |
| An MCP runtime runs as `python main.py`; an `HTTP` runtime as `uvicorn main:app --reload` | the shim exposes `app` (`52-agentcore-packaging.md`); `main()` is not called, so an agent loads its config on the first request; the server reloads when `ac-gen` rewrites the copy |
| Stopping the uvicorn process ends `agentcore dev` too | it does not respawn it |
| `--no-traces` | no local OpenTelemetry collection |
| `agentcore invoke --local` | needs `--port <local port>` to reach these servers; the `-call` tasks are simpler |

Each was read from the CLI's source (1.0.1), not the docs: check them again after a CLI upgrade.

---

## 4. What a local run cannot show

Cold starts, SigV4 between runtimes, the execution role's permissions, the CodeZip install on Linux aarch64 (`mise run ac-check-wheels` checks that one), and `bind()`. Those need a deploy.
