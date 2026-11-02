---
description: "How CDK code is tested: unit tests only synthesize each stack through StackEnum with the test config and make no AWS call, the enums and task generator have their own unit tests, and deployed outputs are checked only by integration tests. Read when writing or fixing a CDK test."
---

# CDK Tests

Seed repo: [`tests/cdk/`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/tree/1.0.0/tests/cdk), [a stack test](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/tests/cdk/stacks/test_cdk_stacks_alerts_stack.py).

---

## 1. A stack's unit test only synthesizes

`tests/cdk/stacks/test_cdk_stacks_<x>_stack.py`: build a fresh `One()` with the `config` fixture (`08-one-singleton.md`), create the stack through `StackEnum(app=cdk.App(), one=one)`, assert its type, and call `app.synth()`. Passing means the constructs, names, and cross-stack references are wired up. It does not assert template contents; names are tested in the config tests (`05-config-names.md`).

---

## 2. The other CDK unit tests

- `test_cdk_stack_ctx_enum.py`: entry names, and the values of one `StackCtx`.
- `test_cdk_stack_enum.py`: the entry lists of both enums match, a full synth, and the dependencies between stacks. Update its expected lists when adding a stack.
- `test_cdk_mise_tasks.py`: only that the generated block of `mise.toml` is up to date; the generator itself is left out of coverage (`01-project-layout.md`).

None of them call AWS; all run in `mise run cov`.

---

## 3. Deployed resources

Only `tests_int/` touches a deployed stack (`11-cdk-stack-exports.md`).
