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


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_unit_test

    run_unit_test(__file__)
