---
name: aws-agentcore-new-mcp
description: "Add a new MCP server runtime to this AgentCore project: its name in the config, its business logic with Pydantic results, the FastMCP runtime module, its RuntimeSpec, its permissions in the agentcore_deps stack, its local tasks and port, and the tests, then verify it locally and package it. Use when the user wants a new MCP server, a new set of tools served on AgentCore Runtime, or to split tools out of an existing MCP runtime."
---

Add one MCP server runtime to the project, end to end, following the patterns of `PowerPlantMcp`.

Read ../aws-agentcore-base/SKILL.md, then:
- ../aws-agentcore-base/references/10-code-runtime.md
- ../aws-agentcore-base/references/20-centralized-config.md
- ../aws-agentcore-base/references/30-mcp-runtime.md
- ../aws-agentcore-base/references/40-agent-runtime.md
- ../aws-agentcore-base/references/50-agentcore-project-layout.md
- ../aws-agentcore-base/references/51-agentcore-config.md
- ../aws-agentcore-base/references/52-agentcore-packaging.md
- ../aws-agentcore-base/references/53-agentcore-dev.md
- ../aws-agentcore-base/references/60-deploy.md
- ../aws-agentcore-base/references/70-teardown.md (to remove a runtime or an environment)

A short citation such as `30` means the reference of that number; a citation of `11` means the legacy file `references/legacy/11-deploy-and-troubleshoot.md`, until OP-8 is rewritten.

For new modules and tests, follow the `pywf-oss-add-module` and `pywf-oss-write-test` skills.

## 1. Agree on the design first

Ask, then propose, and wait for the user's yes before writing files:

- **What questions the tools answer**, one tool per question, and what each returns.
- **Where the data comes from**: the existing database (`one.engine`), a new one (a new config field and resources), an AWS service, or an HTTP API.
- **Which agent calls it**, if any.

Then propose, in one message:

| Item | Proposal |
| :--- | :--- |
| Runtime name (`51`, section 1) | PascalCase ending in `Mcp`, such as `GridOpsMcp`; physical name within 48 characters for every environment |
| Business subpackage | `<pkg>/<domain>/` with `queries.py`, `schemas.py` (and `orm.py` for a database) |
| Runtime module | `<pkg>/runtimes/<snake_name>_mcp.py` |
| Tools | name, inputs, result model, for each |
| Local port | the next free one after the used ones in `mise.toml` `[env]` (`18731`, `18732`, ... ) |
| AWS access | the statements to add to the `agentcore_deps` policy, if any |

## 2. Build it, in this order

1. **Names.** In `config/config_01_name.py`: `agentcore_runtime_name_<snake>` and `agentcore_runtime_physical_name_<snake>`, next to the existing ones. Assert both in `tests/config/test_config_config_01_name.py`.
2. **Business logic** (`30-mcp-runtime.md`, section 2). Pydantic result models with `from_attributes` and a `Field(description=...)` on every field; query functions that take what they need (an engine, a client) as arguments and return those models; no import of config, `one`, or MCP. Unit test them with their own fixtures.
3. **Copy it into the runtimes** (`52`, section 2): add the subpackage to `RUNTIME_SUBPACKAGES` in `agentcore_project/codezip.py`, and to the `allowed` list of `test_assemble_runtime_dir`. A new third-party import goes in `[dependency-groups] agentcore` (and the base dependencies if the dev machine imports it), then `uv lock`.
4. **Runtime module** (`30-mcp-runtime.md`, section 3): copy the shape of `runtimes/power_plant_mcp.py`: `new_mcp_server`, one thin tool per query with `doc_from`, `main()` with `print_config_source` then `run_mcp_server`. Test it like `tests/runtimes/test_runtimes_power_plant_mcp.py`: tool list, descriptions = docstrings, no hidden parameter in the input schema, an output schema, a call per tool, `main()`.
5. **Register it** (`51`, section 7): a `RuntimeSpec(name=..., module="runtimes.<snake>_mcp", protocol=RuntimeProtocolEnum.MCP)` in `get_runtime_specs()` of `agentcore_project/registry.py`; update `test_get_runtime_specs`.
6. **Permissions and resources** (`60`, section 1): statements in the `agentcore_deps` policy, new resources as new `s0N_` methods of that stack, their names in the config; assert them in the stack's test. New config fields: add to `Config`, every `config/*.json5` that needs them, `config/example/`, and the `config` fixture plus fake secret files in `tests/conftest.py`.
7. **Local tasks** (`30`, section 4; `53` for `ac-dev-*`): in `mise.toml`, a port variable `LOCAL_<NAME>_PORT` in `[env]`, then `ac-local-<slug>` and `ac-dev-<slug>` copied from `ac-local-mcp` / `ac-dev-mcp` with the new port, module, and runtime name. For a call task, copy `ac-local-mcp-call` with the new port and a sample `--tool` / `--arguments` (`30-mcp-runtime.md`, section 4); the script is generic.
8. **An agent that calls it**: a `bind()` line and one more `get_mcp_connection` in the agent (`40-agent-runtime.md`, sections 4 and 6), or the `aws-agentcore-new-agent` skill for a new agent.

## 3. Verify

Run, and fix until each passes:

```bash
mise run format && mise run lint
mise run cov
mise run ac-check-wheels
mise run ac-build
mise run build-doc
```

Then start it with `ac-local-<slug>` and call it. `ac-dev-<slug>` also needs the config deployed (`config-deploy-<env>`), which changes AWS: ask first.

Deploying is a separate step with the user's yes (`60`): `mise run gen-env-tasks` first (the new runtime's `ac-invoke-<env>-<slug>`), then `mise run ac-chain-up-<env>` for the whole chain, or only the steps that changed (`cdk-up-<env>-agentcore-deps-stack`, then `ac-deploy-<env>`); then `mise run ac-test-<env>`.

## 4. Report

List the files created and changed, the tools with their result models, the local task names and port, and what is not verified yet (usually: the deploy). If a fact in `aws-agentcore-base` turned out wrong or a new pattern appeared, update that reference too and say so.
