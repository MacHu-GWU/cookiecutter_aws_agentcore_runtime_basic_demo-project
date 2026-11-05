---
description: "OP-2 Centralized Config: the project's config as the one source of truth for everything AgentCore reads, the copies generated from it, the AgentCore values and names it holds, how each runtime gets it (files locally, one SSM SecureString on AgentCore), how config-deploy writes that copy, and how to add a config field a runtime uses. Read before adding or changing a config value or name a runtime uses, when a runtime cannot load its config, or before deploying or deleting the config of an environment."
---

# Centralized Config

Implements **OP-2**.

| | |
| :--- | :--- |
| EP | `<package_name>/config/config_00_main.py` (the model and its loaders) |
| FP | `config/*.json5`, `config/example/`, `<package_name>/config/**`, `<package_name>/one/one_01_config.py` (`one.config`), `<package_name>/one/one_06_config_deploy.py`, `.mise/tasks/config-deploy.py`, `.mise/tasks/config-delete.py`, `tests/config/**`, `tests/one/test_one_one_0{1,6}_*.py`, the `config` fixture and fake secret files of `tests/conftest.py` |
| CMD | `mise run cov`; `mise run config-deploy-<env>`, `mise run config-delete-<env>` (both change AWS: the user's yes, one environment per yes) |

How the model is written, how names are built, and how the files are loaded in general belong to the `pywf-aws-cdk-base` skill (references *Config Model*, *Names in the Config*, *Config Loading*). This file is what AgentCore adds.

---

## 1. One source of truth

AgentCore has a configuration of its own: the CLI project file `agentcore.json`, the deployment targets `aws-targets.json`, each runtime's environment variables. The project has more than AgentCore in it (CDK stacks, scripts, other services), and they all need the same values. So:

- **The project's config is the only place a value is written.** Everything AgentCore reads is a copy, generated from it by code and refreshed by a mise task.
- **A copy is never edited by hand**, and is git-ignored when it is a file. To change it, change the config and run the task that writes the copy; a task that needs a copy writes it first.

```text
config/*.json5 ──► Config (one environment, validated)
   │
   ├── mise run ac-gen              → agentcore/agentcore.json, agentcore/aws-targets.json
   │                                  (runtimes, envVars, policies, the target)
   ├── mise run config-deploy-<env> → the SSM parameter the AgentCore runtimes read
   └── mise run gen-env-tasks       → the per-environment tasks of mise.toml
```

`ENV_NAME` (default `dev`) selects the environment of `ac-gen`; each `config-deploy-<env>` task sets its own.

---

## 2. What the config holds for AgentCore

**Values**, fields of `Config`:

| Field | What | Where |
| :--- | :--- | :--- |
| `agentcore_project_name` | the AgentCore CLI project name; starts every AgentCore resource name. The model checks it: a letter, then letters and digits, at most 23 characters | `config-shared.json5` |
| `<agent>_model_id` | the Bedrock model or cross-region inference profile of each agent | `config-shared.json5`, or per environment |
| a connection string, an API key | what a runtime's dependencies need to connect | a `-secret` file |

**Names**, properties of `ConfigNameMixin` in `config_01_name.py`, under the `AgentCore` banner and next to the other resource types:

| Property | Value |
| :--- | :--- |
| `agentcore_target_name` | the CLI deployment target, named after the environment |
| `agentcore_runtime_name_<x>` | a runtime's name in `agentcore.json`, PascalCase, ending in `Mcp` or `Agent` |
| `agentcore_runtime_physical_name_<x>` | the name AWS knows it by, `<project>_<target>_<Runtime>`; `get_agentcore_runtime_physical_name` raises `ValueError` beyond AgentCore's 48 characters |
| `cft_stack_name_agentcore` | the stack the CLI deploys, `AgentCore-<project>-<target>` |
| `iam_policy_{name,arn,url}_agentcore_runtime` | the managed policy every runtime's execution role gets |
| `ssm_param_{name,arn,url}_config` | the parameter of section 3 |

A runtime ID, its ARN, and its log group end in a suffix AWS assigns at deploy time, so no property can build them.

---

## 3. How each runtime gets its config

`one.config` is `Config.load(env_name, runtime_name, ssm_client)`, loaded once per process and cached:

| Runtime | Source | Loader |
| :--- | :--- | :--- |
| `local` | the four `config/*.json5` files of the environment | `load_from_local_config_file` |
| `agentcore_local`, `agentcore` | the SSM parameter named by `CONFIG_SSM_PARAM_NAME` (an `envVars` entry the project sets on every runtime), read with `one.ssm_client` | `load_from_ssm` |
| `ci` | none: raises `NotImplementedError` (deploys run from a developer's machine) | |

Why one SSM parameter:

- **Not the config files in the code zip**: the packaged runtime cannot see `config/`, and copying the files in would ship the secrets in the CodeZip.
- **Not one environment variable per value**: secrets would sit in plain text on the runtime, and the values would live in two places.
- **One `SecureString`, the whole config as JSON**, encrypted with the AWS-managed key `aws/ssm`: the runtime policy grants `ssm:GetParameter` on it, and that key needs no extra grant when used through SSM in the account.
- **Cost**: one `GetParameter` per process, so one per runtime session, far below the SSM limits.
- **Fail early**: a missing parameter raises `ValueError` naming `config-deploy-<env>`, and each runtime's `main()` loads the config before serving, so it fails at startup with that message in its log.

`json5` is imported inside `load_from_local_config_file`, because the runtimes do not install it; everything else `config/` imports is installed on the runtimes too.

---

## 4. Writing the copy: `config-deploy-<env>`

`<package_name>/one/one_06_config_deploy.py`, through `one.deploy_config()` and `one.delete_config()`:

| Task | Does | Prints |
| :--- | :--- | :--- |
| `config-deploy-<env>` | writes `config.model_dump_json()` to `ssm_param_name_config` as a `SecureString`, **only when it differs**, so an unchanged deploy adds no parameter version | `created`, `updated` (version `a -> b`), or `unchanged`, the size, the console URL |
| `config-delete-<env>` | deletes it; a missing one is not an error. Asks first: only `y` / `yes` goes on | `deleted` or `not found`, the console URL |

- Both are plain functions taking the config and the SSM client (`deploy_config`, `delete_config`); the `one` methods only pass the current environment's.
- When it takes effect: a runtime reads the config once per process, so a session that is already running keeps the old values; every new session reads the new ones. No code deploy is needed for a config change.
- Nothing else deletes the parameter: neither destroying a stack nor tearing down the runtimes. The runtimes of the environment cannot start without it.
- `config-deploy-all` / `config-delete-all` run it for every environment.

---

## 5. Adding a config value or name a runtime uses

1. **The field** in `Config`, with its `#:` comment, or **the name** as a property in `config_01_name.py`.
2. **Its values**: the json5 file of every environment that needs it (a secret in a `-secret` file only), and the matching `config/example/*.json5.example`.
3. **The tests**: the `config` fixture in `tests/conftest.py` (and the fake secret files there, for a secret), the inline files of `test_load_from_local_config_file`, an assertion in `test_names` for a name.
4. `mise run cov`.
5. For the deployed runtimes: `mise run config-deploy-<env>` (the user's yes); new sessions read it.

A new runtime adds two names, `agentcore_runtime_name_<x>` and `agentcore_runtime_physical_name_<x>`; `test_agentcore_runtime_physical_names_fit` then checks the physical name fits 48 characters in every environment with the committed files.

---

## 6. Tests

| Test file | Covers |
| :--- | :--- |
| `tests/config/test_config_config_00_main.py` | validation; the merge order of the four files; loading every environment; `load_from_ssm` (missing parameter, then round trip) and `load` on both AgentCore runtimes; `ci` raises |
| `tests/config/test_config_config_01_name.py` | every name's value; the 48-character limit; every physical name fits in every environment |
| `tests/one/test_one_one_01_config.py` | `one.config` locally, and from SSM on `agentcore` |
| `tests/one/test_one_one_06_config_deploy.py` | created, unchanged, updated, deleted, not found, any environment; what is deployed loads back as the same `Config` |

All AWS calls run against `moto`. `tests/conftest.py` gives every test fake secret files and a fixed `ENV_NAME=dev`, so the suite never reads the real secrets.
