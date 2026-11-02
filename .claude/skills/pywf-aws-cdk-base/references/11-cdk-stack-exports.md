---
description: "The <x>_stack_exports.py module every stack with outputs has: a standard-library-only file another project copies to read the stack's outputs, with literal stack names, one property per output, to_dict, and its integration test. Read before adding or changing a stack output, or when another project needs a stack's values."
---

# Stack Exports

Seed repo: [`alerts_stack_exports.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/cdk/stacks/alerts_stack_exports.py), [its test](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/tests_int/test_cdk_stacks_alerts_stack_exports.py).

---

## 1. Why

Another project that needs a value of this stack, such as a topic ARN, copies this one file instead of depending on this project or guessing output keys.

---

## 2. Rules

- **Standard library only.** A boto3 type stub under `if T.TYPE_CHECKING:` is the one exception. Nothing from this project, not even the config.
- **`STACK_NAMES`:** the literal stack name of every environment, `{"dev": "<project>-dev-<x>", ...}`, not computed.
- `<X>StackExports.load(cf_client, env_name)` reads the outputs with one `describe_stacks` call; `from_describe_stacks_response` parses the response.
- **One property per `cdk.CfnOutput`**, read by its output key, and every property listed in `to_dict()`.
- Left out of coverage in `.coveragerc`: it can only be tested against a deployed stack.

---

## 3. Integration test

`tests_int/test_cdk_stacks_<x>_stack_exports.py` checks `STACK_NAMES[env_name] == one.config.cft_stack_name_<x>`, then loads the exports with `one.cloudformation_client` and calls `to_dict()`, which raises `KeyError` for a missing output. It runs with `mise run int-test`, against the stack deployed in `ENV_NAME`.

---

## 4. Adding an output

1. Its export name in the config: `cft_export_name_<value>` (`05-config-names.md`).
2. A `cdk.CfnOutput` in the stack's outputs method.
3. A property here, and its line in `to_dict()`.
