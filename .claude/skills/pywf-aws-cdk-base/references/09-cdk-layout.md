---
description: "Where CDK code lives: everything in <package_name>/cdk/, one stack per module under stacks/ in a single-file or a folder-with-mixins form, the stack constructor signature, names read from the config, and the thin cdk/ folder at the repo root. Read before writing or reviewing a stack, or when deciding where CDK code goes."
---

# CDK Layout

---

## 1. All CDK code is in the package

```text
<package_name>/cdk/
├── stack_ctx_enum.py, stack_enum.py   # the two enums of stacks
├── mise_tasks.py                      # generates the cdk mise tasks
└── stacks/
    ├── <x>_stack.py                   # a small stack, one file
    ├── <x>_stack_exports.py           # its outputs, for other projects
    └── <y>_stack/                     # a stack that grew: one mixin per resource group
        ├── stack.py
        ├── stack_01_<topic>.py
        └── stack_02_<topic>.py
```

Seed repo: [`alerts_stack.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cookiecutter_aws_cdk_demo/cdk/stacks/alerts_stack.py) (one file), [`publisher_stack/`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/tree/1.0.0/cookiecutter_aws_cdk_demo/cdk/stacks/publisher_stack) (folder).

---

## 2. A stack class

- `__init__(self, scope, id, stack_name, env, config, <resources of other stacks, by name>)`: the first four come from `StackCtx.to_stack_kwargs()`; `config` is the `Config` of the environment (`04-config-model.md`).
- The body stores `self.config`, then calls `self.s01_<verb>_<what>()`, `self.s02_...()` in order, one method per resource group. In the folder form each method lives in its `stack_0N_<topic>.py` mixin.
- **Every name comes from the config** (`05-config-names.md`): `topic_name=self.config.sns_topic_name_<x>`. A stack builds no name string. Add CloudFormation names there too: `cft_stack_name_<x>`, `cft_stack_url_<x>`, `cft_export_name_<value>`.
- Outputs other projects need are a `cdk.CfnOutput` with `export_name=self.config.cft_export_name_<value>`, in a last `s0N_create_outputs` method.

---

## 3. The thin `cdk/` folder at the root

Only `cdk.json` (`"app": "../.venv/bin/python cdk_app.py"`) and [`cdk_app.py`](https://github.com/MacHu-GWU/cookiecutter_aws_cdk_demo-project/blob/1.0.0/cdk/cdk_app.py), whose body is `one.stack_enum.synth()`. The app holds the stacks of the current environment only (`03-env.md`), so `ENV_NAME=prd cdk synth` synthesizes prd and never needs another environment's config. Never put stack logic here.
