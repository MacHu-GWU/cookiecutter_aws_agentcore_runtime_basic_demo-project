---
description: "OP-7 Teardown: taking an environment's AgentCore part out of AWS: the teardown chain (runtimes, agentcore_deps stack, config), how ac-down-<env> destroys the runtimes with the CLI's own teardown and always restores the generated project, the yes/no question every destroying task asks (confirm.py, never mise's confirm), CONFIRM_YES and CONFIRMED_BY_CHAIN, and what to check afterwards. Read before tearing down an environment or any of its AgentCore parts, or when a teardown fails half way."
---

# Teardown

Implements **OP-7**: the deploy chain of `60-deploy.md` in reverse. **Every step destroys something in AWS: run it only after the user's yes, one environment per yes.** The tasks ask too.

| | |
| :--- | :--- |
| EP | `mise run ac-chain-down-<env>` |
| FP | `<package_name>/confirm.py`, `.mise/tasks/confirm.py`, `generate_teardown` / `main_teardown` of `<package_name>/agentcore_project/gen.py`, `build_empty_agentcore_json` of `project_files.py`, `.mise/tasks/ac-gen-teardown.py`, `.mise/tasks/config-delete.py`, the `ac_down` step and the teardown chain of `<package_name>/agentcore_project/mise_tasks.py`, the `if` around `bind()` in `cdk-stack.ts`, their tests |
| CMD | destroys: `mise run ac-chain-down-<env>`, or one step; checks: `mise run ac-status-<env>`; free: `mise run -n <task>` |

---

## 1. The teardown chain

| # | Step task | Destroys | Why in this order |
| :--- | :--- | :--- | :--- |
| 1 | `ac-down-<env>` | the AgentCore stack: every runtime of `<env>`, their execution roles, endpoints | the roles use the policy of step 2 |
| 2 | `cdk-down-<env>-agentcore-deps-stack` | the `agentcore_deps` stack: the runtime policy, and any resource added there | a managed policy cannot be deleted while a role uses it |
| 3 | `config-delete-<env>` | the config parameter (`20-centralized-config.md`) | nothing else deletes it; nothing reads it any more |

```bash
mise run ac-chain-down-<env>
```

The chain prints its steps, asks yes or no once, then runs them, and stops at the first that fails. Run one step alone to take out only that part: such as `ac-down-<env>` to stop paying for the runtimes but keep the policy and the config for the next deploy.

---

## 2. Asking yes or no

`<package_name>/confirm.py`, run as `.venv/bin/python .mise/tasks/confirm.py --action '<question>' [--skip_var <VAR> ...]`, the first command of every destroying task that is not a `cdk-*` one:

- **Only `y` or `yes`** (any case, spaces ignored) goes on. A bare Enter, anything else, or no terminal (`EOFError`, such as in CI) stops the task with exit code 1.
- **Never mise's own `confirm`**: it takes a bare Enter as yes, which once destroyed dev.
- The question is printed as whole lines, flushed, so mise shows it at once and the task needs no `raw = true`.
- **`CONFIRM_YES=true`** answers yes without asking, such as in CI.
- **`CONFIRMED_BY_CHAIN=true`** is set by `ac-chain-down-<env>` after its own question, so its steps do not ask again; run alone, `ac-down-<env>` and `config-delete-<env>` ask (they pass both variables as `--skip_var`, the chain's question passes only `CONFIRM_YES`).
- `cdk-down-<env>-*` is a plain `cdk destroy --force` (the `pywf-aws-cdk-base` skill): it does not ask, so it is only run by the user, or inside the chain after its question.

---

## 3. `ac-down-<env>`: the CLI's own teardown

The AgentCore CLI destroys a target's stack when it deploys a project that declares nothing: `agentcore deploy --target <env> --yes` of an empty project destroys the stack and removes the target from `agentcore/.cli/deployed-state.json`. `agentcore.json` is generated here, so instead of `agentcore remove all` the task:

1. Asks yes or no (section 2), then prints the AgentCore stack's console URL.
2. `ac-gen-teardown.py`: `generate_teardown(config)` writes the empty `agentcore.json` (`build_empty_agentcore_json`, the shape of `agentcore create`) and the target of `<env>`; `app/` is left alone.
3. `trap '<ac-gen>' EXIT`: from here on, the real project is generated again when the task ends, **whether the deploy succeeds or fails**, so the empty `agentcore.json` never outlives the task.
4. `AWS_PROFILE=<profile of env> agentcore deploy --target <env> --yes`.
5. The reminder to commit `deployed-state.json` (`60-deploy.md`, section 5).

The empty project still synthesizes because `cdk-stack.ts` calls `bind()` only `if (this.application.runtimes.size > 0)` (`50-agentcore-project-layout.md`, section 4).

---

## 4. Afterwards

- `mise run ac-status-<env>` should show nothing deployed for the target.
- Commit the changed `agentcore/.cli/deployed-state.json`, and refresh `QUICK_LINKS.md` with `mise run gen-quick-links`.
- What neither stack owns is not removed by the chain, such as the CDK bootstrap stack `CDKToolkit`, and anything the runtimes created at run time. Check the runtimes' log groups (read-only) with `aws logs describe-log-groups --log-group-name-prefix /aws/bedrock-agentcore/runtimes/<physical name>`, and delete them yourself if they should go.
- To come back: `mise run ac-chain-up-<env>` (`60-deploy.md`).

**A failed step:** fix the cause and run the chain again, or only the steps left; each step is safe to repeat (`config-delete-<env>` treats a missing parameter as done). A failing `cdk-down-<env>-agentcore-deps-stack` usually means a role still uses the policy: run `ac-down-<env>` first.

---

## 5. Tests

| Test file | Covers |
| :--- | :--- |
| `tests/test_confirm.py` | which answers mean yes; no terminal; `--skip_var`; the exit codes of `main` |
| `tests/agentcore_project/test_agentcore_project_mise_tasks.py` | the chain's order; who asks and with which skip variables; the `trap` set after the empty project and before the deploy; the reminder |
| `tests/agentcore_project/test_agentcore_project_gen.py` | `main_teardown()`: an empty project and the target, `app/` untouched |
| `tests/agentcore_project/test_agentcore_project_project_files.py` | the empty project's shape; the `if` around `bind()` in `cdk-stack.ts` |
| `tests/one/test_one_one_06_config_deploy.py` | deleting the config, and a missing one |

```bash
.venv/bin/python tests/test_confirm.py
.venv/bin/python tests/agentcore_project/test_agentcore_project_mise_tasks.py
.venv/bin/python tests/agentcore_project/test_agentcore_project_gen.py
```
