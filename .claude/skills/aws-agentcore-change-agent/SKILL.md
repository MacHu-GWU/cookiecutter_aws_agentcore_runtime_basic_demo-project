---
name: aws-agentcore-change-agent
description: "Change an existing agent runtime of this AgentCore project: its system prompt, its own tools, its model, the MCP runtimes it uses (connections and bind lines), or its request and response contract; then run and call it locally. Use when the user wants to add a feature to, fix, tune, or extend an agent that already exists, give it another MCP server, or switch its model."
argument-hint: "[agent-runtime] [what to change]"
---

Change one agent runtime that already exists, keeping it built the way `aws-agentcore-base` describes. Deploying the change is the `aws-agentcore-deploy` skill.

## 0. Know which agent

The runtime registry, `get_runtime_specs(config)` in `<package_name>/agentcore_project/registry.py`, lists every runtime; the agents have protocol `RuntimeProtocolEnum.HTTP`. Match the user's words and the arguments (`$ARGUMENTS`) against each agent's name, slug, and module.

- **Exactly one match**, or the project has only one agent: say "Changing `<Runtime>`" in the first line and go on.
- **No match or several**: ask the user which one, offering the registry's agents as the choices. Never guess.
- **Not this skill's job**: a tool of an MCP runtime is `aws-agentcore-change-mcp`; a new agent is `aws-agentcore-new-agent`; a failure whose cause is unknown is `aws-agentcore-debug`. Say which and switch.

If the user names an MCP runtime to add, it must be in the registry with protocol `MCP`; if it is not, offer the ones that are, or `aws-agentcore-new-mcp` first.

## 1. Read

Read ../aws-agentcore-base/SKILL.md, then:
- ../aws-agentcore-base/references/20-centralized-config.md
- ../aws-agentcore-base/references/40-agent-runtime.md
- ../aws-agentcore-base/references/51-agentcore-config.md

Read ../aws-agentcore-base/references/30-mcp-runtime.md to understand an MCP runtime it uses, ../aws-agentcore-base/references/50-agentcore-project-layout.md before editing `cdk-stack.ts`, ../aws-agentcore-base/references/52-agentcore-packaging.md for a new import, ../aws-agentcore-base/references/60-deploy.md for a new AWS permission, and ../aws-agentcore-base/references/80-invoke-and-observe.md before switching the model. A short citation such as `40` means the reference of that number. For new modules and tests, follow the `pywf-oss-add-module` and `pywf-oss-write-test` skills.

Then read the agent itself: its registry entry, its layer 1 module (`SYSTEM_PROMPT`, `TOOLS`, request and response models), its runtime module, and their tests.

## 2. Agree on the change first

Propose, in one message, only the rows the change touches, and wait for the user's yes before writing files:

| Item | Proposal |
| :--- | :--- |
| Prompt (`40`, section 2) | the new `SYSTEM_PROMPT`, or the part that changes |
| Own tools (`40`, section 2) | each tool added, changed, or removed in `TOOLS`: name, inputs, result model |
| Model (`20`, section 5) | the new value of its model ID field, per environment; checked as callable (`80`, section 6) |
| MCP runtimes (`40`, section 4) | each one added or removed: its `mcp_runtimes` entry, its `bind()` line, its `get_mcp_connection` |
| Contract (`40`, section 2) | fields added to or removed from `<Agent>Request` / `<Agent>Response`; who calls it and must change |
| Sample prompt (`51`, section 7) | a new `sample_payload` if the contract changed |
| AWS access (`60`, section 1) | statements for the `agentcore_deps` policy, only for what its own tools need beyond Bedrock |

## 3. Make it, layer by layer

1. **Layer 1** (`40`, section 2): the prompt, `TOOLS` and their functions, the request and response models, with their tests; still no `strands` import.
2. **The model** (`20`, section 5): the model ID field's value in `config/*.json5`, `config/example/`, and the test fixtures. A new field only if the agent did not have its own yet.
3. **Layer 2** (`40`, sections 3 and 4): `build_agent` gets one `get_mcp_connection("<Mcp>", ...)` per MCP runtime; `make_agent` stays built from its arguments only. Reuse `runtimes/common.py` and `runtimes/mcp_connection.py`; never copy them. Update the runtime's test.
4. **The registry** (`51`, section 7): `mcp_runtimes` and `sample_payload`, and `test_get_runtime_specs`; then `mise run gen-env-tasks`.
5. **Bind lines** (`50`, section 4): one `this.application.runtime('<Mcp>').bind(this.application.runtime('<Agent>'));` per MCP runtime in `agentcore/cdk/lib/cdk-stack.ts`, inside the `if`; remove the line of an MCP runtime it no longer uses. Nothing else goes in that file.
6. **Packaging** (`52`, section 2): a new third-party import goes in `[dependency-groups] agentcore` only, then `uv lock`.
7. **Permissions** (`60`, section 1): only if its own tools need AWS access beyond the model.

## 4. Verify

Run, and fix until each passes:

```bash
mise run format && mise run lint
mise run cov
mise run ac-check-wheels
mise run ac-build
```

Then start its MCP runtimes and the agent with their `ac-local-<slug>` tasks, and `mise run ac-local-<slug>-call`; if the sample prompt does not exercise the change, call it by hand with `devtools/agent_client.py` and a prompt that does (`40`, section 5). That calls the Bedrock model with the environment's profile: say so before running it. A prompt change is judged by its answers: show the user the answer, and run it again with the same session ID if the change is about memory within a conversation.

## 5. Report

List the files changed, what changed in the prompt, tools, model, MCP runtimes, and contract, the answer of the local call, and what is not verified yet (usually: the deploy, which is the `aws-agentcore-deploy` skill). If a fact in `aws-agentcore-base` turned out wrong, say so and propose the fix to that reference.
