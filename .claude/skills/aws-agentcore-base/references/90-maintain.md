---
description: "OP-9 Maintain: keeping the project and its toolchain current over their life: upgrading the AgentCore CLI and its CDK library with the layout check, the undocumented CLI behaviors the code relies on and where, the runtimes' dependency group, adding, renaming, or removing a runtime or an environment through the registry and the generated tasks, and keeping these references in step with the code. Read before upgrading the AgentCore CLI, when the CLI behaves differently than these references say, before adding or removing a runtime or an environment, or after a change that breaks a reference."
---

# Maintain

Implements **OP-9**.

| | |
| :--- | :--- |
| EP | `.claude/skills/aws-agentcore-base/scripts/check_cdk_layout.py`; `<package_name>/agentcore_project/registry.py` |
| FP | `mise.toml` `[tools]`, `agentcore/cdk/package.json` and `package-lock.json`, the constants and functions of section 2, `[dependency-groups] agentcore` of `pyproject.toml`, the registry, the `aws-agentcore-*` skills |
| CMD | `mise run ac-check-layout`, `mise run gen-env-tasks`, then the checks of section 1 |

---

## 1. Upgrading the AgentCore CLI

| What | Pinned in |
| :--- | :--- |
| the CLI, `@aws/agentcore` | `mise.toml` `[tools]` `"npm:@aws/agentcore"` |
| its CDK library, `@aws/agentcore-cdk` | `agentcore/cdk/package.json` and `package-lock.json` |

The CLI checks before a deploy that the library matches its own major version, so upgrade both together: the version a fresh `agentcore create` writes into `package.json` is the one that goes with the CLI.

1. Bump `"npm:@aws/agentcore"` in `mise.toml`; `mise install`.
2. `mise run ac-check-layout` (section 1.1). Apply each difference of the template to `agentcore/cdk/`, keeping the `bind()` lines; or run `agentcore migrate`, which rewrites the directory with a backup, and put the `bind()` lines back.
3. `npm install` in `agentcore/cdk`, so `package-lock.json` matches.
4. Check every behavior of section 2 against the new CLI.
5. `mise run ac-check-layout` again (no difference), `mise run cov`, `mise run ac-build`, an `ac-dev-<slug>` run with its `-call`.
6. Deploy dev with the user's yes (`60-deploy.md`), then `mise run ac-test-dev` and `mise run int-test`.

### 1.1 The layout check

```bash
mise run ac-check-layout
```

It runs `scripts/check_cdk_layout.py` of this skill (stdlib only, no AWS call, no `npm install`): `agentcore create --name LayoutCheck --skip-install --skip-git` in a temporary directory (the CLI refuses to create a project inside another one), then compares every file of the fresh `agentcore/cdk/` with the project's.

| Result | Meaning |
| :--- | :--- |
| same content | OK |
| `lib/cdk-stack.ts` has extra lines | OK, as long as every code line of the template is still there, in order: the project adds `bind()` and drops the template's example comment |
| `MISSING` / `EXTRA` | the template has a file the project does not / the other way round |
| `CHANGED` | the content differs; the unified diff follows |

`package-lock.json`, `node_modules/`, `cdk.out/`, and `dist/` are ignored. `--keep` keeps the fresh project for a closer look. Exit code 1 means drift.

---

## 2. Undocumented CLI behaviors the code relies on

Each was read from the CLI's bundled source (`main.js`) or `@aws/agentcore-cdk`, or found by trying, not from the docs (AgentCore CLI 1.0.1). A new version may change any of them: search the new source for the name in the last column, fix the code that relies on it, and the reference that describes it, in the same change.

| Behavior | Relied on by | Where to look |
| :--- | :--- | :--- |
| `agentcore dev` sets `LOCAL_DEV=1` on the server | `AGENTCORE_DEV_VAR` in `constants.py`; the `agentcore_local` runtime (`10-code-runtime.md`) | `commandForRuntime` |
| `agentcore dev` applies `envVars` of `agentcore.json`, then `agentcore/.env.local`, and passes on the shell's environment | the signals and the config location under `agentcore dev` (`53-agentcore-dev.md`) | `createDevEnvironmentLoader` |
| `agentcore dev` without `--port` silently moves to the next free port | the explicit `--port` of `get_dev_command` in `devtools/local_run.py` | `MAX_PORT_ATTEMPTS` |
| An `HTTP` runtime runs under `agentcore dev` as `uvicorn main:app --reload` | the `app` import of the generated `main.py` (`52-agentcore-packaging.md`) | `commandForRuntime` |
| CodeZip dependencies: `uv pip install --only-binary :all:` for `aarch64-manylinux2014`, `_2_28`, `_2_34` | `CODEZIP_PLATFORMS`, `check_codezip_install` in `codezip.py` | `PLATFORM_CANDIDATES` in `lib/packaging/python.js` |
| The CLI installs `[project].dependencies` of the runtime's `pyproject.toml` and ignores `uv.lock` | the pinned export in `codezip.py` | `lib/packaging/python.js` |
| `bind()` sets `AGENTCORE_RUNTIME_<NAME>_ARN` and grants `InvokeAgentRuntime` | `get_runtime_arn_env_var` in `runtimes/mcp_connection.py` (`40-agent-runtime.md`) | `bind(` in `AgentCoreRuntime.js` |
| `deploy --yes` of a project that declares nothing destroys the target's stack and removes its state | `ac-down-<env>` (`70-teardown.md`) | `teardown(` |
| `.gitignore` of a fresh project commits `agentcore/.cli/deployed-state.json` | keeping it in git (`60-deploy.md`) | the root `.gitignore` the CLI writes |
| `agentcore invoke` of an MCP runtime sends `--payload` as the raw JSON-RPC body | the MCP `sample_payload` and `get_invoke_script` (`60-deploy.md`) | `invoke` |

---

## 3. The runtimes' dependencies

`[dependency-groups] agentcore` of `pyproject.toml` is what every runtime installs (`52-agentcore-packaging.md`): keep it to what the runtimes import (zip size is start time), and every version must have a Linux aarch64 wheel. After any change: `uv lock`, `mise run ac-check-wheels`, `mise run ac-build`. How to choose and upgrade versions in general is the `pywf-oss-upgrade-deps` skill.

---

## 4. Runtimes and environments over time

The registry (`51-agentcore-config.md`) is the one place a runtime is declared, and the tasks of every runtime and environment are generated from it by `mise run gen-env-tasks`; no per-runtime task is written by hand.

| Change | Do |
| :--- | :--- |
| **Add a runtime** | the invoker skill (`aws-agentcore-new-mcp` or `aws-agentcore-new-agent`): names in the config, its code, a registry entry with a unique `local_port`, a sample payload, and for an agent its `mcp_runtimes` and their `bind()` lines; then `gen-env-tasks` |
| **Rename a runtime** | its names in the config, its module if renamed, the registry entry, the `bind()` lines, the server name of an MCP runtime; `gen-env-tasks`, `ac-gen`. The next deploy replaces the runtime (a new ID, a new log group; existing sessions end): check with `ac-status-<env>` |
| **Remove a runtime** | its registry entry, its `bind()` lines and its references in other agents' `mcp_runtimes`, its names in the config, its code and tests; `gen-env-tasks`; deploy each environment (the CLI destroys it) |
| **Add an environment** | a member of `EnvNameEnum` (`pywf-aws-cdk-base`), its `config/config-<env>.json5` and secret file, `AWS_PROFILE_FOR_<ENV>` in `.env`; `gen-env-tasks`; then `ac-chain-up-<env>` with the user's yes |
| **Remove an environment** | `ac-chain-down-<env>` first (the user's yes), then the reverse of adding it |

After any of these and a deploy, `mise run gen-quick-links` refreshes `QUICK_LINKS.md` (`80-invoke-and-observe.md`, section 4.1). The tests catch most misses: names and physical-name length in every environment (`20-centralized-config.md`), unique local ports and every `mcp_runtimes` entry bound in `cdk-stack.ts` (`test_agentcore_project_registry.py`), every runtime module's entry points, and `mise.toml` being up to date.

---

## 5. Keeping these references in step

- `99-ood.md` is the design: every OP with its EP, FP, and CMD. A change that breaks it changes it in the same change, a little.
- One reference per OP, numbered `<OP><part>`; each opens with "Implements OP-N", its EP, FP, and CMD, and cites only lower numbers. Write a fact where its OP is, and nowhere else.
- A fact that turns out wrong is fixed in its reference in the same change as the code; an undocumented behavior goes into section 2.
- The invokers (`aws-agentcore-<job>`, listed in the base `SKILL.md`) list the references they read; keep those lists, the base `SKILL.md`, and the invoker table of `99-ood.md` in step.
- After changing a reference's description, regenerate the index of `SKILL.md`:

```bash
python3 .claude/skills/pywf-oss-base/scripts/update_skill_index.py --skill_dir .claude/skills/aws-agentcore-base
```
