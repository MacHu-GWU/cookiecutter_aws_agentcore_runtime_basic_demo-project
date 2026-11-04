---
description: "Where every AgentCore concern lives in this repo, what is source and what is generated, and the chain from the config to a deployed runtime. Read when looking for where something AgentCore related lives, deciding where a new file goes, or wondering whether a file under agentcore/ or app/ may be edited or committed."
---

# Project Layout

---

## 1. Source and generated

The source of truth is the config, the package, and `uv.lock`. Everything the AgentCore CLI reads is generated from them by `mise run ac-gen`, for one environment (`ENV_NAME`, default `dev`).

```text
config/*.json5 + <pkg>/ + uv.lock
        │  mise run ac-gen  (ENV_NAME=<env>)
        ▼
agentcore/agentcore.json      runtimes, envVars, additionalPolicies    generated, git-ignored
agentcore/aws-targets.json    the one target <env>                     generated, git-ignored
app/<Runtime>/                main.py, pyproject.toml, package copy    generated, git-ignored
        │  agentcore deploy --target <env>   (agentcore/cdk/, TypeScript)
        ▼
stack AgentCore-<Project>-<env>
```

Never edit a generated file; change its source and run `ac-gen`. Every `ac-*` task that needs these files runs `ac-gen` first.

---

## 2. The directories

| Path | What | In git |
| :--- | :--- | :--- |
| `<pkg>/power_plant/` | business logic: seed data, ORM, schemas, queries, weather (`09`) | yes |
| `<pkg>/runtimes/` | one thin module per runtime: the FastMCP server or the agent app, with `main()` (`08`, `09`) | yes |
| `<pkg>/agentcore_project/` | dev-machine tooling: `project_files.py` (`agentcore.json`, `aws-targets.json`), `runtime_dir.py` (`app/`), `gen.py`, `local_port.py` | yes |
| `<pkg>/config/`, `<pkg>/one/`, `env.py`, `runtime.py`, `constants.py` | config, singletons, runtime detection (`06`); also copied into every runtime | yes |
| `<pkg>/cdk/stacks/agentcore_deps_stack.py` | what the runtimes use but is not AgentCore (`07`) | yes |
| `agentcore/cdk/` | the CLI's CDK app (TypeScript): `bin/cdk.ts`, `lib/cdk-stack.ts`, `package.json`, `package-lock.json` | yes, without `node_modules/`, `cdk.out/`, `dist/` |
| `agentcore/.cli/deployed-state.json` | the CLI's record of deployed targets | yes, for now |
| `agentcore/.cli/*` (other), `agentcore/.env*.local`, `agentcore/.cache/` | CLI scratch | no |
| `agentcore/agentcore.json`, `agentcore/aws-targets.json`, `app/` | generated (section 1) | no |

---

## 3. Why `agentcore/cdk/` is committed

It looks generated but is not:

- The CLI writes it once, at `agentcore create`. `deploy` and `build` never rewrite it, and fail if it is missing.
- `package-lock.json` pins `@aws/agentcore-cdk`, whose version the CLI checks against its own before a deploy.
- It holds the one piece of AgentCore wiring that cannot live in `agentcore.json`: `bind()` between runtimes (`08`).
- The CLI's upgrade path, `agentcore migrate`, rewrites it in place with a backup, which assumes the user owns it.

Keep it as close to the CLI's template as possible; anything that is not AgentCore wiring goes to the `agentcore_deps` stack (`07`).

---

## 4. One project, all runtimes

One repo is one AgentCore CLI project, `agentcore_project_name` of the config. Every runtime of the project is deployed together by `agentcore deploy --target <env>`; there is no per-runtime deploy. The list of runtimes is `get_runtime_specs()` in `agentcore_project/project_files.py`, the one place to add a runtime.
