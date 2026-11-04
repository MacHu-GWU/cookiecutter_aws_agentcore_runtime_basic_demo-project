---
name: aws-agentcore-new-agent
description: "Add a new agent runtime (protocol HTTP, Strands on BedrockAgentCoreApp) to this AgentCore project: its name and model in the config, the runtime module with its own tools and its MCP connections (bind, SigV4), its RuntimeSpec, its permissions, its local tasks and port, and the tests, then verify it locally and package it. Use when the user wants a new agent on AgentCore Runtime, or an agent that uses one or more of the project's MCP runtimes."
---

Add one agent runtime to the project, end to end, following the patterns of `SiteAgent`.

Read ../aws-agentcore-base/SKILL.md, then:
- ../aws-agentcore-base/references/03-project-layout.md
- ../aws-agentcore-base/references/04-packaging.md
- ../aws-agentcore-base/references/05-naming.md
- ../aws-agentcore-base/references/06-runtime-and-config.md
- ../aws-agentcore-base/references/07-agentcore-vs-other-resources.md
- ../aws-agentcore-base/references/08-agent-to-mcp.md
- ../aws-agentcore-base/references/10-local-dev.md

Read ../aws-agentcore-base/references/02-runtime-sessions-and-cold-starts.md when latency matters, and ../aws-agentcore-base/references/11-deploy-and-troubleshoot.md before a deploy. Use the `aws-agentcore-new-mcp` skill first if the agent needs an MCP runtime that does not exist yet. For new modules and tests, follow the `pywf-oss-add-module` and `pywf-oss-write-test` skills.

## 1. Agree on the design first

Ask, then propose, and wait for the user's yes before writing files:

- **What the agent is for**, in one sentence; that becomes its system prompt.
- **Its tools**: which of the project's MCP runtimes it uses, and which tools of its own (plain functions in a business subpackage, wrapped with Strands' `tool`).
- **The model**: a Bedrock model or cross-region inference profile the account can call. Check it before relying on it (`11`, section 4: an agreement can be `NOT_AVAILABLE` in an account although the console lists the model).
- **The request and response**: the payload fields `invoke` reads, and what it returns.

Then propose, in one message:

| Item | Proposal |
| :--- | :--- |
| Runtime name (`05`) | PascalCase ending in `Agent`, such as `DispatchAgent`; physical name within 48 characters for every environment |
| Runtime module | `<pkg>/runtimes/<snake_name>_agent.py` |
| Model | config field `<snake>_model_id`, its value per environment |
| MCP runtimes | one `bind()` line each in `cdk-stack.ts`, and the env var each sets |
| Local port | the next free one after the used ones in `mise.toml` `[env]` |

## 2. Build it, in this order

1. **Names.** In `config/config_01_name.py`: `agentcore_runtime_name_<snake>` and `agentcore_runtime_physical_name_<snake>`. Assert both in `tests/config/test_config_config_01_name.py`.
2. **Model in the config** (`06`): a `<snake>_model_id` field in `Config`, its value in `config/config-shared.json5` (or per environment), `config/example/`, the `config` fixture in `tests/conftest.py`, and the inline config of `test_load_from_local_config_file`.
3. **Shared MCP connection code.** `AwsSigV4Auth` and `get_runtime_mcp_url` live in `runtimes/site_agent.py`. Before a second agent uses them, move them to a shared module, such as `runtimes/mcp_connection.py`, with their tests, and import them from both agents. Do not copy them.
4. **Runtime module**: copy the shape of `runtimes/site_agent.py`:
   - `app = BedrockAgentCoreApp()` and an `@app.entrypoint` `invoke(payload)` that, under a lock, calls the agent of the process and returns a JSON-friendly dict.
   - One agent per process (`08`, section 4): `get_agent()` builds it on first use with `one.config.<snake>_model_id` and its MCP connections; `reset_agent()` drops it when a call fails.
   - One `get_<mcp>_connection()` per MCP runtime, with the three cases of `08`, section 2, and its own local URL variable.
   - Credentials and the SigV4 signer created inside `invoke`, never at import time (`08`, section 3).
   - `main()` that prints the config source (`06`, section 5) then `app.run()`.
   - If the model wraps its answer in tags, reuse `strip_thinking`.
   Test it like `tests/runtimes/test_runtimes_site_agent.py`: the connection cases, the agent loads every tool against a real local MCP server (no LLM call), `invoke` with fake agents (reused across calls, reset after a failure), `main()`.
5. **Register it**: a `RuntimeSpec(name=..., module="runtimes.<snake>_agent", protocol="HTTP")` in `get_runtime_specs()`; update `test_get_runtime_specs`. The `HTTP` protocol makes the generated `main.py` expose `app` too (`04`, section 1).
6. **Bind its MCP runtimes**: a `this.application.runtime('<Mcp>').bind(this.application.runtime('<Agent>'))` line per MCP runtime in `agentcore/cdk/lib/cdk-stack.ts` (`08`). Nothing else goes in that file (`07`).
7. **Permissions** (`07`): the CLI-created role can already call Bedrock models; add statements to the `agentcore_deps` policy only for other AWS access the agent's own tools need.
8. **Local tasks** (`10`): a port variable `LOCAL_<NAME>_PORT` in `[env]`, then `ac-local-<slug>` and `ac-dev-<slug>` copied from `ac-local-agent` / `ac-dev-agent`, with `MCP_URL` (or one variable per MCP runtime) pointing at the local MCP ports, and a `-call` task like `ac-local-agent-call` with a sample payload. For the deployed agent, a task like `ac-invoke-dev-agent`.

## 3. Verify

Run, and fix until each passes:

```bash
mise run format && mise run lint
mise run cov
mise run ac-gen && .venv/bin/python .mise/tasks/ac-check-wheels.py
mise run ac-build
mise run build-doc
```

Then start its MCP servers and the agent with the `ac-local-*` tasks, and send the sample payload. That calls the Bedrock model with the dev profile: say so before running it. `ac-dev-<slug>` also needs the config deployed (`config-deploy-<env>`), which changes AWS: ask first.

Deploying is a separate step with the user's yes (`11`): `mise run ac-chain-up-<env>` for the whole chain, or only `ac-deploy-<env>` when only code changed.

## 4. Report

List the files created and changed, the tools and MCP runtimes the agent uses, the model, the local task names and port, the answer of the local test call, and what is not verified yet (usually: the deploy). If a fact in `aws-agentcore-base` turned out wrong or a new pattern appeared, update that reference too and say so.
