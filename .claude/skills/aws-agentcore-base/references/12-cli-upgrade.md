---
description: "Upgrading the AgentCore CLI (@aws/agentcore) and its CDK library (@aws/agentcore-cdk): where both versions are pinned, the layout check against a fresh agentcore create (scripts/check_cdk_layout.py, mise run ac-check-layout), and the undocumented CLI behaviors this repo depends on, to check again after every upgrade. Read before upgrading the AgentCore CLI, or when the CLI behaves differently than the other references say."
---

# Upgrading the AgentCore CLI

---

## 1. Where the versions are pinned

| What | Where | Now |
| :--- | :--- | :--- |
| The CLI, `@aws/agentcore` | `mise.toml` `[tools]` `"npm:@aws/agentcore"` | `1.0.1` |
| Its CDK library, `@aws/agentcore-cdk` | `agentcore/cdk/package.json` and `package-lock.json` | `1.0.0` |

The CLI checks before a deploy that the library matches its own major version. Upgrade both together: the version a fresh `agentcore create` writes into `package.json` is the one that goes with the CLI.

---

## 2. The layout check

`agentcore/cdk/` was written once by `agentcore create` and is committed (`03`). A new CLI may write a different template. The check compares the two:

```bash
mise run ac-check-layout
```

It runs `.claude/skills/aws-agentcore-base/scripts/check_cdk_layout.py`: `agentcore create --name LayoutCheck --skip-install --skip-git` in a temporary directory (the CLI refuses to create a project inside another one), then compares every file of the fresh `agentcore/cdk/` with the project's. No AWS call, no `npm install`.

| Result | Meaning |
| :--- | :--- |
| same content | OK |
| `lib/cdk-stack.ts` has extra lines | OK, as long as every code line of the template is still there, in order: the project adds `bind()` and drops the template's example comment (`07`) |
| `MISSING` | the template has a file the project does not |
| `EXTRA` | the project has a file the template does not |
| `CHANGED` | the content differs; the unified diff follows |

`package-lock.json`, `node_modules/`, `cdk.out/`, and `dist/` are ignored. The project name does not matter: it appears only in `agentcore.json`. Add `--keep` to keep the fresh project for a closer look. Exit code 1 means drift.

---

## 3. Upgrade steps

1. Bump `"npm:@aws/agentcore"` in `mise.toml`, then `mise install`.
2. `mise run ac-check-layout`. For each difference, apply the template's change to `agentcore/cdk/`, keeping the `bind()` lines; or run `agentcore migrate`, which rewrites the directory with a backup, and put the `bind()` lines back.
3. In `agentcore/cdk`: `npm install` so `package-lock.json` matches the new `package.json`.
4. Check the behaviors of section 4 against the new CLI.
5. `mise run ac-check-layout` again (no difference), `mise run cov`, `mise run ac-build`, a local `ac-dev-*` run.
6. Deploy dev with the user's yes (`11`), and invoke it.

---

## 4. Undocumented behaviors this repo depends on

Each was read from the CLI's bundled source (`main.js`) or `@aws/agentcore-cdk`, not from the docs. A new version may change any of them; search the new source for the name in the last column.

| Behavior | Relied on by | Where to look |
| :--- | :--- | :--- |
| `agentcore dev` sets `LOCAL_DEV=1` on the server | `AGENTCORE_DEV_VAR` in `constants.py`, the `agentcore_local` runtime (`06`) | `commandForRuntime` |
| `agentcore dev` applies `envVars` of `agentcore.json`, then `agentcore/.env.local` | config from SSM under `agentcore dev` (`06`) | `createDevEnvironmentLoader` |
| `agentcore dev` without `--port` silently moves to the next free port | the explicit `--port` of the `ac-dev-*` tasks (`10`) | `MAX_PORT_ATTEMPTS` |
| CodeZip dependencies: `uv pip install --only-binary :all:` for `aarch64-manylinux2014`, `_2_28`, `_2_34` | `CODEZIP_PLATFORMS` and `check_codezip_install` in `runtime_dir.py` (`04`) | `PLATFORM_CANDIDATES` in `lib/packaging/python.js` |
| The CLI installs `[project].dependencies` of the runtime's `pyproject.toml` and ignores `uv.lock` | the pinned export in `runtime_dir.py` (`04`) | `lib/packaging/python.js` |
| `bind()` sets `AGENTCORE_RUNTIME_<NAME>_ARN` and grants `InvokeAgentRuntime` | `MCP_ARN_ENV_VAR` in `site_agent.py` (`08`) | `bind(` in `AgentCoreRuntime.js` |
| An HTTP runtime runs under `agentcore dev` as `uvicorn main:app --reload` | the `app` export of the generated `main.py` (`04`) | `commandForRuntime` |
| `.gitignore` of a fresh project commits `agentcore/.cli/deployed-state.json` | keeping it in git (`11`, section 5) | the root `.gitignore` the CLI writes |

If one changed, fix the code that relies on it and the reference that describes it, in the same change.
