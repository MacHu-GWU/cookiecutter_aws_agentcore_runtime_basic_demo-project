# -*- coding: utf-8 -*-

"""
Generate the AgentCore tasks of each environment, written into the
``<env-tasks>`` block of ``mise.toml`` by ``mise run gen-env-tasks`` next to the
``cdk-*`` tasks of :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.mise_tasks`.

Per environment ``<env>``:

- Step tasks: ``config-deploy-<env>`` and ``config-delete-<env>`` (the config in
  SSM), ``ac-deploy-<env>`` and ``ac-down-<env>`` (the runtimes),
  ``ac-status-<env>`` (what is deployed), and per runtime of the registry
  ``ac-invoke-<env>-<slug>`` (its sample payload, sent to the deployed runtime)
  and ``ac-logs-<env>-<slug>`` (its recent logs).
- Chains, which run step tasks in order and stop at the first that fails:
  ``ac-chain-up-<env>`` (config, the ``agentcore_deps`` stack, the runtimes),
  ``ac-chain-down-<env>`` (the reverse, after one yes/no question), and
  ``ac-test-<env>`` (status, then every runtime invoked once).

Then ``config-deploy-all`` and ``config-delete-all``, and per runtime, for a
developer machine: ``ac-local-<slug>``, ``ac-dev-<slug>``, and
``ac-local-<slug>-call`` (:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.devtools.local_run`).
Nothing here calls AWS.
"""

from __future__ import annotations

import json
import dataclasses

from ..env import ENV_NAME_VAR
from ..env import EnvNameEnum
from ..confirm import CONFIRM_YES_VAR
from ..confirm import CONFIRMED_BY_CHAIN_VAR
from ..config.api import Config
from ..one.one_02_boto_ses import get_aws_profile_env_var
from ..cdk.mise_tasks import CDK_ACTIONS
from ..cdk.mise_tasks import StackTarget
from ..cdk.mise_tasks import get_banner
from ..cdk.mise_tasks import get_task_name
from ..cdk.mise_tasks import get_stack_targets
from ..cdk.mise_tasks import render_env_tasks_block
from ..cdk.mise_tasks import to_stack_slug
from .registry import RuntimeSpec
from .registry import RuntimeProtocolEnum
from .registry import get_runtime_specs

ALL = "all"
"""
The environment part of the ``config-<action>-all`` tasks.
"""

CONFIG_ACTIONS = ["deploy", "delete"]
"""
The ``config-<action>-<env>`` tasks, each runs ``.mise/tasks/config-<action>.py``.
"""

SESSION_ID_VAR = "SESSION_ID"
"""
Set it to pass ``--session-id`` to ``agentcore invoke``, such as
``SESSION_ID=<id> mise run ac-invoke-dev-<slug>``: the same ID continues the
same runtime session.
"""

SINCE_VAR = "SINCE"
"""
Set it to change how far back ``ac-logs-<env>-<slug>`` searches, such as
``SINCE=2h``; the default is :data:`DEFAULT_SINCE`.
"""

DEFAULT_SINCE = "30m"

DEPLOYED_STATE_REMINDER = (
    "echo 'Commit agentcore/.cli/deployed-state.json if it changed: "
    "everyone who deploys shares it'"
)
"""
The last line of ``ac-deploy-<env>`` and ``ac-down-<env>``.
"""


def get_config_task_name(action: str, env_name: str) -> str:
    """
    ``config-<action>-<env>``, or ``config-<action>-all`` for :data:`ALL`.
    """
    return f"config-{action}-{env_name}"


@dataclasses.dataclass(frozen=True)
class EnvStep:
    """
    One step task of an environment, also a link of a chain task.
    """

    # fmt: off
    name: str = dataclasses.field()  #: The task name, such as ``config-deploy-dev``.
    emoji: str = dataclasses.field()  #: Shown in front of the description.
    summary: str = dataclasses.field()  #: What it does; the description and the banner. No single quote.
    script: str = dataclasses.field(default="")  #: The commands after the banner; empty for a cdk task, rendered elsewhere.
    confirm: str | None = dataclasses.field(default=None)  #: If set, the yes/no question asked before the script (``confirm.py``). No single quote.
    # fmt: on


def get_cdk_step(action_name: str, env_name: str, stack_slug: str) -> EnvStep:
    """
    The ``cdk-<action>-<env>-<stack>-stack`` task as a chain link, with the
    summary its own banner prints.
    """
    action = {action.name: action for action in CDK_ACTIONS}[action_name]
    return EnvStep(
        name=get_task_name(action.name, env_name, stack_slug),
        emoji=action.emoji,
        summary=action.summary.format(target=f"stack {stack_slug}", env=env_name),
    )


def get_agentcore_target(env_name: str) -> StackTarget:
    """
    The AgentCore stack of one environment, with the AgentCore CLI target name
    as its construct ID. Loads the config of that environment; makes no AWS call.
    """
    config = Config.load_from_local_config_file(env_name=env_name)
    return StackTarget(
        construct_id=config.agentcore_target_name,
        console_url=config.cft_stack_url_agentcore,
    )


def get_agentcore_command(env_name: str, args: str) -> str:
    """
    ``agentcore <args>`` with the AWS profile of the environment.
    """
    profile_var = get_aws_profile_env_var(env_name)
    return f"AWS_PROFILE={{{{env.{profile_var}}}}} agentcore {args}"


def get_invoke_script(spec: RuntimeSpec, target_name: str, env_name: str) -> list[str]:
    """
    The script lines that run ``agentcore invoke`` of the deployed runtime
    ``spec`` with its sample payload, and ``--session-id $SESSION_ID`` when
    that is set: the payload goes into a shell variable first, so the command
    can be printed and run without nested quotes. For an MCP runtime the payload
    is a whole JSON-RPC request, and its method and tool name are passed too.

    :raises ValueError: the payload has a single quote, which the shell quoting
        cannot hold.
    """
    payload = json.dumps(spec.sample_payload)
    if "'" in payload:
        raise ValueError(f"the sample payload of {spec.name} has a single quote")
    args = f"invoke --target {target_name} --runtime {spec.name}"
    if spec.protocol == RuntimeProtocolEnum.MCP:
        args += f" --mcp-method {spec.sample_payload['method']}"
        tool_name = spec.sample_payload.get("params", {}).get("name")
        if tool_name:
            args += f" --mcp-name {tool_name}"
    command = get_agentcore_command(env_name, args)
    session = f"${{{SESSION_ID_VAR}:+--session-id ${SESSION_ID_VAR}}}"
    return [
        f"PAYLOAD='{payload}'",
        "echo '--- Run command ---'",
        f"echo \"{command} --payload '$PAYLOAD' {session}\"",
        f'{command} --payload "$PAYLOAD" {session}',
    ]


def _run_command(command: str) -> list[str]:
    return ["echo '--- Run command ---'", f"echo '{command}'", command]


def get_env_steps(
    env_name: str,
    agentcore_target: StackTarget,
    runtime_specs: list[RuntimeSpec],
) -> dict[str, EnvStep]:
    """
    The AgentCore step tasks of one environment, by role (one ``invoke:<slug>``
    per runtime), plus the two ``cdk-*`` tasks of the ``agentcore_deps`` stack
    the chains use (rendered with the other cdk tasks).
    """
    target_name = agentcore_target.construct_id
    deploy_command = get_agentcore_command(env_name, f"deploy --target {target_name}")
    down_command = f"{deploy_command} --yes"
    status_command = get_agentcore_command(env_name, f"status --target {target_name}")
    gen = ".venv/bin/python .mise/tasks/ac-gen.py"
    console = [
        "echo '--- CloudFormation console ---'",
        f"echo 'AgentCore stack: {agentcore_target.console_url}'",
    ]
    deps_slug = to_stack_slug("agentcore_deps")
    steps = {
        "config_deploy": EnvStep(
            name=get_config_task_name("deploy", env_name),
            emoji="⚙️",
            summary=f"Deploy the config of {env_name} to SSM Parameter Store, if it changed (writes to AWS)",
            script=".venv/bin/python .mise/tasks/config-deploy.py",
        ),
        "config_delete": EnvStep(
            name=get_config_task_name("delete", env_name),
            emoji="🗑️",
            summary=f"Delete the config of {env_name} from SSM Parameter Store (writes to AWS)",
            script=".venv/bin/python .mise/tasks/config-delete.py",
            confirm=f"Delete the config parameter of {env_name}?",
        ),
        "deps_up": get_cdk_step("up", env_name, deps_slug),
        "deps_down": get_cdk_step("down", env_name, deps_slug),
        "ac_deploy": EnvStep(
            name=f"ac-deploy-{env_name}",
            emoji="🚀",
            summary=(
                f"Deploy every AgentCore runtime to the {target_name} target: check that the "
                f"agentcore-deps policy and the config exist, generate the project for "
                f"{env_name}, check the wheels, deploy (writes to AWS)"
            ),
            script="\n".join(
                [
                    *console,
                    ".venv/bin/python .mise/tasks/ac-check-deps.py",
                    gen,
                    ".venv/bin/python .mise/tasks/ac-check-wheels.py",
                    *_run_command(deploy_command),
                    DEPLOYED_STATE_REMINDER,
                ]
            ),
        ),
        "ac_down": EnvStep(
            name=f"ac-down-{env_name}",
            emoji="🔴",
            summary=(
                f"Destroy every AgentCore runtime of the {target_name} target: deploy an "
                f"empty project with --yes, then generate the real one again, even if the "
                f"deploy fails (writes to AWS; keeps the agentcore-deps stack and the config)"
            ),
            confirm=f"Destroy every AgentCore runtime of {env_name}?",
            script="\n".join(
                [
                    *console,
                    ".venv/bin/python .mise/tasks/ac-gen-teardown.py",
                    # restore the real project when the task ends, failed or not
                    f"trap '{gen}' EXIT",
                    *_run_command(down_command),
                    DEPLOYED_STATE_REMINDER,
                ]
            ),
        ),
        "ac_status": EnvStep(
            name=f"ac-status-{env_name}",
            emoji="🔎",
            summary=f"Show the deployed AgentCore runtimes of the {target_name} target (reads AWS)",
            script="\n".join([*console, gen, *_run_command(status_command)]),
        ),
    }
    for spec in runtime_specs:
        steps[f"invoke:{spec.slug}"] = EnvStep(
            name=f"ac-invoke-{env_name}-{spec.slug}",
            emoji="🤖",
            summary=(
                f"Invoke the deployed {spec.name} of {env_name} with its sample "
                f"payload; {SESSION_ID_VAR}=<id> continues a session (calls AWS)"
            ),
            script="\n".join([gen, *get_invoke_script(spec, target_name, env_name)]),
        )
        logs_command = get_agentcore_command(
            env_name,
            f"logs runtime --name {spec.name} --target {target_name} "
            f"--since ${{{SINCE_VAR}:-{DEFAULT_SINCE}}}",
        )
        steps[f"logs:{spec.slug}"] = EnvStep(
            name=f"ac-logs-{env_name}-{spec.slug}",
            emoji="📜",
            summary=(
                f"Show the recent logs of the deployed {spec.name} of {env_name}; "
                f"{SINCE_VAR}=2h looks further back (reads AWS)"
            ),
            script="\n".join([gen, *_run_command(logs_command)]),
        )
    return steps


def get_confirm_command(action: str, skip_vars: list[str]) -> str:
    """
    The command that asks yes or no (:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.confirm`)
    and stops the task unless the answer is yes.
    """
    options = "".join(f" --skip_var {var}" for var in skip_vars)
    return f".venv/bin/python .mise/tasks/confirm.py --action '{action}'{options}"


def _render_step(step: EnvStep, env_name: str) -> str:
    script = get_banner(step.name, step.summary) + "\n"
    if step.confirm:
        # a chain that asked already sets CONFIRMED_BY_CHAIN for its steps
        command = get_confirm_command(
            step.confirm, [CONFIRM_YES_VAR, CONFIRMED_BY_CHAIN_VAR]
        )
        script += command + "\n"
    script += step.script
    lines = [
        f'[tasks."{step.name}"]',
        f'description = "{step.emoji} {step.summary}"',
        f'env = {{ {ENV_NAME_VAR} = "{env_name}" }}',
        'depends = ["inst"]',
    ]
    lines.append(f'run = """\n{script}\n"""')
    return "\n".join(lines)


def _render_chain(
    name: str,
    emoji: str,
    summary: str,
    steps: list[EnvStep],
    confirm: str | None = None,
) -> str:
    """
    A task that runs ``steps`` in order, and stops at the first that fails.
    It first prints the whole chain; each step then prints its own banner.
    With ``confirm``, it then asks yes or no before any step
    (:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.confirm`), and its steps
    do not ask again.
    """
    lines = [
        f'[tasks."{name}"]',
        f'description = "{emoji} {summary}: ' + " → ".join(s.name for s in steps) + '"',
    ]
    if confirm:
        # once answered, the steps do not ask again
        lines.append(f'env = {{ {CONFIRMED_BY_CHAIN_VAR} = "true" }}')
    lines.append("run = [")
    lines.append(f"    \"echo '=== {name}: {summary}, in this order ==='\",")
    for i, step in enumerate(steps, start=1):
        lines.append(f"    \"echo '  {i}. {step.name}: {step.summary}'\",")
    if confirm:
        lines.append(f'    "{get_confirm_command(confirm, [CONFIRM_YES_VAR])}",')
    for step in steps:
        lines.append(f'    {{ task = "{step.name}" }},')
    lines.append(f"    \"echo '=== {name}: done ==='\",")
    lines.append("]")
    return "\n".join(lines)


def render_agentcore_env_tasks(
    env_name: str,
    agentcore_target: StackTarget,
    runtime_specs: list[RuntimeSpec],
) -> str:
    """
    The AgentCore tasks of one environment: the step tasks, then the chains.
    ``ac-down-<env>`` and ``config-delete-<env>`` ask on their own when run
    alone; ``CONFIRM_YES=true`` answers every question, such as in CI.
    """
    steps = get_env_steps(env_name, agentcore_target, runtime_specs)
    invoke_steps = [step for key, step in steps.items() if key.startswith("invoke:")]
    parts = [
        _render_step(steps[key], env_name)
        for key in [
            "config_deploy",
            "config_delete",
            "ac_deploy",
            "ac_down",
            "ac_status",
        ]
    ]
    logs_steps = [step for key, step in steps.items() if key.startswith("logs:")]
    parts.extend(_render_step(step, env_name) for step in invoke_steps)
    parts.extend(_render_step(step, env_name) for step in logs_steps)
    parts.append(
        _render_chain(
            name=f"ac-chain-up-{env_name}",
            emoji="🚀",
            summary=f"Deploy everything AgentCore of {env_name}",
            steps=[steps["config_deploy"], steps["deps_up"], steps["ac_deploy"]],
        )
    )
    parts.append(
        _render_chain(
            name=f"ac-chain-down-{env_name}",
            emoji="🔴",
            summary=f"Destroy everything AgentCore of {env_name}",
            steps=[steps["ac_down"], steps["deps_down"], steps["config_delete"]],
            confirm=f"Destroy the AgentCore runtimes, the agentcore-deps stack, and the config of {env_name}?",
        )
    )
    parts.append(
        _render_chain(
            name=f"ac-test-{env_name}",
            emoji="🧪",
            summary=f"Test the deployed AgentCore runtimes of {env_name}",
            steps=[steps["ac_status"], *invoke_steps],
        )
    )
    return "\n\n".join(parts)


def render_config_all_tasks(env_names: list[str]) -> list[str]:
    """
    ``config-deploy-all`` and ``config-delete-all``: the task of every environment.
    """
    parts = []
    for action in CONFIG_ACTIONS:
        depends = [get_config_task_name(action, env_name) for env_name in env_names]
        parts.append(
            "\n".join(
                [
                    f'[tasks."{get_config_task_name(action, ALL)}"]',
                    f'description = "⚙️ Run config-{action}-<env> for every environment (writes to AWS)"',
                    f"depends = {depends}".replace("'", '"'),
                ]
            )
        )
    return parts


def render_runtime_tasks(runtime_specs: list[RuntimeSpec]) -> list[str]:
    """
    The tasks of each runtime on a developer machine, all through
    ``.mise/tasks/ac-run.py``: run it from the repo, run it packaged under
    ``agentcore dev``, and call it on its local port.
    """
    parts = []
    for spec in runtime_specs:
        command = f".venv/bin/python .mise/tasks/ac-run.py --runtime {spec.name}"
        kind = "MCP server" if spec.protocol == RuntimeProtocolEnum.MCP else "agent"
        needs = ""
        if spec.mcp_runtimes:
            needs = "; start its MCP runtimes first: " + ", ".join(spec.mcp_runtimes)
        tasks = [
            (
                f"ac-local-{spec.slug}",
                f"🔌 Run the {spec.name} {kind} from the repo on port {spec.local_port} (Ctrl+C to stop){needs}",
                "local",
                "inst",
            ),
            (
                f"ac-dev-{spec.slug}",
                f"🏗️ Run the packaged {spec.name} with agentcore dev on port {spec.local_port}, config from SSM of ENV_NAME (run config-deploy-<env> first){needs}",
                "dev",
                "ac-gen",
            ),
            (
                f"ac-local-{spec.slug}-call",
                f"📞 Call the local {spec.name} on port {spec.local_port} with its sample payload (start it with ac-local-{spec.slug} or ac-dev-{spec.slug})",
                "call",
                "inst",
            ),
        ]
        for name, description, mode, depends in tasks:
            parts.append(
                "\n".join(
                    [
                        f'[tasks."{name}"]',
                        f'description = "{description}"',
                        f'run = "{command} --mode {mode}"',
                        f'depends = ["{depends}"]',
                    ]
                )
            )
    return parts


def render_project_env_tasks() -> str:
    """
    The whole ``<env-tasks>`` block of this project: for every environment, its
    AgentCore tasks and the ``cdk-*`` tasks of every stack; then the
    ``config-<action>-all`` tasks.
    """
    env_names = [member.value for member in EnvNameEnum]
    env_extra_tasks = {}
    for env_name in env_names:
        config = Config.load_from_local_config_file(env_name=env_name)
        env_extra_tasks[env_name] = render_agentcore_env_tasks(
            env_name=env_name,
            agentcore_target=get_agentcore_target(env_name),
            runtime_specs=get_runtime_specs(config),
        )
    return render_env_tasks_block(
        env_stack_targets={
            env_name: get_stack_targets(env_name) for env_name in env_names
        },
        env_extra_tasks=env_extra_tasks,
        tail_tasks=[
            *render_config_all_tasks(env_names),
            *render_runtime_tasks(
                get_runtime_specs(Config.load_from_local_config_file(env_names[0]))
            ),
        ],
    )
