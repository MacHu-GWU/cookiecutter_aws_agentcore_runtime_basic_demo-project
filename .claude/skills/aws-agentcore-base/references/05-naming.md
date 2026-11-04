---
description: "How AgentCore names are built from the config: the CLI project name, the target (= environment), runtime names and the physical names AWS sees (48-character limit), the stack name, log groups, and the env var bind() sets. Read before naming a new runtime, or when looking for a deployed runtime, its stack, or its logs."
---

# AgentCore Names

Every name is a property in `config/config_01_name.py` (the project rule: a stack or script builds no name string). The general naming rules are in the `pywf-aws-cdk-base` skill, reference *Names in the Config*.

---

## 1. The parts

| Part | Config | Rule | This repo |
| :--- | :--- | :--- | :--- |
| CLI project name | `agentcore_project_name` (`config-shared.json5`) | a letter, then letters and digits, at most 23 characters (pattern checked by the `Config` model) | `AcRtDemo` |
| Target | `agentcore_target_name` | the environment name | `dev`, `tst`, `prd` |
| Runtime name | `agentcore_runtime_name_<x>` | PascalCase, the `name` in `agentcore.json` and in `runtime('<Name>')` of `cdk-stack.ts` | `PowerPlantMcp`, `SiteAgent` |

---

## 2. What AWS sees

| Resource | Config | Pattern | Example |
| :--- | :--- | :--- | :--- |
| Runtime | `agentcore_runtime_physical_name_<x>` | `<Project>_<target>_<Runtime>`, at most 48 characters (raises `ValueError` beyond) | `AcRtDemo_dev_PowerPlantMcp` |
| Stack | `cft_stack_name_agentcore` | `AgentCore-<Project>-<target>`, `_` turned into `-` | `AgentCore-AcRtDemo-dev` |
| Runtime ID / ARN | none: AWS appends a random suffix | `<physical name>-<10 chars>` | `AcRtDemo_dev_PowerPlantMcp-OhSbwKEDw9` |
| Log group | none (it contains the runtime ID) | `/aws/bedrock-agentcore/runtimes/<runtime ID>-DEFAULT` | `/aws/bedrock-agentcore/runtimes/AcRtDemo_dev_SiteAgent-AkH3to5PQB-DEFAULT` |

The runtime ID is known only after a deploy, so nothing in the repo can build an ARN or a log group name. Find them with `agentcore status --target <env>`, the stack's resources in the console (`cft_stack_url_agentcore`), or `aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/<physical name>`.

---

## 3. Names that bind() makes

`runtime('<A>').bind(runtime('<B>'))` sets on `<B>` the env var `AGENTCORE_RUNTIME_<A in upper case>_ARN`, such as `AGENTCORE_RUNTIME_POWERPLANTMCP_ARN`. Keep the Python constant that reads it (`MCP_ARN_ENV_VAR` in `runtimes/site_agent.py`) in sync with the runtime name (`08`).

---

## 4. Choosing a runtime name

- Short: the 48-character limit counts the project name and the target too. `AcRtDemo_prd_` already takes 13.
- A noun for what it is, with `Mcp` or `Agent` at the end, so the role is clear in the console.
- Add both `agentcore_runtime_name_<x>` and `agentcore_runtime_physical_name_<x>`, and assert both in `tests/config/test_config_config_01_name.py`.
