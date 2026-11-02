---
description: "The two enums of stacks: StackCtxEnum (one cdk_mate StackCtx per stack of the current environment, no CDK construct) and StackEnum (one CDK stack per stack, arguments by name, dependencies as attribute access), their identical entries, and why cdk_mate's own best practice does not apply. Read before adding, removing, or reordering a stack, or wiring one stack to another."
---

# Stack Enums

Seed repo: [`stack_ctx_enum.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/cdk/stack_ctx_enum.py), [`stack_enum.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/cdk/stack_enum.py), [`one_03_cdk.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/one/one_03_cdk.py).

---

## 1. `StackCtxEnum`: what to deploy, without CDK

One `cdk_mate.StackCtx` per stack of the **current** environment (`03-env.md`), built by `_new(stack_name)`:

- construct ID = stack name = `config.cft_stack_name_<x>`, which already contains the environment;
- account and region from the config (`04-config-model.md`), so no STS call;
- session `one.bsm` (`06-boto-session.md`).

Building it creates no CDK construct, so tools that only need names and URLs (the task generator) stay fast.

---

## 2. `StackEnum`: the CDK stacks

One CDK stack per stack, in one `cdk.App`, each entry written out by hand:

- `**self.one.stack_ctx_enum.<x>.to_stack_kwargs()`, `config=self.one.config`, then every other argument by name, so a new `__init__` argument breaks every entry that does not pass it.
- A dependency is attribute access: `alert_topic=self.<a>.alert_topic`. CDK turns it into an export, an import, and a deploy order.
- `synth()` creates every stack, then synthesizes the app.

---

## 3. Entries

- Every entry is a `cached_property` named after the stack's short name (`alerts`), so it is built once; the same construct ID twice in one app is an error.
- Both enums have the same entries in the same order, a stack after the stacks it depends on. `tests/cdk/test_cdk_stack_enum.py` checks the two lists match.
- `get(name)` and `get_all()` read the entries in order; loop over `get_all()` instead of naming each stack.
- No entry may be named `all`; it is reserved for the tasks that act on every stack.
- Reach them as `one.stack_ctx_enum` and `one.stack_enum`, from the `one_03_cdk.py` mixin (`08-one-singleton.md`), which imports `aws_cdk` only inside the property.

---

## 4. Not cdk_mate's best practice

cdk_mate's own docs (and the `pypi-cdk_mate` skill's `best-practices.md`) describe another layout: a `bsm_enum`, one entry per (stack, environment), `StackCtx.new` with an STS call, one `cdk/<stack>/` app per stack. Ignore it here. Use cdk_mate only for its API: `StackCtx`, `to_stack_kwargs`, `stack_console_url`, `cli.*`.
