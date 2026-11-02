# cdk_mate: Multi-Stack, Multi-Environment Best Practices

A real CDK project has several stacks, each deployed to several environments (dev, test, prod, often in different AWS accounts). This is the layout cdk_mate recommends. Every file below is real and deployed to two AWS accounts:

- Enums and stack definitions: <https://github.com/MacHu-GWU/cdk_mate-project/tree/main/cdk_mate/tests>
- `cdk.json`, app scripts, deploy scripts: <https://github.com/MacHu-GWU/cdk_mate-project/tree/main/cdk>
- Synth test without AWS: <https://github.com/MacHu-GWU/cdk_mate-project/blob/main/tests/test_stack_ctx.py> (`TestStackCtxSynth`)
- Docs page: <https://cdk-mate.readthedocs.io/en/latest/03-Multi-Stack-Multi-Environment-Best-Practices/index.html>

`cdk_mate.tests.*` ships inside the package as an **example**; in your project, copy the pattern into your own package (`my_app/iac/...`), do not import `cdk_mate.tests`.

## Example project

Two stacks × two environments = four CloudFormation stacks.

- **Stack1 (alerts):** SNS topic + SSM parameter holding a per-environment log level (`DEBUG` dev, `INFO` test).
- **Stack2 (publisher):** IAM role allowed to publish to Stack1's topic, + SSM parameter with the topic ARN. Stack2 depends on Stack1 in the same environment.

```text
my_package/                     # cdk_mate/tests/ in the example
├── bsm_enum.py                 # one boto session per environment
├── stack_ctx_enum.py           # layer 1: one StackCtx per (stack, env)
├── stack_enum.py               # layer 2: one CDK stack per (stack, env)
└── stacks/
    ├── stack1/
    │   ├── iac_define.py               # class Stack1: __init__ + explicit args
    │   ├── iac_define_01_alerts.py     # mixin: SNS topic
    │   └── iac_define_02_config.py     # mixin: SSM parameter
    └── stack2/
        ├── iac_define.py               # class Stack2: takes alert_topic
        ├── iac_define_01_publisher.py  # mixin: IAM role
        └── iac_define_02_config.py
cdk/
├── cdk.json, app.py, deploy.py         # all stacks, one environment at a time
├── stack1/  cdk.json, stack1_app.py, stack1_deploy.py   # Stack1 only
└── stack2/  cdk.json, stack2_app.py, stack2_deploy.py   # Stack2 (+ Stack1, its dependency)
```

## Why two layers

| Layer | Entry is | Used by |
| :--- | :--- | :--- |
| `stack_ctx_enum.py` | a `StackCtx`: plain data + the `bsm` that deploys it | deploy scripts (synth/diff/deploy/destroy) |
| `stack_enum.py` | the CDK stack, created in a given `cdk.App` from the matching `StackCtx` | app scripts that `cdk.json` runs |

- **Deploy scripts need only stack contexts.** They import `stack_ctx_enum` alone and never load a stack definition, so they stay fast. The CDK CLI loads the stacks itself by running the app script.
- **Each stack's arguments are written out by name.** One method per entry, so a new `__init__` argument breaks every entry that does not pass it. A generic "create the stack of this context" helper would hide the signature behind `**kwargs`.
- **Dependencies are plain attribute access** (`self.stack1_dev.alert_topic`). CDK turns it into an export in Stack1, an import in Stack2, and a stack dependency.
- **Every entry is a `cached_property`**: built once, on first use. Using `stack2_dev` creates `stack1_dev` once; creating the same construct id twice in one app is an error. No STS call happens until a `StackCtx` is needed.
- **The app is passed in** (`StackEnum(app=cdk.App())`), so every app script and test starts from a fresh app.

## `bsm_enum.py`

```python
from functools import cached_property
from boto_session_manager.api import BotoSesManager

class BsmEnum:
    def __init__(self):
        self.use_mock: bool = False   # tests set True → moto's fake account

    def _get_bsm(self, profile: str) -> BotoSesManager:
        if self.use_mock:
            return BotoSesManager(region_name="us-east-1")
        return BotoSesManager(profile_name=profile)

    @cached_property
    def dev(self) -> BotoSesManager:
        return self._get_bsm("my_app_dev_us_east_1")

    @cached_property
    def test(self) -> BotoSesManager:
        return self._get_bsm("my_app_test_us_east_1")

bsm_enum = BsmEnum()
```

## Layer 1: `stack_ctx_enum.py`

```python
from functools import cached_property
import cdk_mate.api as cdk_mate
from .bsm_enum import bsm_enum

class StackCtxEnum:
    """One StackCtx per (stack, environment), named <stack>_<env>."""

    @cached_property
    def stack1_dev(self) -> cdk_mate.StackCtx:
        return cdk_mate.StackCtx.new(stack_name="cdk-mate-stack1-dev", bsm=bsm_enum.dev)

    @cached_property
    def stack1_test(self) -> cdk_mate.StackCtx:
        return cdk_mate.StackCtx.new(stack_name="cdk-mate-stack1-test", bsm=bsm_enum.test)

    @cached_property
    def stack2_dev(self) -> cdk_mate.StackCtx:
        return cdk_mate.StackCtx.new(stack_name="cdk-mate-stack2-dev", bsm=bsm_enum.dev)

    @cached_property
    def stack2_test(self) -> cdk_mate.StackCtx:
        return cdk_mate.StackCtx.new(stack_name="cdk-mate-stack2-test", bsm=bsm_enum.test)

stack_ctx_enum = StackCtxEnum()
```

## Layer 2: `stack_enum.py`

```python
import dataclasses
from functools import cached_property
import aws_cdk as cdk
from .stacks.stack1.iac_define import Stack1
from .stacks.stack2.iac_define import Stack2
from .stack_ctx_enum import stack_ctx_enum

@dataclasses.dataclass
class StackEnum:
    app: cdk.App = dataclasses.field()

    @cached_property
    def stack1_dev(self) -> Stack1:
        return Stack1(
            scope=self.app,
            **stack_ctx_enum.stack1_dev.to_stack_kwargs(),
            log_level="DEBUG",                         # per-environment argument
        )

    @cached_property
    def stack1_test(self) -> Stack1:
        return Stack1(scope=self.app, **stack_ctx_enum.stack1_test.to_stack_kwargs(), log_level="INFO")

    @cached_property
    def stack2_dev(self) -> Stack2:
        return Stack2(
            scope=self.app,
            **stack_ctx_enum.stack2_dev.to_stack_kwargs(),
            alert_topic=self.stack1_dev.alert_topic,  # dependency on Stack1
        )

    @cached_property
    def stack2_test(self) -> Stack2:
        return Stack2(scope=self.app, **stack_ctx_enum.stack2_test.to_stack_kwargs(),
                      alert_topic=self.stack1_test.alert_topic)
```

## Stack definitions: class + one mixin per resource group

```python
# stacks/stack1/iac_define.py
import aws_cdk as cdk
from constructs import Construct
from .iac_define_01_alerts import Stack1AlertsMixin
from .iac_define_02_config import Stack1ConfigMixin

class Stack1(cdk.Stack, Stack1AlertsMixin, Stack1ConfigMixin):
    def __init__(self, scope: Construct, id: str, stack_name: str, env: cdk.Environment, log_level: str):
        super().__init__(scope=scope, id=id, stack_name=stack_name, env=env)
        self.log_level = log_level
        self.create_alerts()
        self.create_config()

# stacks/stack1/iac_define_01_alerts.py
import typing as T
from aws_cdk import aws_sns as sns
if T.TYPE_CHECKING:
    from .iac_define import Stack1

class Stack1AlertsMixin:
    def create_alerts(self: "Stack1"):
        self.alert_topic = sns.Topic(self, "AlertTopic", topic_name=f"{self.stack_name}-alerts")

# stacks/stack2/iac_define.py: takes the other stack's resource as an explicit argument
class Stack2(cdk.Stack, Stack2PublisherMixin, Stack2ConfigMixin):
    def __init__(self, scope: Construct, id: str, stack_name: str, env: cdk.Environment, alert_topic: sns.ITopic):
        super().__init__(scope=scope, id=id, stack_name=stack_name, env=env)
        self.alert_topic = alert_topic
        self.create_publisher()   # iam.Role + self.alert_topic.grant_publish(role)
        self.create_config()
```

## `cdk/`: app and deploy scripts

`cdk/cdk.json` runs the app with the project's Python: `"app": "../.venv/bin/python app.py"` (`"../../.venv/bin/python stack2_app.py"` in a subfolder).

```python
# cdk/app.py: all stacks
import aws_cdk as cdk
from my_package.stack_enum import StackEnum

stack_enum = StackEnum(app=cdk.App())
_ = stack_enum.stack1_dev
_ = stack_enum.stack1_test
_ = stack_enum.stack2_dev
_ = stack_enum.stack2_test
stack_enum.app.synth()
```

```python
# cdk/deploy.py: one list per environment, one cdk command per list
import cdk_mate.api as cdk_mate
from my_package.stack_ctx_enum import stack_ctx_enum

create_dev_stack_ctx_list = [stack_ctx_enum.stack1_dev, stack_ctx_enum.stack2_dev]     # creation order
create_test_stack_ctx_list = [stack_ctx_enum.stack1_test, stack_ctx_enum.stack2_test]
delete_dev_stack_ctx_list = [stack_ctx_enum.stack2_dev, stack_ctx_enum.stack1_dev]     # deletion order
delete_test_stack_ctx_list = [stack_ctx_enum.stack2_test, stack_ctx_enum.stack1_test]

cdk_mate.cli.Synth().run(dir_cdk=__file__)                       # whole app
# cdk_mate.cdk_diff_many(create_dev_stack_ctx_list, dir_cdk=__file__)
cdk_mate.cdk_deploy_many(create_dev_stack_ctx_list, dir_cdk=__file__, prompt=False)
cdk_mate.cdk_deploy_many(create_test_stack_ctx_list, dir_cdk=__file__, prompt=False)
# cdk_mate.cdk_destroy_many(delete_dev_stack_ctx_list, dir_cdk=__file__, prompt=False)
```

```python
# cdk/stack2/stack2_app.py: one stack (its dependencies come along)
stack_enum = StackEnum(app=cdk.App())
_ = stack_enum.stack2_dev    # also creates stack1_dev
_ = stack_enum.stack2_test
stack_enum.app.synth()

# cdk/stack2/stack2_deploy.py: uncomment the step you want
# stack_ctx_enum.stack2_dev.cdk_diff(dir_cdk=__file__)
# stack_ctx_enum.stack2_dev.cdk_deploy(dir_cdk=__file__, prompt=False)
# stack_ctx_enum.stack2_dev.cdk_destroy(dir_cdk=__file__, prompt=False)
```

`dir_cdk=__file__` makes the scripts runnable from any cwd: `python /path/to/cdk/deploy.py`.

## Order of dependent stacks

- `cdk deploy` of Stack2 deploys Stack1 first; `exclusively=True` deploys Stack2 only.
- `cdk destroy` of Stack1 destroys Stack2 first; with `exclusively=True` it fails while Stack2 exists.
- A list in one command runs in dependency order whatever the list order; the lists above are ordered anyway, for readability.
- `cdk_*_many` uses the first stack's `bsm` and warns when the list spans accounts/regions: one list per environment.

## Testing without AWS

Under a moto mock (`bsm_enum.use_mock = True`), create every stack in a fresh `cdk.App` and synth it (needs `node` for aws-cdk-lib, no AWS account):

```python
app = cdk.App()
stack_enum = StackEnum(app=app)
_ = stack_enum.stack2_dev
assembly = app.synth()
template = assembly.get_stack_by_name("cdk-mate-stack2-dev").template
```

## Adding to the project

**A new environment:** add a `BsmEnum` property (`prod`); add `<stack>_prod` to `stack_ctx_enum.py` and `stack_enum.py` with that environment's arguments; add them to the app scripts and a new list in the deploy scripts.

**A new stack:** create `stacks/<stack>/iac_define.py` + mixins, taking its settings and other stacks' resources as explicit `__init__` args; add one entry per environment to both enums (dependency: `self.<other>_<env>.<resource>`); add it to the synth test; add it to `cdk/app.py` / `cdk/deploy.py` or give it its own `cdk/<stack>/` folder.
