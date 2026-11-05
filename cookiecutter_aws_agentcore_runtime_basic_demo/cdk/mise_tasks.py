# -*- coding: utf-8 -*-

"""
Generate the ``<env-tasks>`` block of ``mise.toml`` (``mise run gen-env-tasks``):
four tasks per (environment, stack), ``cdk-<action>-<env>-<stack>-stack``, plus
four ``cdk-<action>-<env>-all`` per environment. Each task prints the console URL
of the stacks it acts on, then runs one plain cdk command in ``cdk/`` with
``ENV_NAME`` and ``--profile {{env.AWS_PROFILE_FOR_<ENV>}}``. See the ``pywf-aws-cdk-base`` skill, ``12-cdk-mise-tasks.md``.

:func:`render_env_tasks_block` also takes the other tasks of each environment,
already rendered, such as the AgentCore ones of
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.agentcore_project.mise_tasks`,
which renders the whole block of this project.

The stacks are the entries of :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum.StackCtxEnum`,
the environments the members of :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.env.EnvNameEnum`;
nothing calls AWS.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

from ..env import ENV_NAME_VAR
from ..env import EnvNameEnum
from ..config.api import Config
from ..one.api import One
from ..one.one_02_boto_ses import get_aws_profile_env_var
from .stack_ctx_enum import StackCtxEnum
from .stack_ctx_enum import list_entry_names

ALL = "all"
"""
The reserved stack name that targets every stack; no stack may use it.
"""

BEGIN_MARKER = "# <env-tasks>"
"""
The line that opens the generated block in ``mise.toml``.
"""

END_MARKER = "# </env-tasks>"
"""
The line that closes the generated block in ``mise.toml``.
"""


@dataclasses.dataclass(frozen=True)
class CdkAction:
    """
    One kind of generated task, such as ``up``.
    """

    # fmt: off
    name: str = dataclasses.field()  #: The action part of the task name, such as ``up``.
    emoji: str = dataclasses.field()  #: Shown in front of the task description.
    summary: str = dataclasses.field()  #: The task description, with ``{target}`` and ``{env}`` placeholders.
    sub_command: str = dataclasses.field()  #: The cdk sub command, such as ``deploy``.
    options: str = dataclasses.field()  #: Options after the stack selector, such as ``--require-approval never``.
    use_profile: bool = dataclasses.field()  #: Whether it calls AWS and needs ``--profile``.
    all_option: str = dataclasses.field(default="--all")  #: Selects every stack; ``cdk synth`` does every stack without one.
    # fmt: on


CDK_ACTIONS: list[CdkAction] = [
    # fmt: off
    CdkAction(
        name="synth",
        emoji="⚪",
        summary="Synthesize {target} of {env} to CloudFormation templates (no AWS call)",
        sub_command="synth",
        options="",
        use_profile=False,
        all_option="",
    ),
    CdkAction(
        name="plan",
        emoji="🔵",
        summary="Plan {target} of {env}: diff against what is deployed, through a CloudFormation change set (no deploy)",
        sub_command="diff",
        options="--method auto",
        use_profile=True,
    ),
    CdkAction(
        name="up",
        emoji="🟢",
        summary="Deploy {target} of {env} (no approval prompt)",
        sub_command="deploy",
        options="--require-approval never",
        use_profile=True,
    ),
    CdkAction(
        name="down",
        emoji="🔴",
        summary="Destroy {target} of {env} (force, no confirmation)",
        sub_command="destroy",
        options="--force",
        use_profile=True,
    ),
    # fmt: on
]
"""
The four actions, in the order they appear in ``mise.toml``.
"""


@dataclasses.dataclass(frozen=True)
class StackTarget:
    """
    One stack of one environment, as a task needs it.
    """

    # fmt: off
    construct_id: str = dataclasses.field()  #: Selects the stack in the cdk CLI; it is the stack name.
    console_url: str = dataclasses.field()  #: Printed before the cdk command.
    # fmt: on


def to_stack_slug(stack: str) -> str:
    """
    The stack part of a task name, such as ``my-stack`` for the entry ``my_stack``.
    """
    return stack.replace("_", "-")


def validate_stacks(stacks: list[str]) -> None:
    """
    :raises ValueError: a stack is named :data:`ALL`, or two stacks share a slug.
    """
    slugs = [to_stack_slug(stack) for stack in stacks]
    if ALL in slugs:
        raise ValueError(
            f"stack name {ALL!r} is reserved for the cdk-*-{ALL} tasks, rename the stack"
        )
    if len(set(slugs)) != len(slugs):
        raise ValueError(f"duplicate stack name in {stacks}")


def get_stack_targets(env_name: str) -> dict[str, StackTarget]:
    """
    Every stack of one environment, by entry name, in creation order.
    Loads the config of that environment; makes no AWS call.
    """
    one = One()
    one.config = Config.load_from_local_config_file(env_name=env_name)
    stack_ctx_enum = StackCtxEnum(one=one)
    return {
        stack: StackTarget(
            construct_id=stack_ctx.construct_id,
            console_url=one.config.get_cft_stack_url(stack_ctx.stack_name),
        )
        for stack, stack_ctx in zip(
            list_entry_names(StackCtxEnum),
            stack_ctx_enum.get_all(),
        )
    }


def get_task_name(
    action_name: str,
    env_name: str,
    stack_slug: str,
) -> str:
    """
    ``cdk-<action>-<env>-all``, or ``cdk-<action>-<env>-<stack>-stack`` for one stack.
    """
    if stack_slug == ALL:
        return f"cdk-{action_name}-{env_name}-{ALL}"
    return f"cdk-{action_name}-{env_name}-{stack_slug}-stack"


def get_cdk_command(
    action: CdkAction,
    env_name: str,
    construct_id: str | None,
) -> str:
    """
    The cdk command line of a task.

    :param construct_id: the stack to act on, or ``None`` for every stack.
    """
    parts = ["cdk", action.sub_command]
    if construct_id is None:
        parts.append(action.all_option)
    else:
        parts.extend([construct_id, "--exclusively"])
    parts.append(action.options)
    if action.use_profile:
        parts.append(f"--profile {{{{env.{get_aws_profile_env_var(env_name)}}}}}")
    return " ".join(part for part in parts if part)


def get_run_script(
    action: CdkAction,
    env_name: str,
    targets: list[StackTarget],
    construct_id: str | None,
) -> str:
    """
    The script of a task: the console URL of each stack in ``targets``, then the
    cdk command, printed and run.
    """
    command = get_cdk_command(action, env_name, construct_id)
    lines = ["echo '--- CloudFormation console ---'"]
    for target in targets:
        lines.append(f"echo '{target.construct_id}: {target.console_url}'")
    lines.append("echo '--- Run command ---'")
    lines.append(f"echo '{command}'")
    lines.append(command)
    return "\n".join(lines)


def get_banner(task_name: str, summary: str) -> str:
    """
    The first line of every generated step task: ``>>> <task>: <what it does>``.
    A chain task runs its steps one after another, so its output reads as a
    list of these lines, each followed by that step's own output.
    """
    return f"echo '>>> {task_name}: {summary}'"


def _render_task(
    action: CdkAction,
    env_name: str,
    stack_slug: str,
    targets: list[StackTarget],
) -> str:
    if stack_slug == ALL:
        construct_id = None
        target = "all stacks"
    else:
        construct_id = targets[0].construct_id
        target = f"stack {stack_slug}"
    summary = action.summary.format(target=target, env=env_name)
    task_name = get_task_name(action.name, env_name, stack_slug)
    script = get_banner(task_name, summary) + "\n"
    script += get_run_script(action, env_name, targets, construct_id)
    lines = [
        f'[tasks."{task_name}"]',
        f'description = "{action.emoji} {summary}"',
        'dir = "cdk"',
        f'env = {{ {ENV_NAME_VAR} = "{env_name}" }}',
        'depends = ["inst"]',
        f'run = """\n{script}\n"""',
    ]
    return "\n".join(lines)


def render_env_tasks_block(
    env_stack_targets: dict[str, dict[str, StackTarget]],
    env_extra_tasks: dict[str, str] | None = None,
    tail_tasks: list[str] | None = None,
) -> str:
    """
    Render the whole generated block, markers included.

    :param env_stack_targets: for each environment, its stacks by entry name (see
        :func:`get_stack_targets`). Tasks follow its order: by environment, its
        extra tasks, then the ``all`` tasks, then each stack.
    :param env_extra_tasks: for each environment, other tasks already rendered,
        placed before its cdk tasks.
    :param tail_tasks: tasks already rendered, placed last.

    :raises ValueError: see :func:`validate_stacks`.
    """
    env_extra_tasks = env_extra_tasks or {}
    parts = [
        f"{BEGIN_MARKER}\n# Generated by `mise run gen-env-tasks`. Do not edit by hand."
    ]
    for env_name, stack_targets in env_stack_targets.items():
        validate_stacks(list(stack_targets))
        if env_name in env_extra_tasks:
            parts.append(env_extra_tasks[env_name])
        groups = [(ALL, list(stack_targets.values()))]
        for stack, target in stack_targets.items():
            groups.append((to_stack_slug(stack), [target]))
        for stack_slug, targets in groups:
            for action in CDK_ACTIONS:
                parts.append(_render_task(action, env_name, stack_slug, targets))
    parts.extend(tail_tasks or [])
    parts.append(END_MARKER)
    return "\n\n".join(parts)


def print_cdk_stack_urls() -> None:
    """
    Print the console URL of every stack in every environment
    (``mise run print-cdk-stack-urls``). It never raises: an environment whose
    stacks cannot be worked out, such as one without its ``-secret`` config file,
    prints one error line, and the others are still printed.
    """
    for member in EnvNameEnum:
        env_name = member.value
        print(f"--- {env_name} ---")
        try:
            targets = get_stack_targets(env_name)
        except Exception as e:
            print(
                f"ERROR: cannot work out the stacks of {env_name!r}: "
                f"{type(e).__name__}: {e}"
            )
            continue
        for target in targets.values():
            print(f"{target.construct_id}: {target.console_url}")


def replace_env_tasks_block(text: str, block: str) -> str:
    """
    Replace the generated block in the ``mise.toml`` text, markers included.

    :param text: the content of ``mise.toml``.
    :param block: the new block, from :func:`render_env_tasks_block`.

    :raises ValueError: the markers are missing, or the end marker comes first.
    """
    begin = text.find(BEGIN_MARKER)
    end = text.find(END_MARKER)
    if begin == -1 or end == -1 or end < begin:
        raise ValueError(
            f"mise.toml must contain the lines {BEGIN_MARKER!r} and {END_MARKER!r}, in this order"
        )
    end = end + len(END_MARKER)
    return text[:begin] + block + text[end:]


def update_mise_toml(
    path: Path,
    block: str,
) -> bool:
    """
    Rewrite the generated block of the ``mise.toml`` at ``path``.

    :param block: the new block, such as :func:`render_project_env_tasks`.

    :returns: ``True`` if the file changed, ``False`` if it was already up to date.
    """
    text = path.read_text(encoding="utf-8")
    new_text = replace_env_tasks_block(text, block)
    if new_text == text:
        return False
    path.write_text(new_text, encoding="utf-8")
    return True
