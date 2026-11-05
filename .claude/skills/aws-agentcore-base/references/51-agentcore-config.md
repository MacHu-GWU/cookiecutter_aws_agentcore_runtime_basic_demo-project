---
description: "OP-5 AgentCore Runtime, layer 2: how the AgentCore CLI's own configuration is generated from the project config by mise run ac-gen: the runtime registry (the one place a runtime is declared, with its protocol), agentcore.json with each runtime's envVars and additionalPolicies, aws-targets.json, the empty project for teardown, and how to add a field or a runtime. Read before adding or registering a runtime, adding a field to agentcore.json, or when the generated AgentCore files look wrong."
---

# AgentCore Config, Generated

Implements **OP-5**, layer 2. The project config is the source of truth (`20-centralized-config.md`); this layer turns it into what the AgentCore CLI reads.

| | |
| :--- | :--- |
| EP | `<package_name>/agentcore_project/gen.py` (via `.mise/tasks/ac-gen.py`) |
| FP | `<package_name>/agentcore_project/registry.py`, `<package_name>/agentcore_project/project_files.py`, `<package_name>/agentcore_project/gen.py`, `tests/agentcore_project/test_agentcore_project_{registry,project_files,gen}.py` |
| CMD | `mise run ac-gen` (for `ENV_NAME`, default `dev`); `ENV_NAME=<env> mise run ac-gen`; tests below |

---

## 1. The runtime registry

`get_runtime_specs(config)` in `agentcore_project/registry.py` is **the one list of runtimes**. Everything per runtime is generated from it.

| Field of `RuntimeSpec` | What |
| :--- | :--- |
| `name` | the runtime's name in `agentcore.json`, from `agentcore_runtime_name_<x>` of the config |
| `module` | the runtime module relative to the package, such as `runtimes.<runtime_name>` (or `runtimes.<runtime_name>.main`) |
| `protocol` | `RuntimeProtocolEnum.MCP` (an MCP server: port 8000, `/mcp`) or `RuntimeProtocolEnum.HTTP` (an agent: port 8080, `/invocations`, `/ping`) |
| `sample_payload` | what the generated call tasks send, `ac-local-<slug>-call` locally and `ac-invoke-<env>-<slug>` deployed: `{"prompt": ...}` for an agent, a whole JSON-RPC `tools/call` request for an MCP server |
| `local_port` | its port on a developer machine, unique (18731, 18732, ...): `ac-local-<slug>` and `ac-dev-<slug>` listen there |
| `mcp_runtimes` | for an agent: the MCP runtimes it calls; each needs its `bind()` line in `cdk-stack.ts`, and the local tasks point the agent at their local ports |
| `slug` (derived) | the name in task names, kebab case: `MyMcp` → `my-mcp` |

`RUNTIME_PYTHON` (`3.12`, the dev Python of `mise.toml`) and `RUNTIME_VERSION` (`PYTHON_3_12`, its name in `agentcore.json`) apply to every runtime.

**Choosing a runtime name:** PascalCase, a noun for what it is ending in `Mcp` or `Agent`, so its role shows in the console; short, because AWS knows it as `<project>_<target>_<Runtime>`, at most 48 characters, and `<project>_prd_` already takes part of that. A test checks the physical name fits in every environment (`20-centralized-config.md`).

---

## 2. `agentcore.json`

`build_agentcore_json(config)` writes, per runtime of the registry:

| Field | Value |
| :--- | :--- |
| `name` | `spec.name` |
| `build`, `entrypoint`, `codeLocation` | `CodeZip`, `main.py`, `app/<Runtime>` (layer 3) |
| `runtimeVersion` | `RUNTIME_VERSION` |
| `protocol` | `spec.protocol` |
| `envVars` | `get_runtime_env_vars(config)`, the same for every runtime (section 3) |
| `additionalPolicies` | `[config.iam_policy_arn_agentcore_runtime]`: the managed policy of the `agentcore_deps` stack, attached to the CLI-created execution role |

and the project header, `name` (`agentcore_project_name`), `version` 2, `managedBy` `CDK`: the shape of the CLI's schema (`@aws/agentcore-cdk`, `AgentEnvSpecSchema`).

**Other fields that refer outward**, not used yet: `networkMode` / `networkConfig` (a VPC, for a database in one). `executionRoleArn` is not used on purpose: the CLI-created role already carries logs, X-Ray, Bedrock model access, and workload identity, and `bind()` adds its grant to it; a role passed in is imported read-only, so CDK would drop the `bind()` grant with only a synth warning. Permissions are added to the policy instead.

To add a field: in `build_agentcore_json`, its value from a config property, and an assertion in `test_build_agentcore_json`. If two runtimes need different policies, give each its own `additionalPolicies`.

---

## 3. The env vars every runtime gets

`get_runtime_env_vars(config)`, written into `envVars` of every runtime, for the environment `ac-gen` runs for:

| Variable | Value | For |
| :--- | :--- | :--- |
| `IS_AGENTCORE_RUNTIME` | `true` | the runtime signal (`10-code-runtime.md`) |
| `ENV_NAME` | the environment, such as `dev` | `one.env` |
| `CONFIG_SSM_PARAM_NAME` | `config.ssm_param_name_config` | where the config is (`20-centralized-config.md`) |

Both a deployed runtime and `agentcore dev` apply `envVars`, so both see these three. That is why `agentcore.json` is per environment, git-ignored, and regenerated. Values, secrets above all, never go here: they are in the config parameter.

---

## 4. `aws-targets.json` and the empty project

- `build_aws_targets_json(config)`: one target, named after the environment (`agentcore_target_name`), with the config's account and region. Only that environment's target is ever in the file, so a command cannot reach another environment by mistake.
- `build_empty_agentcore_json(config)`: the project header without `runtimes`, the shape `agentcore create` writes for an empty project. `agentcore deploy --yes` of it destroys the target's stack: the teardown of the runtimes.
- `write_json(path, data)` writes indented JSON only when the content changed.

---

## 5. `ac-gen`

`gen.py`:

- `generate_all(config)`: `agentcore.json`, `aws-targets.json`, then `app/<Runtime>/` of every registered runtime (layer 3).
- `generate_teardown(config)`: the empty `agentcore.json` and the target; `app/` is left alone.
- `main()` / `main_teardown()`: the same with the local config of `ENV_NAME`; `.mise/tasks/ac-gen.py` and `ac-gen-teardown.py` call them.

```bash
mise run ac-gen
```

```bash
ENV_NAME=tst mise run ac-gen
```

---

## 6. Tests

| Test file | Covers |
| :--- | :--- |
| `test_agentcore_project_registry.py` | the runtimes and their protocols; every runtime module has `main()`, and `app` for `HTTP` |
| `test_agentcore_project_project_files.py` | the env vars; `agentcore.json` (header, protocol, Python, `envVars`, policy); every runtime name in `cdk-stack.ts`, and its `if`; the empty project; the target; `write_json` |
| `test_agentcore_project_gen.py` | `main()` for another environment into a temporary directory; `main_teardown()` |

```bash
.venv/bin/python tests/agentcore_project/test_agentcore_project_registry.py
.venv/bin/python tests/agentcore_project/test_agentcore_project_project_files.py
.venv/bin/python tests/agentcore_project/test_agentcore_project_gen.py
```

---

## 7. Registering a runtime

1. Its names in the config (`20-centralized-config.md`, section 5) and its runtime module (`30-mcp-runtime.md` or `40-agent-runtime.md`).
2. A `RuntimeSpec` entry in `get_runtime_specs(config)`, with a sample payload, the next free local port, and for an agent its `mcp_runtimes`; update `test_get_runtime_specs`.
3. For an agent that uses it: a `bind()` line in `cdk-stack.ts` (`50-agentcore-project-layout.md`, section 4).
4. `mise run ac-gen`, then check the packaging (layer 3), then `mise run gen-env-tasks` for its generated tasks.
