---
name: aws-agentcore-change-mcp
description: "Change an existing MCP server runtime of this AgentCore project: add, change, or remove a tool, change where its data comes from, add a dependency or an AWS permission it needs, and keep the agents that call it working; then run and call it locally. Use when the user wants to add a feature to, fix, or extend an MCP runtime that already exists, or to change one of its tools."
argument-hint: "[mcp-runtime] [what to change]"
---

Change one MCP runtime that already exists, keeping it built the way `aws-agentcore-base` describes. Deploying the change is the `aws-agentcore-deploy` skill.

## 0. Know which runtime

The runtime registry, `get_runtime_specs(config)` in `<package_name>/agentcore_project/registry.py`, lists every runtime; the MCP ones have protocol `RuntimeProtocolEnum.MCP`. Match the user's words and the arguments (`$ARGUMENTS`) against each MCP runtime's name, slug, and module.

- **Exactly one match**, or the project has only one MCP runtime: say "Changing `<Runtime>`" in the first line and go on.
- **No match or several**: ask the user which one, offering the registry's MCP runtimes as the choices. Never guess.
- **Not this skill's job**: an agent's prompt or how it picks tools is `aws-agentcore-change-agent`; a new runtime is `aws-agentcore-new-mcp`; a failure whose cause is unknown is `aws-agentcore-debug`. Say which and switch.

## 1. Read

Read ../aws-agentcore-base/SKILL.md, then:
- ../aws-agentcore-base/references/20-centralized-config.md
- ../aws-agentcore-base/references/30-mcp-runtime.md
- ../aws-agentcore-base/references/51-agentcore-config.md
- ../aws-agentcore-base/references/52-agentcore-packaging.md

Read ../aws-agentcore-base/references/40-agent-runtime.md too if an agent calls this runtime (its name is in an agent's `mcp_runtimes`), and ../aws-agentcore-base/references/60-deploy.md if the change needs an AWS permission or resource. A short citation such as `30` means the reference of that number. For new modules and tests, follow the `pywf-oss-add-module` and `pywf-oss-write-test` skills.

Then read the runtime itself: its registry entry, its runtime module, the layer 1 functions it wraps, and their tests.

## 2. Agree on the change first

Propose, in one message, only the rows the change touches, and wait for the user's yes before writing files:

| Item | Proposal |
| :--- | :--- |
| Tools | each tool added, changed, or removed: name, inputs, result model |
| Data source (`30`, section 5) | a new `one` dependency, its config fields |
| Dependencies (`52`, section 2) | a new third-party import for the `agentcore` group; a new subpackage to copy into the runtimes |
| AWS access (`60`, section 1) | statements or resources for the `agentcore_deps` stack |
| Sample call (`51`, section 7) | a new `sample_payload` if its tool is renamed or removed |
| Agents affected | every agent with this runtime in its `mcp_runtimes`: a renamed or removed tool, or a changed result model, may break its prompt or tests |

## 3. Make it, layer by layer

1. **Layer 1** (`30`, section 2): the tool functions and their result models, with their unit tests. Same rules as a new one: dependencies as arguments, a docstring for the LLM, `Field(description=...)` on every field, no import of `one`, the config, or MCP.
2. **A dependency** (`30`, section 5; `20`, section 5): a `one` property in its own `one/one_0N_<topic>.py` with its test; its config fields in every `config/*.json5` that needs them, `config/example/`, and the fixtures of `tests/conftest.py`.
3. **Packaging** (`52`, section 2): a new subpackage goes in `RUNTIME_SUBPACKAGES` of `agentcore_project/codezip.py` and the `allowed` list of `test_assemble_runtime_dir`; a new third-party import goes in `[dependency-groups] agentcore` only, then `uv lock`.
4. **Layer 2** (`30`, section 3): one thin wrapper per tool in the runtime module (`doc_from`, the dependency from `one`, the result model as the return type), and its test in `tests/runtimes/`. A removed tool goes from both.
5. **The registry** (`51`, section 7): update `sample_payload` if its tool changed, and `test_get_runtime_specs`; then `mise run gen-env-tasks`.
6. **Permissions and resources** (`60`, section 1): statements in the `agentcore_deps` policy, new resources as new `s0N_` methods, names in the config, asserted in the stack's test.
7. **The agents that call it**: search their `SYSTEM_PROMPT`, own tools, and tests for each renamed or removed tool, and fix them in the same change; a change to the agent's behavior is the `aws-agentcore-change-agent` skill.

## 4. Verify

Run, and fix until each passes:

```bash
mise run format && mise run lint
mise run cov
mise run ac-check-wheels
mise run ac-build
```

Then `mise run ac-local-<slug>` and `mise run ac-local-<slug>-call`. If the sample call does not reach the changed tool, call that tool by hand with `devtools/mcp_client.py` (`30`, section 4). If an agent calls this runtime, run the agent locally too and call it (`40`, section 5): that calls the Bedrock model, so say so first.

## 5. Report

List the files changed, each tool added, changed, or removed with its result model, the agents touched, and what is not verified yet (usually: the deploy, which is the `aws-agentcore-deploy` skill; a new permission needs `cdk-up-<env>-agentcore-deps-stack` first). If a fact in `aws-agentcore-base` turned out wrong, say so and propose the fix to that reference.
