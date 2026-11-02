# cdk_mate 1.0.0: Public API Reference

```python
from cdk_mate.api import StackCtx
import cdk_mate.api as cdk_mate     # then cdk_mate.StackCtx, cdk_mate.cli.Deploy
```

Docs: <https://cdk-mate.readthedocs.io/> · Source: <https://github.com/MacHu-GWU/cdk_mate-project>

---

## 1. CDK CLI in Python: `cdk_mate.cli`

`cdk_mate.api.cli` is a namespace of dataclasses, one per CDK CLI command (all except `cdk docs` and `cdk lsp`). They are generated from the option registry of aws-cdk CLI 2.1145.0, so field names are the CLI option names in snake_case and fixed-choice options are typed `Literal`. Field list per class: `cdk-commands.md`.

### `cdk_mate.cli.BaseCommand`

The base of every command. Its fields are the global options, accepted by every command.

| Field | Type | CLI |
| :--- | :--- | :--- |
| `cdk_cmd` | `list[str]` | executable; `["cdk"]` when unset. Pin a version: `["npx", "aws-cdk@2.1145.0"]` |
| `extra_args` | `list[str]` | appended verbatim at the end, for options not defined yet |
| `app` | `str` | `--app` |
| `profile` | `str` | `--profile` |
| `region` | `str` | `--region` |
| `role_arn` | `str` | `--role-arn` (role for CloudFormation) |
| `context` | `dict[str, str]` | `--context K=V` |
| `output` | `str` | `--output` (cloud assembly dir) |
| `verbose` | `int` | `--verbose` × n |
| `debug`, `json`, `strict`, `trace`, `ci`, `color`, `no_color`, `lookups`, `staging`, `notices`, `yes`, `ignore_errors`, `version_reporting`, `asset_metadata`, `path_metadata`, ... | `bool` | `--x` / `--no-x` |
| `plugin`, `unstable` | `list[str]` | repeated |
| `build`, `proxy`, `ca_bundle_path`, `telemetry_file` | `str` | value |

#### `.to_args() -> list[str]`

The command line `run()` would execute. Needs no AWS and no `cdk`.

```python
cdk_mate.cli.Deploy(stacks=["MyStack"], require_approval="never").to_args()
# ['cdk', 'deploy', 'MyStack', '--require-approval', 'never']
cdk_mate.cli.Deploy().to_args()                          # ['cdk', 'deploy']
cdk_mate.cli.Deploy(rollback=False).to_args()            # ['cdk', 'deploy', '--no-rollback']
cdk_mate.cli.Deploy(concurrency=0).to_args()             # ['cdk', 'deploy', '--concurrency', '0']
cdk_mate.cli.Deploy(change_set_name="").to_args()        # ['cdk', 'deploy']
cdk_mate.cli.Deploy(notification_arns=["arn:a", "arn:b"]).to_args()
# ['cdk', 'deploy', '--notification-arns', 'arn:a', '--notification-arns', 'arn:b']
cdk_mate.cli.Deploy(parameters={"MyStack:Env": "dev"}).to_args()
# ['cdk', 'deploy', '--parameters', 'MyStack:Env=dev']
cdk_mate.cli.Synth(verbose=2).to_args()                  # ['cdk', 'synth', '--verbose', '--verbose']
cdk_mate.cli.Diff(stacks=["MyStack"], fail=True, profile="p").to_args()
# ['cdk', 'diff', 'MyStack', '--fail', '--profile', 'p']   (command fields first, then globals)
cdk_mate.cli.Deploy(stacks=["MyStack"], extra_args=["--tags", "team=data"]).to_args()
# ['cdk', 'deploy', 'MyStack', '--tags', 'team=data']
cdk_mate.cli.Synth(cdk_cmd=["npx", "aws-cdk@2.1145.0"], quiet=True).to_args()
# ['npx', 'aws-cdk@2.1145.0', 'synth', '--quiet']
```

Rules: `True` → `--name`, `False` → `--no-name`; `0` is passed; `None`, `""`, unset pass nothing; a list repeats the option; a dict becomes `KEY=VALUE`; a trailing `_` in a field name is dropped (`import_` → `--import`, `list_` → `--list`); `_` becomes `-`.

**Gotcha:** the CDK CLI prints `Unknown option(s): ... These will be ignored.` and exits 0 for an option it does not know. A field that exists in cdk_mate may not exist in an older CLI: pin the CLI (`cdk_cmd`) or check its version.

#### `.run(bsm: BotoSesManager | None = None, dir_cdk: str | os.PathLike | None = None) -> subprocess.CompletedProcess`

Runs `to_args()` with `subprocess.run(check=True)`; output goes straight to the terminal.

- `bsm`: the subprocess gets `AWS_REGION`, plus `AWS_PROFILE` if `bsm` came from a named profile, else a frozen access key / secret / session token. Any `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_PROFILE` inherited from the parent is removed first. `None` → the default credential chain of the environment.
- `dir_cdk`: the subprocess cwd, i.e. the folder holding `cdk.json`. A file path (typically `__file__`) means its parent. Not a dir → `NotADirectoryError`.
- The calling process's `os.environ` and cwd never change, so it is thread-safe.
- Raises `subprocess.CalledProcessError` on non-zero exit (note `cdk diff --fail` exits 1 on a diff).

```python
from boto_session_manager.api import BotoSesManager
import cdk_mate.api as cdk_mate

bsm = BotoSesManager(profile_name="dev", region_name="us-east-1")

cdk_mate.cli.Bootstrap(
    aws_environment=["aws://123456789012/us-east-1"],
    qualifier="hnb659fds",
).run(bsm=bsm)

cdk_mate.cli.Synth().run(dir_cdk="/path/to/cdk/project")
cdk_mate.cli.Diff(stacks=["MyStack"], method="template", security_only=True).run(bsm=bsm, dir_cdk=__file__)
cdk_mate.cli.Deploy(stacks=["MyStack"], require_approval="never").run(bsm=bsm, dir_cdk=__file__)
cdk_mate.cli.Destroy(stacks=["Stack1", "Stack2"], force=True).run(bsm=bsm, dir_cdk=__file__)
```

---

## 2. Stack context

### `StackCtx`

```python
@dataclasses.dataclass
class StackCtx:
    construct_id: str          # required; CDK construct id, also what `cdk deploy <id>` takes
    stack_name: str            # required; CloudFormation stack name
    aws_account_id: str        # required
    aws_region: str            # required
    bsm: BotoSesManager | None = None   # credentials used by the cdk_* methods
```

Plain data: building one creates no CDK construct. Subclass it to add fields.

```python
stack1 = cdk_mate.StackCtx(
    construct_id="CdkMateStack1Dev",
    stack_name="cdk-mate-stack1-dev",
    aws_account_id="123456789012",
    aws_region="us-east-1",
)
```

#### `StackCtx.new(stack_name: str, bsm: BotoSesManager) -> StackCtx` (classmethod)

`cls(**cls.make_stack_ctx_kwargs(stack_name, bsm))`. Reading `bsm.aws_account_id` makes one `sts:GetCallerIdentity` call, so wrap it in a `cached_property` (see `best-practices.md`) to defer it.

```python
ctx = cdk_mate.StackCtx.new(stack_name="cdk-mate-stack1-dev", bsm=bsm)
# construct_id='CdkMateStack1Dev', stack_name='cdk-mate-stack1-dev', account/region from bsm
```

#### `StackCtx.make_stack_ctx_kwargs(stack_name: str, bsm: BotoSesManager) -> dict` (classmethod)

Returns `{"construct_id": to_camel(stack_name), "stack_name": to_slug(stack_name), "aws_account_id": bsm.aws_account_id, "aws_region": bsm.aws_region, "bsm": bsm}`. Override in a subclass to change naming or fill extra fields; `new` uses it.

#### `.to_stack_kwargs() -> dict[str, Any]`

`{"id": construct_id, "stack_name": stack_name, "env": cdk.Environment(account=..., region=...)}`. Your stack's `__init__` must accept `scope, id, stack_name, env` (plus its own args):

```python
class Stack1(cdk.Stack):
    def __init__(self, scope: Construct, id: str, stack_name: str, env: cdk.Environment, log_level: str):
        super().__init__(scope=scope, id=id, stack_name=stack_name, env=env)
        ...

Stack1(scope=app, **ctx.to_stack_kwargs(), log_level="DEBUG")
```

#### `.stack_console_url -> str` (property)

`https://{region}.console.aws.amazon.com/cloudformation/home?region={region}#/stacks?filteringStatus=active&filteringText={stack_name}&viewNested=true`

#### `.cdk_synth(dir_cdk=None, **kwargs)` / `.cdk_diff(dir_cdk=None, **kwargs)`
#### `.cdk_deploy(dir_cdk=None, prompt: bool = False, **kwargs)` / `.cdk_destroy(dir_cdk=None, prompt: bool = False, **kwargs)`

`build_cmd(<Cmd>, [self], prompt=..., **kwargs).run(bsm=self.bsm, dir_cdk=dir_cdk)`, after logging the console URL. `kwargs` are any fields of the command class (e.g. `exclusively=True`).

```python
ctx.cdk_diff(dir_cdk=__file__)
ctx.cdk_deploy(dir_cdk=__file__, prompt=False)          # --require-approval never
ctx.cdk_deploy(dir_cdk=__file__, exclusively=True)       # skip dependencies
ctx.cdk_destroy(dir_cdk=__file__, prompt=True)           # CLI asks for confirmation
```

### `build_cmd(cmd_class: type[T_CMD], stack_ctx_list: list[StackCtx], prompt: bool = False, **kwargs) -> T_CMD`

Builds (does not run) the command every `cdk_*` method and `cdk_*_many` function runs.

- `stacks` = `[ctx.construct_id for ctx in stack_ctx_list]`, in order.
- `Deploy`: `prompt=False` → `require_approval="never"`; `prompt=True` → not set (CLI asks).
- `Destroy`: `prompt=False` → `force=True`; `prompt=True` → not set.
- `kwargs` override those defaults (`require_approval="broadening"`).
- Empty list → `ValueError("stack_ctx_list is empty, there is no stack to run")`.

```python
cdk_mate.build_cmd(cdk_mate.cli.Synth, [stack1]).to_args()
# ['cdk', 'synth', 'CdkMateStack1Dev']
cdk_mate.build_cmd(cdk_mate.cli.Deploy, [stack1]).to_args()
# ['cdk', 'deploy', 'CdkMateStack1Dev', '--require-approval', 'never']
cdk_mate.build_cmd(cdk_mate.cli.Destroy, [stack1]).to_args()
# ['cdk', 'destroy', 'CdkMateStack1Dev', '--force']
cdk_mate.build_cmd(cdk_mate.cli.Deploy, [stack1], prompt=True).to_args()
# ['cdk', 'deploy', 'CdkMateStack1Dev']
cdk_mate.build_cmd(cdk_mate.cli.Deploy, [stack1, stack2], require_approval="broadening", concurrency=2).to_args()
# ['cdk', 'deploy', 'CdkMateStack1Dev', 'CdkMateStack2Dev', '--concurrency', '2', '--require-approval', 'broadening']

cmd = cdk_mate.build_cmd(cdk_mate.cli.Deploy, [stack1, stack2])
print(" ".join(cmd.to_args()))         # check first
cmd.run(bsm=bsm, dir_cdk=__file__)     # then run the same object
```

### `cdk_synth_many(stack_ctx_list, dir_cdk=None, **kwargs)`
### `cdk_diff_many(stack_ctx_list, dir_cdk=None, **kwargs)`
### `cdk_deploy_many(stack_ctx_list, dir_cdk=None, prompt: bool = False, **kwargs)`
### `cdk_destroy_many(stack_ctx_list, dir_cdk=None, prompt: bool = False, **kwargs)`

One `cdk` command for all listed stacks: the app is synthesized once and the CLI orders stacks by dependency regardless of list order.

- Runs with the **first** stack's `bsm` (`None` → default credentials). If the list spans several (account, region) pairs, a warning is logged: that works only when the other accounts trust the first (`cdk bootstrap --trust`). Keep one list per environment.
- Logs every stack's console URL first.
- Empty list → `ValueError`.
- `cdk_synth_many` still runs the whole app; naming stacks only selects what is reported. For every stack: `cdk_mate.cli.Synth().run(dir_cdk=__file__)`.

```python
cdk_mate.cdk_deploy_many([stack_ctx_enum.stack1_dev, stack_ctx_enum.stack2_dev], dir_cdk=__file__, prompt=False)
cdk_mate.cdk_destroy_many([stack_ctx_enum.stack2_dev, stack_ctx_enum.stack1_dev], dir_cdk=__file__, prompt=False)
```

---

## 3. Utilities

### `to_camel(s: str) -> str`

Whitespace, `-` and `_` split words; each is capitalized. Used for construct ids.

```python
cdk_mate.to_camel("Hello_world")          # 'HelloWorld'
cdk_mate.to_camel("HELLO WORLD")          # 'HelloWorld'
cdk_mate.to_camel("cdk-mate-stack1-dev")  # 'CdkMateStack1Dev'
```

### `to_slug(s: str) -> str`

Whitespace runs and `_` become `-`; case is kept. Used for CloudFormation stack names.

```python
cdk_mate.to_slug("Hello_World")           # 'Hello-World'
cdk_mate.to_slug("hello  world")          # 'hello-world'
```

---

## 4. Logging

cdk_mate logs through the standard `logging` logger `"cdk_mate"` (plain messages to stdout by default): console URLs, the CDK directory, the masked AWS account / principal / region of `bsm`, and the command line (`shlex.join`, copy-pasteable). The identity report costs one `sts:GetCallerIdentity` call and is skipped when the logger is quieter than `INFO`; a failure there only logs a warning.

```python
import logging
logging.getLogger("cdk_mate").setLevel(logging.WARNING)
```
