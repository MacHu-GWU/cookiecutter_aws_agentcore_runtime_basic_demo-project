---
description: "The runtime: where the code runs (local or ci), how it is detected, and the rule that code which must behave differently per runtime asks the runtime singleton instead of reading the environment itself. Read when code must behave differently on a developer machine and in CI, or when adding a runtime."
---

# Runtime

Seed repo: [`runtime.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/runtime.py).

---

## 1. What it is

The runtime is **where** the code runs, independent of which environment it targets. `RuntimeNameEnum` lists every runtime: `local` (a developer's machine) and `ci` (a CI runner). The `CI` environment variable is the signal for `ci`; anything else is `local`.

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
