# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.paths import path_enum
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.mise_tasks import (
    render_project_env_tasks,
)


def test_mise_toml_is_up_to_date():
    """
    ``mise.toml`` holds the tasks of exactly the stacks of StackCtxEnum, and the
    config and AgentCore tasks, of every environment. If this fails, run
    ``mise run gen-env-tasks``.
    """
    text = path_enum.path_mise_toml.read_text(encoding="utf-8")
    assert render_project_env_tasks() in text


def test_chains():
    """
    The deploy chain runs config, the agentcore-deps stack, then the runtimes;
    the teardown chain the reverse, after a confirmation; every step prints a
    banner first.
    """
    import tomllib

    tasks = tomllib.loads(path_enum.path_mise_toml.read_text(encoding="utf-8"))["tasks"]
    up = tasks["ac-chain-up-dev"]
    assert [item["task"] for item in up["run"] if isinstance(item, dict)] == [
        "config-deploy-dev",
        "cdk-up-dev-agentcore-deps-stack",
        "ac-deploy-dev",
    ]
    down = tasks["ac-chain-down-dev"]
    assert [item["task"] for item in down["run"] if isinstance(item, dict)] == [
        "ac-down-dev",
        "cdk-down-dev-agentcore-deps-stack",
        "config-delete-dev",
    ]
    # the teardown chain asks yes/no once before its first step, then tells its
    # steps not to ask again; never mise's `confirm`, which takes Enter as yes
    assert "confirm" not in down
    assert "raw" not in down
    assert down["env"] == {"CONFIRMED_BY_CHAIN": "true"}
    first_task = next(i for i, item in enumerate(down["run"]) if isinstance(item, dict))
    question = down["run"][first_task - 1]
    assert question.startswith(".venv/bin/python .mise/tasks/confirm.py --action ")
    assert "CONFIRMED_BY_CHAIN" not in question
    assert not any("confirm.py" in str(item) for item in up["run"])
    # destructive steps ask on their own, unless a chain asked already
    for name in ["ac-down-dev", "config-delete-dev"]:
        assert "raw" not in tasks[name]
        assert (
            "--skip_var CONFIRM_YES --skip_var CONFIRMED_BY_CHAIN" in tasks[name]["run"]
        )
    for name in [
        "config-deploy-dev",
        "ac-deploy-dev",
        "cdk-down-dev-agentcore-deps-stack",
    ]:
        assert "confirm.py" not in tasks[name]["run"]
    for name in [
        "config-deploy-dev",
        "ac-deploy-dev",
        "ac-down-dev",
        "cdk-up-dev-agentcore-deps-stack",
    ]:
        assert tasks[name]["run"].strip().startswith(f"echo '>>> {name}: ")
    # ac-deploy does not deploy the config itself; the chain does
    assert tasks["ac-deploy-dev"]["depends"] == ["inst"]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_unit_test

    run_unit_test(__file__)
