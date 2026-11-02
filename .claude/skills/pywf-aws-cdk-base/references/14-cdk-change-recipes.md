---
description: "The files to touch, in order, for the common CDK changes: add a stack, add a resource or output, make one stack use another's resource, add an environment, remove a stack, and the checks after each. Read before adding or removing a stack, a resource, an output, a stack dependency, or an environment, or when checking that such a change is complete."
---

# CDK Change Recipes

Finish every recipe with section 6.

---

## 1. Add a stack `<x>`

1. Config names (`05-config-names.md`, `09-cdk-layout.md`): `cft_stack_name_<x>`, `cft_stack_url_<x>`, and the names of its resources; add them to the names test.
2. The stack (`09-cdk-layout.md`): `stacks/<x>_stack.py`, or `stacks/<x>_stack/` with mixins.
3. An entry `<x>` in both enums, after the stacks it depends on (`10-cdk-stack-enums.md`).
4. If it has outputs: `stacks/<x>_stack_exports.py` and its `tests_int/` test (`11-cdk-stack-exports.md`).
5. `tests/cdk/stacks/test_cdk_stacks_<x>_stack.py`, and the expected lists in the enum tests (`13-cdk-tests.md`).
6. `mise run cdk-gen-tasks` (`12-cdk-mise-tasks.md`).

---

## 2. Add a resource or an output to a stack

1. Its names in the config.
2. A new `s0N_...` method, or a new mixin in the folder form.
3. For an output: follow `11-cdk-stack-exports.md` section 4.

---

## 3. Make stack `<b>` use a resource of stack `<a>`

Add the resource as a named `__init__` argument of `<b>`, pass `self.<a>.<attr>` in the `<b>` entry of `StackEnum`, and keep `<a>` above `<b>` in both enums. Never look the value up by name inside `<b>`.

---

## 4. Add an environment `<env>`

The general steps are in `03-env.md`. For CDK, also add `<env>` to `STACK_NAMES` in every `*_stack_exports.py`, then run `mise run cdk-gen-tasks`. Deploy to it with the user's yes.

---

## 5. Remove a stack `<x>`

Destroy it in every environment first, `cdk-down-<env>-<x>-stack`, with the user's yes for each environment. Then undo section 1 and run `mise run cdk-gen-tasks`.

---

## 6. Checks after any change

1. `mise run cdk-gen-tasks`, if the stacks or the environments changed.
2. `mise run cdk-synth-<env>-all` for one environment.
3. `mise run cov`, then `mise run format` and `mise run lint`.
4. Optionally `mise run cdk-plan-<env>-<x>-stack` to show the diff. Deploying is a separate step, after the user's yes.
