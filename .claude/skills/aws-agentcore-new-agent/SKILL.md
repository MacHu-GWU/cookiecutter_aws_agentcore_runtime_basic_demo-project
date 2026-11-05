---
name: aws-agentcore-new-agent
description: "Add a new agent runtime (protocol HTTP, Strands on BedrockAgentCoreApp) to this AgentCore project: its names and model in the config, its prompt and own tools in plain Python, the thin runtime module with one agent per process and its MCP connections (bind, SigV4), its registry entry (local port, sample prompt, MCP runtimes), its permissions, and the tests, then run and call it locally, package it, and deploy it with the user's yes. Use when the user wants a new agent on AgentCore Runtime, or an agent that uses one or more of the project's MCP runtimes."
---

Add one agent runtime, end to end, the way the existing agent runtime is built (the registry entry with protocol `HTTP` in `agentcore_project/registry.py`); if the project has none, the references below are the whole pattern.

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

Read ../aws-agentcore-base/references/80-invoke-and-observe.md when latency matters or the deployed agent fails. A short citation such as `40` means the reference of that number. Use the `aws-agentcore-new-mcp` skill first if the agent needs an MCP runtime that does not exist yet. For new modules and tests, follow the `pywf-oss-add-module` and `pywf-oss-write-test` skills.

## 1. Agree on the design first

Ask, then propose, and wait for the user's yes before writing files:

- **What the agent is for**, in one sentence; that becomes its system prompt.
- **Its tools**: which of the project's MCP runtimes it uses, and which tools of its own (plain functions, listed in `TOOLS` of its layer 1 module). Offer the MCP runtimes of the registry (`get_runtime_specs(config)`, protocol `MCP`) as the choices; never assume one. A name that is not there is a new MCP runtime: `aws-agentcore-new-mcp` first.
- **The model**: a Bedrock model or cross-region inference profile the account can call. Check it before relying on it (`80`, section 6: an agreement can be `NOT_AVAILABLE` in an account although the console lists the model).
- **The request and response**: the payload fields a caller sends and what the agent returns; they become `<Agent>Request` and `<Agent>Response` (`40`, section 2).

Then propose, in one message:

| Item | Proposal |
| :--- | :--- |
| Runtime name (`51`, section 1) | PascalCase ending in `Agent`, such as `DispatchAgent`; physical name within 48 characters in every environment |
| Layer 1 module (`40`, section 2) | `<package_name>/<domain>/<snake_name>_agent.py`: `SYSTEM_PROMPT`, `TOOLS` |
| Runtime module (`40`, section 3) | `<package_name>/runtimes/<snake_name>_agent.py` |
| Model | config field `<snake>_model_id`, its value per environment |
| MCP runtimes (`40`, section 4) | its `mcp_runtimes`, one `bind()` line each in `cdk-stack.ts` |
| Local port (`51`, section 1) | the next free one in the registry |
| Sample prompt | for the call tasks |

## 2. Build it, in this order

1. **Names** (`20`, section 5): `agentcore_runtime_name_<snake>` and `agentcore_runtime_physical_name_<snake>` in `<package_name>/config/config_01_name.py`, asserted in `tests/config/test_config_config_01_name.py`.
2. **Model in the config** (`20`, section 5): a `<snake>_model_id` field in `Config`, its value in `config/config-shared.json5` (or per environment), `config/example/`, the `config` fixture in `tests/conftest.py`, and the inline config of `test_load_from_local_config_file`.
3. **Layer 1** (`40`, section 2): the module with `<Agent>Request`, `<Agent>Response`, `SYSTEM_PROMPT`, and `TOOLS`, the tool functions, and their tests; no `strands` import.
4. **Runtime module** (`40`, sections 3 and 4): `make_agent`, `build_agent` (with `one.new_boto_ses()`, `one.config.<snake>_model_id`, one `get_mcp_connection("<Mcp>", ...)` per MCP runtime), `agent = ProcessAgent(build_agent)`, `invoke` (validate the payload, a 400 when it does not), `main()`. Reuse `runtimes/common.py` and `runtimes/mcp_connection.py`; never copy them. Test it like the existing agent runtime's test.
5. **Register it** (`51`, section 7): a `RuntimeSpec(name=..., module="runtimes.<snake_name>_agent", protocol=RuntimeProtocolEnum.HTTP, sample_payload={"prompt": ...}, local_port=<next free>, mcp_runtimes=[...])` in `get_runtime_specs(config)`; update `test_get_runtime_specs`. The `HTTP` protocol makes the generated `main.py` expose `app` too (`52`, section 1). Then `mise run gen-env-tasks`.
6. **Bind its MCP runtimes** (`40`, section 4): a `this.application.runtime('<Mcp>').bind(this.application.runtime('<Agent>'));` line per MCP runtime in `agentcore/cdk/lib/cdk-stack.ts`, inside the `if`. Nothing else goes in that file (`50`, section 4). A registry test checks every `mcp_runtimes` entry has its line.
7. **Permissions** (`60`, section 1): the CLI-created role can already call Bedrock models; add statements to the `agentcore_deps` policy only for other AWS access the agent's own tools need.

## 3. Verify

Run, and fix until each passes:

```bash
mise run format && mise run lint
mise run cov
mise run ac-check-wheels
mise run ac-build
mise run build-doc
```

Then start its MCP runtimes and the agent with their `ac-local-<slug>` tasks, and `mise run ac-local-<slug>-call`. That calls the Bedrock model with the environment's profile: say so before running it. `ac-dev-<slug>` also needs the config deployed (`config-deploy-<env>`), which changes AWS: ask first.

Deploying is a separate step with the user's yes: the `aws-agentcore-deploy` skill. Changing the agent after this is the `aws-agentcore-change-agent` skill.

## 4. Report

List the files created and changed, the tools and MCP runtimes the agent uses, the model, the generated task names and the local port, the answer of the local call, and what is not verified yet (usually: the deploy). If a fact in `aws-agentcore-base` turned out wrong or a new pattern appeared, update that reference too and say so.
