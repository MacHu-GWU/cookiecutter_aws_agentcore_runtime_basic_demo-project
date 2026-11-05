---
name: aws-agentcore-new-agent
description: "Add a new agent runtime (protocol HTTP, Strands on BedrockAgentCoreApp) to this AgentCore project: its name and model in the config, the runtime module with its own tools and its MCP connections (bind, SigV4), its RuntimeSpec, its permissions, its local tasks and port, and the tests, then verify it locally and package it. Use when the user wants a new agent on AgentCore Runtime, or an agent that uses one or more of the project's MCP runtimes."
---

Add one agent runtime to the project, end to end, following the patterns of `SiteAgent`.

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

A short citation such as `30` means the reference of that number. Read ../aws-agentcore-base/references/80-invoke-and-observe.md when a deployed runtime is slow or fails, or to call it from code.

Use the `aws-agentcore-new-mcp` skill first if the agent needs an MCP runtime that does not exist yet. For new modules and tests, follow the `pywf-oss-add-module` and `pywf-oss-write-test` skills.

## 1. Agree on the design first

Ask, then propose, and wait for the user's yes before writing files:

- **What the agent is for**, in one sentence; that becomes its system prompt.
- **Its tools**: which of the project's MCP runtimes it uses, and which tools of its own (plain functions in a business subpackage, listed in `TOOLS` of its layer 1 module).
- **The model**: a Bedrock model or cross-region inference profile the account can call. Check it before relying on it (`80`, section 6: an agreement can be `NOT_AVAILABLE` in an account although the console lists the model).
- **The request and response**: the payload fields `invoke` reads, and what it returns.

Then propose, in one message:

| Item | Proposal |
| :--- | :--- |
| Runtime name (`51`, section 1) | PascalCase ending in `Agent`, such as `DispatchAgent`; physical name within 48 characters for every environment |
| Layer 1 module | `<pkg>/<domain>/<snake_name>_agent.py`: `SYSTEM_PROMPT`, `TOOLS` |
| Runtime module | `<pkg>/runtimes/<snake_name>_agent.py` |
| Model | config field `<snake>_model_id`, its value per environment |
| MCP runtimes | one `bind()` line each in `cdk-stack.ts`, and the env var each sets |
| Local port | the next free one after the used ones in `mise.toml` `[env]` |

## 2. Build it, in this order

1. **Names.** In `config/config_01_name.py`: `agentcore_runtime_name_<snake>` and `agentcore_runtime_physical_name_<snake>`. Assert both in `tests/config/test_config_config_01_name.py`.
2. **Model in the config** (`20`, section 5): a `<snake>_model_id` field in `Config`, its value in `config/config-shared.json5` (or per environment), `config/example/`, the `config` fixture in `tests/conftest.py`, and the inline config of `test_load_from_local_config_file`.
3. **Layer 1** (`40-agent-runtime.md`, section 2): `<pkg>/<domain>/<snake_name>_agent.py` with `SYSTEM_PROMPT` and `TOOLS`, the tool functions, and their tests, like `power_plant/site_agent.py`.
4. **Runtime module** (`40-agent-runtime.md`, sections 3 and 4): copy the shape of `runtimes/site_agent.py`: `make_agent`, `build_agent` (with `one.new_boto_ses()`, `one.config.<snake>_model_id`, one `get_mcp_connection` per MCP runtime), `agent = ProcessAgent(build_agent)`, `invoke`, `main()`. Reuse `runtimes/common.py` and `runtimes/mcp_connection.py`; never copy them. Test it like `tests/runtimes/test_runtimes_site_agent.py`.
5. **Register it** (`51`, section 7): a `RuntimeSpec(name=..., module="runtimes.<snake>_agent", protocol=RuntimeProtocolEnum.HTTP)` in `get_runtime_specs()` of `agentcore_project/registry.py`; update `test_get_runtime_specs`. The `HTTP` protocol makes the generated `main.py` expose `app` too (`52`, section 1).
6. **Bind its MCP runtimes**: a `this.application.runtime('<Mcp>').bind(this.application.runtime('<Agent>'))` line per MCP runtime in `agentcore/cdk/lib/cdk-stack.ts` (`40-agent-runtime.md`, section 4). Nothing else goes in that file (`50`, section 4).
7. **Permissions** (`60`, section 1): the CLI-created role can already call Bedrock models; add statements to the `agentcore_deps` policy only for other AWS access the agent's own tools need.
8. **Local tasks** (`40-agent-runtime.md`, section 5; `53` for `ac-dev-*`): a port variable `LOCAL_<NAME>_PORT` in `[env]`, then `ac-local-<slug>` and `ac-dev-<slug>` copied from `ac-local-agent` / `ac-dev-agent`, with `MCP_URL` (or one variable per MCP runtime) pointing at the local MCP ports, and a `-call` task like `ac-local-agent-call` with a sample `--prompt`. Its registry entry gets a sample `{"prompt": ...}` payload, for the generated `ac-invoke-<env>-<slug>` (`51`, section 1).

## 3. Verify

Run, and fix until each passes:

```bash
mise run format && mise run lint
mise run cov
mise run ac-check-wheels
mise run ac-build
mise run build-doc
```

Then start its MCP servers and the agent with the `ac-local-*` tasks, and send the sample payload. That calls the Bedrock model with the dev profile: say so before running it. `ac-dev-<slug>` also needs the config deployed (`config-deploy-<env>`), which changes AWS: ask first.

Deploying is a separate step with the user's yes (`60`): `mise run gen-env-tasks` first, then `mise run ac-chain-up-<env>` for the whole chain, or only `ac-deploy-<env>` when only code changed; then `mise run ac-test-<env>`.

## 4. Report

List the files created and changed, the tools and MCP runtimes the agent uses, the model, the local task names and port, the answer of the local test call, and what is not verified yet (usually: the deploy). If a fact in `aws-agentcore-base` turned out wrong or a new pattern appeared, update that reference too and say so.
