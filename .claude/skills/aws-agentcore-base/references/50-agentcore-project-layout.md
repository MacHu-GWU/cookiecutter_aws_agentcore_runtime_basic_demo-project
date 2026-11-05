---
description: "OP-5 AgentCore Runtime, layer 1: the AgentCore CLI project of the repo, what each file under agentcore/ and app/ is, which are source and which are generated, why agentcore/cdk/ is committed, what cdk-stack.ts may hold, and the split between the AgentCore project and the CDK stack of everything else. Read when looking for an AgentCore file, deciding whether a file under agentcore/ or app/ may be edited or committed, or before editing agentcore/cdk/."
---

# AgentCore Project Layout

Implements **OP-5**, layer 1. OP-5 is the bridge from the runtime modules (`30-mcp-runtime.md`, `40-agent-runtime.md`) to AgentCore: one AgentCore CLI project for all runtimes, in four layers, one reference each, `50` to `53`: its files (this one), its config generated from ours (layer 2), the package build (layer 3), and the CLI's local run (layer 4).

| | |
| :--- | :--- |
| EP | `agentcore/` |
| FP | `agentcore/cdk/**` (committed), `agentcore/.cli/deployed-state.json`, the AgentCore paths of `<package_name>/paths.py`, `.gitignore`, the `cdk-stack.ts` checks in `tests/agentcore_project/test_agentcore_project_project_files.py` |
| CMD | `mise run ac-gen` (writes the generated files), `mise run ac-build` |

---

## 1. One CLI project, all runtimes

The repo is one AgentCore CLI project, named by `agentcore_project_name` of the config. Every runtime of the project is in it and is deployed together, by `agentcore deploy --target <env>`; there is no per-runtime deploy. A target is an environment.

---

## 2. Source and generated

The config, the package, and `uv.lock` are the sources. Everything the CLI reads besides its CDK app is generated from them, for one environment at a time:

```text
config/*.json5 + <package_name>/ + uv.lock
        │  mise run ac-gen  (ENV_NAME=<env>)
        ▼
agentcore/agentcore.json      the runtimes, their envVars and policies
agentcore/aws-targets.json    the one target, <env>
app/<Runtime>/                main.py, pyproject.toml, the code copy
        │  agentcore deploy --target <env>   (runs agentcore/cdk/)
        ▼
stack AgentCore-<project>-<env>
```

| Path | What | Source or generated | In git |
| :--- | :--- | :--- | :--- |
| `agentcore/agentcore.json` | the CLI project: its runtimes, their `envVars`, `additionalPolicies` | generated (layer 2) | no |
| `agentcore/aws-targets.json` | the deployment target of one environment | generated (layer 2) | no |
| `app/<Runtime>/` | each runtime's code directory, zipped by the CLI | generated (layer 3) | no |
| `agentcore/cdk/` | the CLI's CDK app (TypeScript): `bin/cdk.ts`, `lib/cdk-stack.ts`, `package.json`, `package-lock.json`, `cdk.json`, `tsconfig.json` | source, written once by `agentcore create` | yes, without `node_modules/`, `cdk.out/`, `dist/` |
| `agentcore/.cli/deployed-state.json` | the CLI's record of each deployed target's stack | written by the CLI on deploy and teardown | yes |
| `agentcore/.cli/*` (others), `agentcore/.env*.local`, `agentcore/.cache/` | CLI scratch | written by the CLI | no |

**Never edit a generated file**: change its source and run `ac-gen`. Every task that needs the generated files runs `ac-gen` first, for its own environment, so they are always those of the environment last generated.

---

## 3. Why `agentcore/cdk/` is committed

It looks generated but is not:

- The CLI writes it once, at `agentcore create`; `build` and `deploy` never rewrite it, and fail when it is missing.
- `package-lock.json` pins `@aws/agentcore-cdk`, whose major version the CLI checks against its own before a deploy.
- It holds the one piece of AgentCore wiring that cannot live in `agentcore.json`: `bind()` between runtimes.
- The CLI's upgrade path, `agentcore migrate`, rewrites it in place with a backup, which assumes the user owns it.

Keep it as close to the CLI's template as possible; the toolchain OP compares it with a fresh `agentcore create` after every CLI upgrade (`mise run ac-check-layout`). On a fresh clone, run `npm install` in `agentcore/cdk` once.

---

## 4. `cdk-stack.ts`: only AgentCore wiring

`bin/cdk.ts` reads `agentcore.json` and `aws-targets.json` and makes one `AgentCoreStack` per target. `lib/cdk-stack.ts` holds the template's `AgentCoreApplication`, plus one line per agent-to-MCP pair:

```typescript
if (this.application.runtimes.size > 0) {
  this.application.runtime('<Mcp>').bind(this.application.runtime('<Agent>'));
}
```

- `bind()` grants the agent's execution role the call to the MCP runtime and gives the agent the MCP runtime's ARN (`40-agent-runtime.md`, section 4). It must stay here: it needs the MCP runtime's ARN, which exists only inside this stack.
- The `if` lets an empty project, which declares no runtime, still synthesize: that is how the runtimes are torn down.
- The runtime names are the config's (`agentcore_runtime_name_<x>`). Tests check that every registered runtime's name appears in `cdk-stack.ts`, and that the `if` is there.

Nothing else goes in this file.

---

## 5. AgentCore and everything else

| What | Where | Deployed by |
| :--- | :--- | :--- |
| AgentCore resources: runtimes, their execution roles, endpoints, `bind()` | `agentcore.json` (generated) + `cdk-stack.ts` | the AgentCore CLI (`ac-deploy-<env>`) |
| Everything else the runtimes use: IAM policies, databases, buckets, secrets, VPCs | the Python CDK stack `agentcore_deps` | `cdk-up-<env>-agentcore-deps-stack` |

The AgentCore project only **refers** to the rest, by names from the config, through fields of `agentcore.json` (layer 2). No CloudFormation export or import is needed: every name and ARN is a config property. So the `agentcore_deps` stack is deployed first.
