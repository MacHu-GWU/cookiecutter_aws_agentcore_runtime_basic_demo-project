---
description: "Operation-oriented design (OOD) of an AgentCore project made from this template: the OPs from code runtime detection, the central config, MCP and agent runtimes (local first, pure functions with injected dependencies), the AgentCore CLI project, deploy, teardown, invoke and observe, to toolchain maintenance, each with its EP, FP, and CMD, and the reference that implements each. Read before refactoring an AgentCore module, before moving a file between OPs, or when deciding which OP a new piece of AgentCore work belongs to."
---

# Operation-Oriented Design of an AgentCore Project

This is the design the code follows. When a refactor has to break it, change this file in the same change, a little, rather than letting code and design drift.

---

## 0. Conventions of this document

### 0.1 Scope

Everything specific to running an MCP server or an agent on AgentCore Runtime. Not in scope, and only referred to:

| Concern | Owner |
| :--- | :--- |
| Python library layout, code style, tests, docs, release, dependency upgrades | `pywf-oss-base` and its invokers |
| The config model and its loading, environments, the boto session, the `one` singleton, CDK stacks and their generated tasks | `pywf-aws-cdk-base` |

When a general mechanism is used for an AgentCore reason (a CDK stack for what the runtimes use, the config read from SSM, AgentCore tasks generated next to the CDK ones), the mechanism belongs to its owner, and the AgentCore decision belongs to an OP here.

### 0.2 Placeholders

The document is a template: it names no business domain of a particular project.

| Placeholder | Meaning | Example shape |
| :--- | :--- | :--- |
| `<package_name>` | the import package | `my_project` |
| `<domain>` | a business subpackage, named after its business | `<package_name>/<domain>/` |
| `<runtime_name>` | a runtime's module name, snake case, ending in `_mcp` or `_agent` | `orders_mcp` |
| `<Runtime>` | the runtime's name in `agentcore.json`, PascalCase | `OrdersMcp` |
| `<slug>` | the runtime's name in task names, kebab case | `orders-mcp` |
| `<NAME>` | the runtime's name in env var names, upper case | `ORDERSMCP` |
| `<env>` | an environment | `dev`, `tst`, `prd` |

### 0.3 Marks

- **Asks first**: changes AWS; run only after the user's yes, one environment per yes.

---

## 1. The OP map

| OP | Name | One sentence | Main CMD |
| :--- | :--- | :--- | :--- |
| OP-1 | Code runtime | Where the code is running, and how it knows. | `mise run cov` |
| OP-2 | Centralized config | The project's config is the one source of truth; everything AgentCore reads is generated from it. | `mise run ac-gen`, `config-deploy-<env>` |
| OP-3 | MCP runtime | Tools as pure functions, a thin MCP server around them, run and tested locally. | `mise run ac-local-<slug>` |
| OP-4 | Agent runtime | An agent's prompt and tools as pure Python, a thin Strands agent around them, run and tested locally against a local MCP server. | `mise run ac-local-<slug>` |
| OP-5 | AgentCore runtime | The AgentCore CLI project: its files, its config generated from ours, the package build, and `agentcore dev`. | `mise run ac-gen`, `ac-build`, `ac-dev-<slug>` |
| OP-6 | Deploy | Put an environment into AWS in order, then test it there. | `mise run ac-chain-up-<env>` |
| OP-7 | Teardown | Take an environment's AgentCore part out of AWS, in reverse order. | `mise run ac-chain-down-<env>` |
| OP-8 | Invoke and observe | Call the deployed runtimes from a client, manage sessions, read logs, debug. | `mise run ac-invoke-<env>-<slug>` |
| OP-9 | Maintain | Keep the toolchain current and the project's runtimes, environments, and docs in step over their life. | `mise run ac-check-layout` |

The OP order is also the refactor order: each OP builds only on the ones before it.

The invokers are walks through these OPs, each for one intent of the user; the mise tasks run the single steps:

| Invoker | Walk |
| :--- | :--- |
| `aws-agentcore-new-mcp` | OP-2-2 → OP-3 → OP-5-2 (registry) → OP-5-4 → OP-6 (asks first) |
| `aws-agentcore-new-agent` | OP-2-2 → OP-4 → OP-5-1 (`bind`) → OP-5-2 → OP-5-4 → OP-6 (asks first) |
| `aws-agentcore-change-mcp` | OP-3 (+ OP-2-2, OP-5-3, OP-6-1 as needed) → OP-5-2 → the agents that call it |
| `aws-agentcore-change-agent` | OP-4 (+ OP-2-2, OP-5-1 `bind`, OP-6-1 as needed) → OP-5-2 |
| `aws-agentcore-deploy` | OP-6-2 (the steps the change needs, asks first) → OP-6-4 → OP-8 (quick links) |
| `aws-agentcore-debug` | OP-8-3 → back to the OP the cause is in, then hands the fix to its invoker |

---

## 2. The core design: local first, pure functions, injected dependencies

Every MCP server and agent here has a local version and a deployed version, and **both run the same code**. That works because of one rule:

> Business code is a set of stateless functions. Everything outside them (a database engine, an AWS client, a model, an MCP connection, the config) is passed in as an argument. Only the thin runtime layer builds those dependencies, and it builds them for the runtime it is in (OP-1).

The layers, the same for an MCP server and an agent:

| Layer | What | Knows about | Tested by |
| :--- | :--- | :--- | :--- |
| 1. Business | pure functions and contract models; for an agent also its prompt | only its arguments | unit tests with fakes or local stand-ins (an in-memory database, a stub client) |
| 2. Framework | the MCP server or the Strands agent: decorators and a factory that wire layer 1 to the framework, and inject the dependencies | layer 1, the framework, `one` | tests against a real local server, no AWS |
| 3. Runtime entry | `main()`: load the config and the dependencies, print where they came from, serve | layer 2, `one` | a test of `main()` with the server stubbed |

Consequences:

- The local version leaves out what only the cloud needs (IAM, SigV4, SSM). The cloud version differs only in which dependencies layer 2 and 3 inject.
- Dependencies are built lazily, once per process, never at import time: an AgentCore microVM is restored from a snapshot, so anything made at import time (credentials above all) is stale.
- One process is one runtime session on AgentCore, so "once per process" is "once per session".

---

## OP-1 Code Runtime

The same code runs in four places, and has to know which one it is in to pick its dependencies (config source, credentials, region).

- EP: `<package_name>/runtime.py`
- FP: `<package_name>/constants.py` (the signal names and values), `<package_name>/runtime.py`, `tests/test_runtime.py`; the one writer of the project's own signal, `get_runtime_env_vars` (OP-5-2)
- CMD: `mise run cov`
- Docs: `10-code-runtime.md`

### OP-1-1 The four runtimes

| Runtime | What runs | Started by | AWS credentials |
| :--- | :--- | :--- | :--- |
| `local` | the package from the repo: tests, scripts, `ac-local-*` servers | a developer | the local profile of the environment |
| `agentcore_local` | the packaged copy in `app/<Runtime>/`, simulating AgentCore | `agentcore dev` (`ac-dev-*`) | the local profile |
| `ci` | tests on a CI runner, such as GitHub Actions; they run as `local` (`tests/conftest.py`), and loading the config is not supported here | the CI runner | the runner's environment or assumed role |
| `agentcore` | the deployed runtime | AgentCore Runtime | the runtime's execution role |

### OP-1-2 How the code knows: the signals

The hard part is telling `agentcore_local` from `agentcore`: AgentCore documents no variable that says "you run on AgentCore", and the two run the same packaged code.

| Signal | Set by | Means |
| :--- | :--- | :--- |
| `IS_AGENTCORE_RUNTIME=true` (exactly `true`) | the project, through `envVars` in `agentcore.json` (generated, OP-5-2); `agentcore dev` applies `envVars` too | `agentcore` or `agentcore_local` |
| `LOCAL_DEV` (any value) | `agentcore dev` only (undocumented CLI behavior, OP-9-2) | `agentcore_local` |
| `CI` | GitHub Actions and most CI services | `ci` |
| none of them | | `local` |

The order of the check: `IS_AGENTCORE_RUNTIME` first (then `LOCAL_DEV` splits it), then `CI`, then `local`.

### OP-1-3 Using it

- Code asks `runtime.current_runtime_name()` (or `one.runtime`), never `os.environ`; the signal names and the value `true` live only in `constants.py`, each with a docstring saying who sets it, and only `runtime.py` reads them. The answer is worked out on every call, never cached.
- Branch on it one runtime at a time, comparing with `RuntimeNameEnum.<name>.value` (the general rule of `pywf-aws-cdk-base`, reference *Runtime*).
- The tests write the signal names out instead of importing them: they are a contract with `agentcore.json` and the CLI.
- Only layers 2 and 3 of section 2 ask. Business code never does: it gets its dependencies already chosen.
- A new runtime kind (a container, a Lambda) is a new enum member plus its signal, in this OP only.

---

## OP-2 Centralized Config

AgentCore has its own configuration (`agentcore.json`, `aws-targets.json`, per-runtime `envVars`), and the project has more than AgentCore in it. So the **project's config is the source of truth**, and code generates every AgentCore setting from it. Nothing AgentCore reads is edited by hand.

- EP: `<package_name>/config/config_00_main.py` (the model and its loaders)
- FP: `config/*.json5`, `config/example/`, `<package_name>/config/**` (the AgentCore fields and names), `<package_name>/one/one_01_config.py`, `<package_name>/one/one_06_config_deploy.py` (writes the SSM copy), `.mise/tasks/config-{deploy,delete}.py`, `tests/config/**`, `tests/one/test_one_one_0{1,6}_*.py`, `tests/conftest.py`
- CMD: `mise run cov`; `mise run ac-gen` (derive for `ENV_NAME`); `mise run config-deploy-<env>` (asks first)
- Docs: `20-centralized-config.md`; the mechanics are in `pywf-aws-cdk-base`

### OP-2-1 One source, several derived copies

```text
config/*.json5  →  Config (one environment)
   ├── mise run ac-gen            → agentcore/agentcore.json, agentcore/aws-targets.json   (OP-5-2)
   ├── mise run config-deploy-<env> → one SSM SecureString, the whole config                (OP-6-2)
   └── mise run gen-env-tasks      → the per-environment and per-runtime tasks of mise.toml (OP-9-4)
```

Every derived copy is regenerated by its task; a task that needs one regenerates it first.

### OP-2-2 What the config holds for AgentCore

| Kind | Examples | Where |
| :--- | :--- | :--- |
| Values | the CLI project name, a model ID per agent, a connection string (secret file) | fields of `Config` |
| Names | the target, runtime names and physical names (48-character limit), the AgentCore stack, the runtime policy, the config parameter | properties in `config_01_name.py`; nothing else builds a name string |

To add one: the field or property, its values in `config/*.json5` and `config/example/`, the test fixtures, and an assertion in the config tests.

### OP-2-3 How a runtime gets its config

| Runtime (OP-1) | Config from |
| :--- | :--- |
| `local` | `config/*.json5` |
| `agentcore_local`, `agentcore` | the SSM parameter named by `CONFIG_SSM_PARAM_NAME` (an `envVars` entry), written by `config-deploy-<env>` |
| `ci` | none: `NotImplementedError` (deploys run from a developer's machine) |

Why SSM and not `envVars` or a copy in the zip: secrets would sit in plain text on the runtime or in the CodeZip. Cost: one `GetParameter` per process, so one per session.

---

## OP-3 MCP Runtime

An MCP server is a set of tools, and a tool is a function. Following section 2, the function is written and tested on its own, the MCP server is a thin layer that registers it, and the whole runs locally before anything AgentCore is involved. Deploying it is OP-5 and OP-6.

- EP: `<package_name>/runtimes/<runtime_name>.py`, or `<package_name>/runtimes/<runtime_name>/main.py` when it grows
- FP: `<package_name>/<domain>/**`, the runtime module, `<package_name>/runtimes/common.py`, `<package_name>/devtools/**`, `tests/<domain>/**`, `tests/runtimes/**`, `tests/devtools/**`
- CMD: per layer (see the reference); `mise run cov`; `mise run ac-local-<slug>`, then `mise run ac-local-<slug>-call`
- Docs: `30-mcp-runtime.md`

### OP-3-1 Layer 1: the tool functions

- Put them wherever the business fits: a `<domain>` subpackage, named after the business. The template does not fix the place.
- Each takes its dependencies (an engine, a client) as arguments and returns a contract model: Pydantic, `Field(description=...)` on every field (the LLM reads them as the output schema), `from_attributes=True` to build it from an ORM row. Storage models and contract models are separate.
- The first paragraph of the docstring is the tool description the LLM reads: write it for the LLM, never mention the injected dependency.
- Errors are `ValueError` with a clear message.
- The import rule (OP-5-3): only the standard library and the `agentcore` dependency group at module level; no `one`, no config, no MCP.
- Tests: `tests/<domain>/`, with their own local dependencies (such as an in-memory database).

### OP-3-2 Layer 2: the MCP server

A runtime module, always under `<package_name>/runtimes/`: `<runtime_name>.py` when small, `<runtime_name>/main.py` (a subpackage) when not. Either way it has a `main()`.

- One FastMCP server from `new_mcp_server(name)` of the shared `runtimes/common.py`: `host="0.0.0.0"`, port from `FASTMCP_PORT` (default 8000), `stateless_http=True`, path `/mcp`, served over `streamable-http` by `run_mcp_server`: the AgentCore MCP contract, which works locally too.
- One thin wrapper per tool: `@mcp.tool()`, the function's docstring copied by `doc_from` (`functools.wraps` would not do: it would expose the injected parameter), the dependency injected from `one` (such as `one.engine`), the contract model as the return type.
- The dependencies are `one` properties built once per process (section 2).
- `main()`: load the config and the dependencies, print where they came from (`print_config_source`, `flush=True`), then run. A runtime that cannot start fails here, before taking traffic.

### OP-3-3 Run it locally

- `mise run ac-local-<slug>` (generated from the registry; `devtools/local_run.py`): frees the runtime's `local_port` (`free_port` of `devtools/local_port.py`, only this repo's leftover servers), then `FASTMCP_PORT=<port> python -m <package_name>.runtimes.<runtime_name>`. Runtime `local`, config from the files.
- Every runtime has its own unusual local port in the registry (18731, 18732, ...), below the ephemeral range, so a listener there is almost surely ours. Deployed runtimes always use AgentCore's 8000 (MCP) and 8080 (HTTP).

### OP-3-4 Test it locally

- Unit: layer 1 (OP-3-1).
- Server: `tests/runtimes/test_runtimes_<runtime_name>.py`: the tool list, description = docstring, no injected parameter in the input schema, an output schema, one call per tool, `main()` with `mcp.run` stubbed.
- By hand: `mise run ac-local-<slug>-call` lists the tools and calls one with the runtime's sample arguments, through the tested MCP client `<package_name>/devtools/mcp_client.py` (OP-8-1 adds SigV4 to call a deployed one).

---

## OP-4 Agent Runtime

An agent is a prompt, a model, its own tools, and the MCP servers it uses. Following section 2, everything but the framework is plain Python; the Strands agent is a thin layer; the whole runs locally against a local MCP server. Deploying it is OP-5 and OP-6.

- EP: `<package_name>/runtimes/<runtime_name>.py`, or `<package_name>/runtimes/<runtime_name>/main.py`
- FP: `<package_name>/<domain>/<agent_name>.py` and its tool functions, the runtime module, `<package_name>/runtimes/{common,mcp_connection}.py`, `one.new_boto_ses`, `<package_name>/devtools/agent_client.py`, `tests/<domain>/**`, `tests/runtimes/**`, `tests/devtools/**`
- CMD: per layer (see the reference); `mise run cov`; `mise run ac-local-<mcp slug>`, `ac-local-<slug>`, then `ac-local-<slug>-call` (calls Bedrock: say so first)
- Docs: `40-agent-runtime.md`

### OP-4-1 Layer 1: what the agent is, in plain Python

`<package_name>/<domain>/<agent_name>.py`, no `strands` import: `<Agent>Request` and `<Agent>Response`, the payload contract as Pydantic models; `SYSTEM_PROMPT`; and `TOOLS`, its own tool functions (pure, typed, a docstring for the LLM, a contract model, exactly as OP-3-1). The model ID is a config field (OP-2-2), not a constant.

### OP-4-2 Layer 2: the Strands agent

- `make_agent(model_id, boto_session, mcp_url, mcp_auth)` builds the `Agent` from its arguments only: `BedrockModel`, the prompt, `TOOLS` wrapped with `strands.tool`, one `MCPClient` per MCP server.
- `build_agent()` gives it the dependencies of the process: `one.new_boto_ses()` (a new session, credentials resolved on the first invocation, never at import time), the model ID of the config, the MCP connection.
- `agent = ProcessAgent(build_agent)` (`runtimes/common.py`): one agent per process, so per session; its MCP session stays open and the conversation is remembered; one call at a time; dropped after a failure.
- `BedrockAgentCoreApp` with `@app.entrypoint invoke(payload)`: the AgentCore HTTP contract. It validates the payload against the request model (a 400 with pydantic's errors when it does not validate), and `strip_thinking` cleans the answer.
- Where its MCP servers are (`runtimes/mcp_connection.py`, `get_mcp_connection(<Mcp>, boto_session)`): `MCP_URL_<MCP NAME>` if set, else the ARN in `get_runtime_arn_env_var(<Mcp>)` (set by `bind()`, OP-5-1) turned into the invocation URL and signed with `AwsSigV4Auth` (`get_deployed_mcp_connection`), else a `ValueError` that names the missing `bind()` line.
- `main()`: `print_config_source()`, then `app.run()`.

### OP-4-3 Run and test it locally

- `mise run ac-local-<slug>`: frees its port, then uvicorn serves `<package_name>.runtimes.<runtime_name>:app` with one `MCP_URL_<NAME>` per MCP runtime of its `mcp_runtimes`, pointing at their local ports; the model is called with the environment's profile and region through `one.new_boto_ses`. Start the MCP server first (OP-3-3).
- Tests: the agent loads every tool against a real local MCP server, without a model call; `ProcessAgent` with fake agents; `invoke`; `main()`.
- By hand: `mise run ac-local-<slug>-call` sends a sample prompt through the tested client `<package_name>/devtools/agent_client.py` (optionally with `--session-id`).

---

## OP-5 AgentCore Runtime

The bridge from the code of OP-3 and OP-4 to AgentCore: one AgentCore CLI project for all runtimes, generated from the config and the package, built, and run locally by the CLI itself.

- EP: `<package_name>/agentcore_project/gen.py` (via `.mise/tasks/ac-gen.py`)
- FP: `<package_name>/agentcore_project/{registry,project_files,gen,codezip}.py`, the AgentCore paths of `<package_name>/paths.py`, `agentcore/cdk/**`, `[dependency-groups] agentcore` in `pyproject.toml`, `uv.lock`, `tests/agentcore_project/**`
- CMD: `mise run ac-gen`, `ac-check-wheels`, `ac-build`, `ac-dev-<slug>`
- Docs: `50-agentcore-project-layout.md`, `51-agentcore-config.md`, `52-agentcore-packaging.md`, `53-agentcore-dev.md`, one per layer

### OP-5-1 Layer 1: the files

| Path | What | Source or generated | In git |
| :--- | :--- | :--- | :--- |
| `agentcore/agentcore.json` | the runtimes, their `envVars`, `additionalPolicies` | generated (OP-5-2) | no |
| `agentcore/aws-targets.json` | the one target of the environment | generated (OP-5-2) | no |
| `app/<Runtime>/` | `main.py` shim, pinned `pyproject.toml`, package copy | generated (OP-5-3) | no |
| `agentcore/cdk/` | the CLI's CDK app (TypeScript), written once by `agentcore create` | source, kept close to the CLI's template (OP-9-1) | yes, without `node_modules/`, `cdk.out/`, `dist/` |
| `agentcore/cdk/lib/cdk-stack.ts` | only AgentCore wiring: one `bind()` per agent-to-MCP pair, inside `if (runtimes.size > 0)` | source | yes |
| `agentcore/.cli/deployed-state.json` | the CLI's record of deployed targets | written by the CLI | yes |

The rule: AgentCore resources live in this project; anything else the runtimes use (policies, databases, buckets, VPCs) lives in a Python CDK stack and is referred to by name from `agentcore.json` (OP-6-1). All runtimes are deployed together; there is no per-runtime deploy.

### OP-5-2 Layer 2: the AgentCore config, from the project config

- The **runtime registry** `get_runtime_specs(config)` in `agentcore_project/registry.py` is the one place a runtime is declared: name, module, protocol (`RuntimeProtocolEnum.MCP` or `HTTP`). Everything per runtime is derived from it: `agentcore.json`, `app/<Runtime>/`, and its generated tasks with their slug, local port, and sample call (OP-9-4).
- `build_agentcore_json` (`agentcore_project/project_files.py`): per runtime `CodeZip`, `main.py`, `app/<Runtime>`, Python version, protocol, the `envVars` of OP-1-2 and OP-2-3 (`IS_AGENTCORE_RUNTIME`, `ENV_NAME`, `CONFIG_SSM_PARAM_NAME`), `additionalPolicies` from the config.
- `build_aws_targets_json`: one target named after the environment, account and region from the config.
- `build_empty_agentcore_json`: a project that declares nothing, for teardown (OP-7-1).
- `write_json` writes only when the content changed.

### OP-5-3 Layer 3: package and build

- `assemble_runtime_dir` (`agentcore_project/codezip.py`) writes into `app/<Runtime>/`, leaving the rest alone (the `.venv` of `agentcore dev`):
  - `main.py`: a shim that imports `main` (and `app` for `HTTP`, because `agentcore dev` serves an HTTP runtime with `uvicorn main:app`).
  - `pyproject.toml`: the `agentcore` dependency group, every version pinned from `uv.lock` (`uv export`), because the CLI ignores `uv.lock`.
  - a copy of the modules and subpackages the runtimes need; never the dev tooling.
- **The import rule**: copied code imports at module level only the standard library, the `agentcore` group, and other copied code; dev-only imports go inside the function that needs them. A test imports the assembled runtimes where the dev-only packages raise `ImportError`.
- `mise run ac-check-wheels` (`check_codezip_installs`): installs each runtime's dependencies as the CLI does, wheels only, Linux aarch64, as a dry run, and keeps uv's own error.
- `mise run ac-build`: `agentcore build`, CodeZips and the synthesized stack, no AWS call.

### OP-5-4 Layer 4: run it with the AgentCore CLI locally

Different from OP-3-3 and OP-4-3: this runs the **packaged** copy, as close to deployed as it gets on a dev machine.

- `mise run ac-dev-<slug>`: frees the port, then `AWS_REGION=<config region> agentcore dev --agent <Runtime> --port <local port> --no-traces`. Always an explicit `--port`: without it the CLI silently moves to the next free port.
- Runtime `agentcore_local` (OP-1-2): config from SSM, so `config-deploy-<env>` must have run (asks first); credentials from the local profile.
- Python env: `app/<Runtime>/.venv`, made by the CLI from the generated `pyproject.toml`. An HTTP runtime reloads when `ac-gen` rewrites the copy.
- The same ports as OP-3-3 and OP-4-3, so local and packaged servers mix, and the same `-call` tasks reach them.
- What it still cannot show: cold starts, SigV4 between runtimes, the execution role, the CodeZip install on aarch64 (use `ac-check-wheels`). Those need OP-6.

---

## OP-6 Deploy

Put an environment's AgentCore part into AWS, in dependency order, then prove it works there. **Every step asks first.**

- EP: `<package_name>/agentcore_project/mise_tasks.py`, which renders the AgentCore tasks of every environment
- FP: `<package_name>/cdk/stacks/agentcore_deps_stack.py`, `<package_name>/one/one_04_agentcore_deps.py` (the check before deploy), `<package_name>/agentcore_project/mise_tasks.py`, `sample_payload` of the registry, `.mise/tasks/{ac-check-deps,ac-gen,ac-check-wheels}.py`, the `<env-tasks>` block of `mise.toml`, `agentcore/.cli/deployed-state.json`; the config step is OP-2's
- CMD: `mise run ac-chain-up-<env>`, or a single step; `mise run ac-test-<env>`; free: `mise run -n <task>`, `cdk-plan-<env>-agentcore-deps-stack`, `gen-env-tasks`
- Docs: `60-deploy.md`

### OP-6-1 What the runtimes depend on

The `agentcore_deps` CDK stack: the managed policy attached to every execution role through `additionalPolicies` (read the config parameter, plus what the tools need), later databases, buckets, VPCs; names from the config. `additionalPolicies`, not `executionRoleArn`, so `bind()` can still add its grant to the CLI-created role.

### OP-6-2 The chain

| # | Step | Does | Run alone when |
| :--- | :--- | :--- | :--- |
| 1 | `config-deploy-<env>` | the config to SSM, only if it changed | only the config changed (a new session reads it) |
| 2 | `cdk-up-<env>-agentcore-deps-stack` | the stack of OP-6-1 | only a permission or resource changed |
| 3 | `ac-deploy-<env>` | the runtimes (OP-6-3) | only code changed |

`ac-chain-up-<env>` prints the chain, then runs the steps in order, each printing `>>> <task>: <what it does>`, and stops at the first failure.

### OP-6-3 `ac-deploy-<env>`

1. Check what it depends on (`check_agentcore_deps`: the policy and the config parameter exist), else print the task to run.
2. `ac-gen` for `<env>`.
3. `ac-check-wheels`.
4. `agentcore deploy --target <env>` with the environment's profile: the CLI checks the account, synthesizes, packages, deploys.
5. Print the reminder to commit `agentcore/.cli/deployed-state.json`.

### OP-6-4 Test it in the cloud

- `mise run ac-status-<env>`: `agentcore status`, what is deployed.
- `mise run ac-invoke-<env>-<slug>`: `agentcore invoke` of one deployed runtime with the `sample_payload` of its registry entry (a JSON-RPC request for an MCP runtime); `SESSION_ID` adds `--session-id`.
- `mise run ac-test-<env>`: the status, then every runtime invoked once.
- Without the CLI, from Python: OP-8.
- A healthy start logs the config source line of `main()` (OP-3-2, OP-4-2).

---

## OP-7 Teardown

Take an environment's AgentCore part out of AWS: the deploy chain in reverse. **Asks first**, with `<package_name>/confirm.py`: only `y` / `yes` goes on; a bare Enter, anything else, or no terminal stops; `CONFIRM_YES=true` answers yes (CI). Never mise's `confirm`, which takes a bare Enter as yes.

- EP: `mise run ac-chain-down-<env>`, rendered by `<package_name>/agentcore_project/mise_tasks.py` (as OP-6)
- FP: `<package_name>/confirm.py`, `<package_name>/agentcore_project/gen.py` (`generate_teardown`), the `ac_down` step of `mise_tasks.py`, `.mise/tasks/{confirm,ac-gen-teardown,config-delete}.py`, `tests/test_confirm.py`
- CMD: `mise run ac-chain-down-<env>`, or a single step; `mise run ac-status-<env>` afterwards
- Docs: `70-teardown.md`

### OP-7-1 `ac-down-<env>`: the runtimes

The CLI's own teardown: `agentcore deploy --yes` of a project that declares nothing destroys the target's stack and removes the target from `deployed-state.json`. Since `agentcore.json` is generated, the task writes the empty one (`ac-gen-teardown`), sets `trap '<ac-gen>' EXIT`, and deploys it: the real project comes back when the task ends, failed or not. `bind()` sits inside `if (runtimes.size > 0)` so the empty project still synthesizes.

### OP-7-2 The chain

| # | Step | Does |
| :--- | :--- | :--- |
| 1 | `ac-down-<env>` | every runtime of `<env>` |
| 2 | `cdk-down-<env>-agentcore-deps-stack` | the stack of OP-6-1, once no role uses its policy |
| 3 | `config-delete-<env>` | the config parameter |

`ac-chain-down-<env>` asks once and sets `CONFIRMED_BY_CHAIN=true`, so its steps do not ask again; run alone, `ac-down-<env>` and `config-delete-<env>` ask on their own.

### OP-7-3 After a teardown

`ac-status-<env>` shows nothing deployed; commit the changed `deployed-state.json`; check for what neither stack owns, such as the runtimes' log groups.

---

## OP-8 Invoke and Observe

Call the deployed runtimes from a client program, keep the conversation and the microVMs warm, and find out what happened.

- EP: `<package_name>/devtools/agentcore_client.py`: find a runtime's ARN, `InvokeAgentRuntime` with a session ID, the log group
- FP: `<package_name>/devtools/{agentcore_client,mcp_client,quick_links}.py`, `get_deployed_mcp_connection` of `runtimes/mcp_connection.py` (OP-4-2), the AgentCore clients of `one/one_02_boto_ses.py`, the console URL helpers of `config_01_name.py`, the `ac-logs` step of `agentcore_project/mise_tasks.py`, `QUICK_LINKS.md`, `tests_int/test_agentcore_runtimes.py`
- CMD: `mise run int-test` (needs a deploy), `mise run gen-quick-links` (reads AWS), `mise run ac-logs-<env>-<slug>`, `mise run ac-invoke-<env>-<slug>`
- Docs: `80-invoke-and-observe.md`

### OP-8-1 Call a runtime from a client

One client per protocol, each taking a URL (or an ARN) and an auth, so the same code calls a local server and a deployed runtime:

| Protocol | Local | Deployed |
| :--- | :--- | :--- |
| `HTTP` (agent) | `POST http://localhost:<port>/invocations` | `InvokeAgentRuntime` (boto3 `bedrock-agentcore`, or `agentcore invoke`) with a `runtimeSessionId` |
| `MCP` | streamable HTTP client to `http://localhost:<port>/mcp` | the same client to the invocation URL of the ARN, signed with SigV4 (`get_deployed_mcp_connection` of OP-4-2) |

### OP-8-2 Sessions

- One session, one microVM: a new session ID is a cold start, the same one goes back to the warm microVM until the idle timeout (default 15 min) or the max lifetime (default 8 h).
- The caller makes one `runtimeSessionId` per conversation (at least 33 characters, never shared between users) and sends it with every message: `--session-id` for `agentcore invoke`, `SESSION_ID` for `ac-invoke-<env>-<slug>`.
- For MCP the platform picks the `Mcp-Session-Id` and the client sends it back; an agent keeps one MCP session per agent session by keeping one agent per process (OP-4-2).
- Keep the MCP runtime's idle timeout at least the agent's.

### OP-8-3 Logs and debugging

- Log group `/aws/bedrock-agentcore/runtimes/<runtime ID>-DEFAULT`, one stream per session: a new stream per call means a new (cold) session. The runtime ID is known only after a deploy: `agentcore status`, the stack's console URL, or `describe-log-groups` by the physical-name prefix.
- `ac-logs-<env>-<slug>`: `agentcore logs runtime`, the recent logs of one runtime (read-only).
- Latency: the T1–T5 breakdown of `80`, section 3; time the same prompt three times with one session ID.
- Failures met so far, with fixes: `80`, section 6 (invocation) and `60`, section 7 (deploy). Add every new one.

---

## OP-9 Maintain

Keep the toolchain current and the project consistent over its life.

- EP: `.claude/skills/aws-agentcore-base/scripts/check_cdk_layout.py`; `<package_name>/agentcore_project/registry.py`
- FP: `mise.toml` `[tools]`, `agentcore/cdk/package.json` and `package-lock.json`, the constants that depend on CLI behavior, the registry, the `aws-agentcore-*` skills
- CMD: `mise run ac-check-layout`, `mise run gen-env-tasks`, then the CMDs of OP-3 to OP-5
- Docs: `90-maintain.md`, this file

### OP-9-1 Upgrade the AgentCore CLI

Bump `"npm:@aws/agentcore"` in `mise.toml` and `@aws/agentcore-cdk` in `agentcore/cdk/` together; `mise run ac-check-layout` compares `agentcore/cdk/` with a fresh `agentcore create` (the `bind()` lines are the only allowed extra); `npm install`; re-check OP-9-2; `cov`, `ac-build`, an `ac-dev-*` run; deploy dev (asks first).

### OP-9-2 The undocumented behaviors

The table of `90-maintain.md`, section 2: each behavior this repo relies on (such as `LOCAL_DEV` of OP-1-2, the CodeZip platforms of OP-5-3, `bind()`'s env var name, the empty-project teardown of OP-7-1, the raw JSON-RPC payload of `agentcore invoke`), the code that relies on it, and where to look in the CLI's source.

### OP-9-3 The runtime dependencies

The `agentcore` dependency group is what every runtime installs: keep it small (zip size is start time), and every version must have a Linux aarch64 wheel (`ac-check-wheels`); constrain a version without one out, with a comment. How to upgrade is `pywf-oss-upgrade-deps`.

### OP-9-4 Runtimes and environments over time

- Add a runtime: the invokers (section 1); the registry entry is `get_runtime_specs(config)`. Rename or remove one: its registry entry, its names in the config, its `bind()` lines and other agents' `mcp_runtimes`, then `gen-env-tasks` and `ac-gen`; the next deploy replaces or drops it.
- Add an environment: `EnvNameEnum` (owned by `pywf-aws-cdk-base`), its config files, `mise run gen-env-tasks`.
- `gen-env-tasks` renders the per-environment tasks (OP-6, OP-7, OP-8) and the per-runtime tasks (`ac-local-<slug>`, `ac-local-<slug>-call`, `ac-dev-<slug>`, `ac-invoke-<env>-<slug>`, `ac-logs-<env>-<slug>`) from `EnvNameEnum` and the registry (`local_port`, `sample_payload`, `mcp_runtimes`); no per-runtime task is hand-written.

### OP-9-5 Keep the docs in step

A change that breaks this design changes this file in the same change. A fact a reference states that turns out wrong is fixed in the reference. The invokers' read lists stay in step with the base `SKILL.md`.

---

## 10. The references

One per OP, numbered `<OP><part>` so the file order is the OP order. Each opens with "Implements OP-N" and its EP, FP, CMD, and cites only lower numbers.

| Reference | OP |
| :--- | :--- |
| `00-agentcore-docs-mcp.md` | every OP (a habit) |
| `10-code-runtime.md` | OP-1 |
| `20-centralized-config.md` | OP-2 |
| `30-mcp-runtime.md` | OP-3 |
| `40-agent-runtime.md` | OP-4 |
| `50-agentcore-project-layout.md`, `51-agentcore-config.md`, `52-agentcore-packaging.md`, `53-agentcore-dev.md` | OP-5, one per layer |
| `60-deploy.md` | OP-6 |
| `70-teardown.md` | OP-7 |
| `80-invoke-and-observe.md` | OP-8 |
| `90-maintain.md` | OP-9 |
| `99-ood.md` | the design |
