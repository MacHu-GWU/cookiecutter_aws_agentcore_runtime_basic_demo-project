---
description: "OP-6 Deploy: putting an environment's AgentCore part into AWS and testing it there: the agentcore_deps stack of what the runtimes use (and how to give them a permission or a resource), the deploy chain (config, agentcore_deps, runtimes), what ac-deploy-<env> does, testing the deployed runtimes with ac-status, ac-invoke-<env>-<slug>, and ac-test-<env>, deployed-state.json, the generated tasks, and the deploy failures met so far. Read before deploying, before giving a runtime a permission or a resource, after a deploy fails, or to check a deployed environment."
---

# Deploy

Implements **OP-6**. **Every deploy step changes AWS: run it only after the user's yes, one environment per yes.**

| | |
| :--- | :--- |
| EP | `<package_name>/agentcore_project/mise_tasks.py` (generates the tasks); `mise run ac-chain-up-<env>` |
| FP | `<package_name>/cdk/stacks/agentcore_deps_stack.py`, `<package_name>/one/one_04_agentcore_deps.py`, `<package_name>/agentcore_project/mise_tasks.py`, `sample_payload` of the registry, `.mise/tasks/{ac-check-deps,ac-gen,ac-check-wheels}.py`, the `<env-tasks>` block of `mise.toml`, `agentcore/.cli/deployed-state.json`, their tests |
| CMD | changes AWS: `mise run ac-chain-up-<env>`, or one step; tests the deployed runtimes: `mise run ac-test-<env>`; free: `mise run gen-env-tasks`, `mise run -n <task>` (prints what a task would run), `cdk-plan-<env>-agentcore-deps-stack`, `ac-build` |

---

## 1. What the runtimes depend on: the `agentcore_deps` stack

The AgentCore project holds only AgentCore resources (`50-agentcore-project-layout.md`, section 5). Everything else the runtimes use is in the Python CDK stack `agentcore_deps` (`<package_name>/cdk/stacks/agentcore_deps_stack.py`, an entry of `StackCtxEnum` / `StackEnum`); the CDK mechanics are in the `pywf-aws-cdk-base` skill.

Today it holds one managed policy, `iam_policy_name_agentcore_runtime`, attached to every runtime's execution role through `additionalPolicies` of `agentcore.json` (`51-agentcore-config.md`). It allows `ssm:GetParameter` on the config parameter; the `aws/ssm` key needs no grant through SSM.

**Giving the runtimes a new permission:**

1. A `PolicyStatement` in `s01_create_runtime_policy`, with resource names or ARNs from the config.
2. Assert it in `tests/cdk/stacks/test_cdk_stacks_agentcore_deps_stack.py`.
3. `mise run cdk-up-<env>-agentcore-deps-stack` (the user's yes). No AgentCore deploy is needed: the policy is already attached, and new sessions use it.

The CLI-created role already carries logs, X-Ray, Bedrock model access, workload identity, and the `bind()` grants. If two runtimes need different permissions, add a second policy with its own names in `config_01_name.py`, and give each runtime its own `additionalPolicies`.

**A new resource** (a table, a bucket, a secret): a new `s0N_...` method of the stack, its name in the config, its permission in the policy; its name reaches the runtime through the config, or through `envVars` only if the runtime cannot read it from there.

---

## 2. The deploy chain

The AgentCore stack refers to what `agentcore_deps` creates, and the runtimes read the config at startup, so the order is fixed:

| # | Step task | Does | Run alone when |
| :--- | :--- | :--- | :--- |
| 1 | `config-deploy-<env>` | the config to SSM, only if it changed (`20-centralized-config.md`) | only the config changed: new sessions read it |
| 2 | `cdk-up-<env>-agentcore-deps-stack` | the stack of section 1 | only a permission or a resource changed |
| 3 | `ac-deploy-<env>` | the runtimes (section 3) | only runtime code or `agentcore.json` changed |

```bash
mise run ac-chain-up-<env>
```

A chain prints all its steps first; each step prints `>>> <task>: <what it does>` before its own output, so the log reads as the list of steps. It stops at the first step that fails. The CDK bootstrap stack (`CDKToolkit`) must exist in the account and region.

---

## 3. `ac-deploy-<env>`

With `ENV_NAME=<env>`; each command stops the task when it fails:

1. The banner, then the AgentCore stack's console URL.
2. `ac-check-deps.py`: `one.check_agentcore_deps()` (`one/one_04_agentcore_deps.py`) checks the `agentcore_deps` policy and the config parameter exist, and prints the task to run for each that does not.
3. `ac-gen.py`: the project files and `app/` for `<env>` (`51-agentcore-config.md`).
4. `ac-check-wheels.py`: every runtime's dependencies install as the CLI installs them (`52-agentcore-packaging.md`).
5. `AWS_PROFILE=<profile of env> agentcore deploy --target <env>`: the CLI checks the profile's account is the target's, synthesizes `agentcore/cdk`, packages the CodeZips, deploys the stack.
6. A reminder to commit `agentcore/.cli/deployed-state.json` (section 5).

It does not deploy the config: that is step 1 of the chain. A running session keeps the code it started with; a deploy reaches new sessions only.

---

## 4. Testing the deployed runtimes

Generated per environment, from the registry; they read AWS and call the runtimes (an agent calls its model), but change nothing:

| Task | Does |
| :--- | :--- |
| `ac-status-<env>` | `agentcore status --target <env>`: the deployed resources of the target, as the CLI reports them |
| `ac-invoke-<env>-<slug>` | `agentcore invoke --target <env> --runtime <Runtime>` with the runtime's `sample_payload` (`51-agentcore-config.md`); `SESSION_ID=<id>` adds `--session-id` |
| `ac-test-<env>` | the chain: `ac-status-<env>`, then every `ac-invoke-<env>-<slug>` |

```bash
mise run ac-test-<env>
```

- **An agent** gets `{"prompt": ...}` and answers `{"result": ...}`.
- **An MCP runtime** gets a whole JSON-RPC request as the payload (such as `{"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "<tool>", "arguments": {...}}}`), and the task also passes `--mcp-method` and `--mcp-name`. The answer is a server-sent event with the JSON-RPC result. The server is stateless, so a `tools/call` needs no `initialize` first.
- The task puts the payload in a shell variable, so it is printed and run without nested quotes; a payload cannot contain a single quote (the generator refuses it).
- A healthy start logs the config source line of `main()`; a failing call is in the runtime's log (the invoke and observe OP).

---

## 5. `deployed-state.json` stays in git

`agentcore/.cli/deployed-state.json` records each deployed target's stack. The `.gitignore` of a fresh `agentcore create` commits it on purpose, so everyone who deploys shares it: commit it after every deploy or teardown that changes it. With several deployers, give each environment one deployer (in the end, CI), so two people never write it for the same target at once.

---

After a deploy that creates or replaces a runtime, `mise run gen-quick-links` refreshes the console links of `QUICK_LINKS.md` (it reads AWS).

---

## 6. The generated tasks

`mise run gen-env-tasks` rewrites the `<env-tasks>` block of `mise.toml`; never edit it by hand. `<package_name>/agentcore_project/mise_tasks.py` renders the AgentCore part of each environment (`config-*`, `ac-deploy`, `ac-down`, `ac-status`, `ac-invoke-*`, the `ac-chain-*` and `ac-test` chains), and passes it to `render_env_tasks_block` of `<package_name>/cdk/mise_tasks.py`, which adds the `cdk-*` tasks and knows nothing of AgentCore.

Run it after changing the registry (a runtime, its sample payload), an environment, or a stack. `test_mise_toml_is_up_to_date` fails until it is run.

---

## 7. Deploy failures met so far

| Symptom | Cause | Fix |
| :--- | :--- | :--- |
| `The policy ... does not exist` from `ac-deploy` | `agentcore_deps` not deployed | `mise run cdk-up-<env>-agentcore-deps-stack` |
| `The config parameter ... does not exist` from `ac-deploy` | the config was never deployed | `mise run config-deploy-<env>` |
| `uv install failed for all platform candidates` at synth | a dependency version without a Linux aarch64 wheel | `mise run ac-check-wheels` names it; exclude the version (`52-agentcore-packaging.md`) |
| `Deployment target '<env>' expects AWS account ...` | the profile signs in to another account than the target's | point `AWS_PROFILE_FOR_<ENV>` in `.env` at the config's account; run through mise (a shell without mise does not load `.env`) |
| `CDK dependencies are missing` | `agentcore/cdk/node_modules` absent (a fresh clone) | `npm install` in `agentcore/cdk` |
| `Unknown runtime "<Name>" in project` at synth | a `runtime('<Name>')` in `cdk-stack.ts` that `agentcore.json` does not declare | run `ac-gen`; keep `bind()` inside `if (this.application.runtimes.size > 0)` |
| a deploy does not change a running session | a microVM keeps the code it started with | a new session gets the new code |

---

## 8. Tests

| Test file | Covers |
| :--- | :--- |
| `tests/cdk/stacks/test_cdk_stacks_agentcore_deps_stack.py` | the policy, by name, reads only the config parameter |
| `tests/one/test_one_one_04_agentcore_deps.py` | the check, against `moto`: neither, one, both exist |
| `tests/agentcore_project/test_agentcore_project_mise_tasks.py` | `mise.toml` is up to date; the order of the chains; who asks yes/no; the banners; the deploy reminder; `ac-test`, the invoke commands, the payload quoting |
| `tests/cdk/test_cdk_mise_tasks.py` | the cdk tasks, with the extra and tail tasks placed |

```bash
.venv/bin/python tests/agentcore_project/test_agentcore_project_mise_tasks.py
.venv/bin/python tests/one/test_one_one_04_agentcore_deps.py
.venv/bin/python tests/cdk/stacks/test_cdk_stacks_agentcore_deps_stack.py
```
