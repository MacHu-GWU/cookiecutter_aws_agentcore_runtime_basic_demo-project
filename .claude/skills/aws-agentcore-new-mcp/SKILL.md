---
name: aws-agentcore-new-mcp
description: "Add a new MCP server runtime to this AgentCore project: its names in the config, its tool functions with Pydantic results, the thin FastMCP runtime module, its registry entry (local port, sample call), its permissions in the agentcore_deps stack, and the tests, then run and call it locally, package it, and deploy it with the user's yes. Use when the user wants a new MCP server, a new set of tools served on AgentCore Runtime, or to split tools out of an existing MCP runtime."
---

Add one MCP server runtime, end to end, the way the existing MCP runtime is built (the registry entry with protocol `MCP` in `agentcore_project/registry.py`); if the project has none, the references below are the whole pattern.

Read ../aws-agentcore-base/SKILL.md, then:
- ../aws-agentcore-base/references/10-code-runtime.md
- ../aws-agentcore-base/references/20-centralized-config.md
- ../aws-agentcore-base/references/30-mcp-runtime.md
- ../aws-agentcore-base/references/50-agentcore-project-layout.md
- ../aws-agentcore-base/references/51-agentcore-config.md
- ../aws-agentcore-base/references/52-agentcore-packaging.md
- ../aws-agentcore-base/references/53-agentcore-dev.md
- ../aws-agentcore-base/references/60-deploy.md

Read ../aws-agentcore-base/references/40-agent-runtime.md too if an agent will call it, and ../aws-agentcore-base/references/80-invoke-and-observe.md when the deployed runtime is slow or fails. A short citation such as `30` means the reference of that number. For new modules and tests, follow the `pywf-oss-add-module` and `pywf-oss-write-test` skills.

## 1. Agree on the design first

Ask, then propose, and wait for the user's yes before writing files:

- **What questions the tools answer**, one tool per question, and what each returns.
- **Where the data comes from**: an existing dependency of `one` (such as a database engine), a new one (a config field, its resources), an AWS service, or an HTTP API.
- **Which agent calls it**, if any: offer the agents of the registry (`get_runtime_specs(config)`, protocol `HTTP`) as the choices, or none.

Then propose, in one message:

| Item | Proposal |
| :--- | :--- |
| Runtime name (`51`, section 1) | PascalCase ending in `Mcp`, such as `GridOpsMcp`; physical name within 48 characters in every environment |
| Business subpackage (`30`, section 2) | `<package_name>/<domain>/`, with the tool functions and their result models (and storage models for a database) |
| Runtime module (`30`, section 3) | `<package_name>/runtimes/<snake_name>_mcp.py` |
| Tools | name, inputs, result model, for each |
| Local port (`51`, section 1) | the next free one in the registry (18731, 18732, ...) |
| Sample call | a tool and its arguments, for the call tasks |
| AWS access (`60`, section 1) | the statements to add to the `agentcore_deps` policy, if any |

## 2. Build it, in this order

1. **Names** (`20`, section 5): `agentcore_runtime_name_<snake>` and `agentcore_runtime_physical_name_<snake>` in `<package_name>/config/config_01_name.py`, asserted in `tests/config/test_config_config_01_name.py`. New config values (a connection string, an API key): the field, every `config/*.json5` that needs it, `config/example/`, and the fixtures of `tests/conftest.py`.
2. **Tool functions** (`30`, section 2): stateless, dependencies as arguments, a docstring for the LLM, a Pydantic result model with a `Field(description=...)` on every field; no import of `one`, the config, or MCP. Unit test them with their own fixtures.
3. **A dependency** the tools need (`30`, section 5): a `one` property in its own `one/one_0N_<topic>.py`, with its test.
4. **Copy it into the runtimes** (`52`, section 2): the subpackage in `RUNTIME_SUBPACKAGES` of `agentcore_project/codezip.py`, and in the `allowed` list of `test_assemble_runtime_dir`. A new third-party import goes in `[dependency-groups] agentcore` only (`mise run inst` installs it on the dev machine too), then `uv lock`.
5. **Runtime module** (`30`, section 3): `new_mcp_server("<Runtime>")`, one thin tool per function with `doc_from` and the dependency from `one`, `main()` with `print_config_source` then `run_mcp_server`. Test it like the existing MCP runtime's test: the server name, the tool list, descriptions = docstrings, no dependency in the input schema, an output schema, a call per tool, `main()`.
6. **Register it** (`51`, section 7): a `RuntimeSpec(name=..., module="runtimes.<snake_name>_mcp", protocol=RuntimeProtocolEnum.MCP, sample_payload=<a JSON-RPC tools/call request>, local_port=<next free>)` in `get_runtime_specs(config)`; update `test_get_runtime_specs`. Then `mise run gen-env-tasks`: its local, dev, call, invoke, and logs tasks appear.
7. **Permissions and resources** (`60`, section 1): statements in the `agentcore_deps` policy, new resources as new `s0N_` methods of that stack, names in the config; assert them in the stack's test.
8. **An agent that calls it**: connecting an existing agent to it is the `aws-agentcore-change-agent` skill (its `mcp_runtimes`, a `bind()` line, a `get_mcp_connection`); a new agent is the `aws-agentcore-new-agent` skill.

## 3. Verify

Run, and fix until each passes:

```bash
mise run format && mise run lint
mise run cov
mise run ac-check-wheels
mise run ac-build
mise run build-doc
```

Then `mise run ac-local-<slug>` and `mise run ac-local-<slug>-call`. `ac-dev-<slug>` also needs the config deployed (`config-deploy-<env>`), which changes AWS: ask first.

Deploying is a separate step with the user's yes: the `aws-agentcore-deploy` skill. Changing the runtime after this is the `aws-agentcore-change-mcp` skill.

## 4. Report

List the files created and changed, the tools with their result models, the generated task names and the local port, and what is not verified yet (usually: the deploy). If a fact in `aws-agentcore-base` turned out wrong or a new pattern appeared, update that reference too and say so.
