---
name: pypi-cdk_mate
description: "cdk_mate (v1.0.0, valid for cdk_mate >=1.0.0,<2.0.0): run the AWS CDK CLI from Python with explicit boto sessions, and organize multi-stack, multi-environment CDK projects. Public API: StackCtx, build_cmd, cdk_synth_many, cdk_diff_many, cdk_deploy_many, cdk_destroy_many, to_camel, to_slug, and cli.<Command> dataclasses (Deploy, Diff, Synth, Destroy, Bootstrap, ...). Use when code imports cdk_mate, mentions StackCtx or stack_ctx_enum / stack_enum, or needs to synth/diff/deploy/destroy CDK stacks from Python across AWS accounts."
---

# cdk_mate 1.0.0

**Version scope:** written for cdk_mate 1.0.0 and valid for every 1.x release (`>=1.0.0,<2.0.0`): semantic versioning keeps the public API below backward compatible within 1.x, though a later 1.x may add commands or options not listed here. Check the installed version with `importlib.metadata.version("cdk_mate")`. On 0.x, this skill does not apply (no `build_cmd`, `cdk_synth_many`, `cdk_cmd`, `extra_args`, and `False` / `0` options were not passed); read that version's source instead. On 2.0 or newer, treat this skill as possibly outdated and check the release history.

Three pieces: (1) **CDK CLI in Python**: one dataclass per `cdk` command, one field per option; `.to_args()` builds the command line, `.run(bsm=..., dir_cdk=...)` runs it with the credentials of a `boto_session_manager.BotoSesManager` and in the folder of `cdk.json`, without touching your own `os.environ` or cwd. (2) **`StackCtx`**: one stack in one environment (construct id, stack name, account, region, bsm), with `cdk_*` methods and `cdk_*_many` functions. (3) **Best practice** for many stacks × many environments: `bsm_enum` → `stack_ctx_enum` (layer 1) → `stack_enum` (layer 2). Python 3.11+.

## Import

```python
from cdk_mate.api import StackCtx
import cdk_mate.api as cdk_mate     # then cdk_mate.StackCtx, cdk_mate.cli.Deploy
```

## Public API

- `cdk_mate.cli.<Command>`: dataclasses `Acknowledge, Bootstrap, CliTelemetry, Context, Deploy, Destroy, Diagnose, Diff, Doctor, Drift, Flags, GC, Import, Init, List, Metadata, Migrate, Notices, Orphan, PublishAssets, Refactor, Rollback, Synth, Validate, Watch`, all subclasses of `cdk_mate.cli.BaseCommand`. Every field defaults to "not set" and is then omitted, so the CLI uses its own default.
  - `.to_args() -> list[str]`: the command line, e.g. `["cdk", "deploy", "MyStack", "--require-approval", "never"]`.
  - `.run(bsm: BotoSesManager | None = None, dir_cdk: str | PathLike | None = None) -> subprocess.CompletedProcess`: raises `CalledProcessError` on non-zero exit. `dir_cdk` may be a file (e.g. `__file__`); its parent is used.
  - Global fields on every command: `profile`, `region`, `context: dict`, `app`, `output`, `verbose: int`, ..., plus `cdk_cmd: list[str]` (executable, default `["cdk"]`, e.g. `["npx", "aws-cdk@2.1145.0"]`) and `extra_args: list[str]` (appended verbatim).
- `StackCtx(construct_id: str, stack_name: str, aws_account_id: str, aws_region: str, bsm: BotoSesManager | None = None)`: dataclass for one stack in one environment.
  - `StackCtx.new(stack_name: str, bsm: BotoSesManager) -> StackCtx`: construct id = `to_camel(stack_name)`, stack name = `to_slug(stack_name)`, account/region from `bsm` (one STS call).
  - `StackCtx.make_stack_ctx_kwargs(stack_name, bsm) -> dict`: the kwargs `new` uses; override in a subclass to change naming.
  - `.to_stack_kwargs() -> dict`: `{"id", "stack_name", "env": cdk.Environment}` for your `cdk.Stack.__init__`.
  - `.stack_console_url -> str`: CloudFormation console URL.
  - `.cdk_synth(dir_cdk=None, **kwargs)`, `.cdk_diff(dir_cdk=None, **kwargs)`: run for this stack with its `bsm`.
  - `.cdk_deploy(dir_cdk=None, prompt: bool = False, **kwargs)`, `.cdk_destroy(dir_cdk=None, prompt: bool = False, **kwargs)`.
- `build_cmd(cmd_class: type[BaseCommand], stack_ctx_list: list[StackCtx], prompt: bool = False, **kwargs) -> BaseCommand`: build without running; `stacks` = construct ids. `prompt=False` adds `--require-approval never` (Deploy) / `--force` (Destroy); kwargs win. Empty list → `ValueError`.
- `cdk_synth_many(stack_ctx_list, dir_cdk=None, **kwargs)`, `cdk_diff_many(...)`: one `cdk` command for many stacks.
- `cdk_deploy_many(stack_ctx_list, dir_cdk=None, prompt: bool = False, **kwargs)`, `cdk_destroy_many(...)`: same; run with the **first** stack's `bsm` (warning if the list spans accounts/regions). Keep one list per environment.
- `to_camel(s: str) -> str`: `"cdk-mate-stack1-dev"` → `"CdkMateStack1Dev"`.
- `to_slug(s: str) -> str`: `"cdk_mate_stack1_dev"` → `"cdk-mate-stack1-dev"` (case kept).

## Value → argument rules

| Python value | Command line |
| :--- | :--- |
| `True` / `False` | `--name` / `--no-name` (e.g. `rollback=False` → `--no-rollback`) |
| `0` | passed (`--concurrency 0`) |
| `None`, `""`, unset | nothing |
| `list` | option repeated (`--notification-arns a --notification-arns b`) |
| `dict` | `KEY=VALUE` (`parameters={"MyStack:Env": "dev"}`) |
| count (`verbose=2`) | `--verbose --verbose` |

Order: subcommand, positional args (`stacks`), command options, global options, `extra_args`. Field names with a trailing `_` drop it (`import_`, `list_`). The CDK CLI **ignores unknown options with exit 0**, so make sure your CLI version supports what you set.

## Quick examples

```python
from boto_session_manager.api import BotoSesManager
import cdk_mate.api as cdk_mate

bsm = BotoSesManager(profile_name="dev", region_name="us-east-1")
cdk_mate.cli.Deploy(stacks=["MyStack"], require_approval="never").run(bsm=bsm, dir_cdk=__file__)
cdk_mate.cli.Synth().run(dir_cdk=__file__)  # whole app

stack1 = cdk_mate.StackCtx.new(stack_name="my-app-stack1-dev", bsm=bsm)
print(cdk_mate.build_cmd(cdk_mate.cli.Deploy, [stack1]).to_args())  # inspect first
stack1.cdk_diff(dir_cdk=__file__)
cdk_mate.cdk_deploy_many([stack1, stack2], dir_cdk=__file__, prompt=False)
```

Logs (console URLs, masked identity, cwd, command line) go to the `logging` logger `"cdk_mate"`; `logging.getLogger("cdk_mate").setLevel(logging.WARNING)` silences them and skips the STS call.

## Multi-stack, multi-environment best practice (summary)

- `bsm_enum.py`: one `cached_property` `BotoSesManager` per environment (`dev`, `test`, `prod`).
- `stack_ctx_enum.py` (layer 1): one `cached_property` `StackCtx.new(...)` per (stack, env), named `<stack>_<env>`. Deploy scripts import **only** this.
- `stack_enum.py` (layer 2): dataclass with `app: cdk.App`; one `cached_property` per (stack, env), same names, calling `StackX(scope=self.app, **stack_ctx_enum.<name>.to_stack_kwargs(), <own args by name>)`. A dependency is `self.stack1_dev.alert_topic`.
- `stacks/<stack>/iac_define.py` + one mixin file per resource group (`iac_define_01_<topic>.py`).
- `cdk/cdk.json` runs `app.py` (creates stacks via `StackEnum(app=cdk.App())`, then `app.synth()`); `cdk/deploy.py` calls `cdk_*_many` per environment with `dir_cdk=__file__`.

Full example: <https://github.com/MacHu-GWU/cdk_mate-project/tree/main/cdk_mate/tests> (enums, stacks) and <https://github.com/MacHu-GWU/cdk_mate-project/tree/main/cdk> (cdk.json, app and deploy scripts).

## More detail

- `ref/public-api.md`: full API reference with examples.
- `ref/cdk-commands.md`: every command class, its subcommand, and its own fields.
- `ref/best-practices.md`: the full project layout and code for the multi-stack, multi-environment pattern.
