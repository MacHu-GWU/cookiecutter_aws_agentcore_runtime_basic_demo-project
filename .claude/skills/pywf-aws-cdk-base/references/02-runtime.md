---
description: "The runtime: where the code runs (local or ci), how it is detected, and the rule that code which must behave differently per runtime asks the runtime singleton instead of reading the environment itself. Read when code must behave differently on a developer machine and in CI, or when adding a runtime."
---

# Runtime

Seed repo: [`runtime.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/runtime.py).

---

## 1. What it is

The runtime is **where** the code runs, independent of which environment it targets. `RuntimeNameEnum` lists every runtime: `local` (a developer's machine) and `ci` (a CI runner). The `CI` environment variable is the signal for `ci`; anything else is `local`.

This project adds two AgentCore runtimes, checked first:

| Runtime | Where | Signal |
| :--- | :--- | :--- |
| `agentcore` | a deployed AgentCore runtime | `IS_AGENTCORE_RUNTIME=true` (set by `envVars` in `agentcore.json`), no `LOCAL_DEV` |
| `agentcore_local` | the packaged code in `app/<Runtime>/`, run by `agentcore dev` | `IS_AGENTCORE_RUNTIME=true` and `LOCAL_DEV` (set by the AgentCore CLI) |

AgentCore documents no variable of its own for this, so the project sets `IS_AGENTCORE_RUNTIME`; the names are in `constants.py`. The `ac-local-*` tasks run the package from the repo, so they are `local`.

---

## 2. One semantic, one implementation per runtime

Some steps mean the same thing everywhere but are done differently per runtime: getting AWS credentials, loading the config. Write them as one function that branches on `runtime.current_runtime_name()`, and give each runtime its own branch. Never read `os.environ` for the runtime in other modules; the detection rule lives only in `runtime.py`.

A runtime a step does not support raises `NotImplementedError` with a message that says where to run it instead.

---

## 3. Using it

Read it as `one.runtime.current_runtime_name()`, which returns a string such as `"local"`; compare it with `RuntimeNameEnum.<name>.value`. Importing `runtime.py` has no side effect; nothing is detected until asked.

---

## 4. Adding a runtime

Add a member to `RuntimeNameEnum` and its detection rule to `Runtime.get_current_runtime_name`, before the fallback to `local`. Then review every branch on the runtime: each must handle the new one or raise `NotImplementedError`.
