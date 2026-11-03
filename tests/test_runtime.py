# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtime import RuntimeNameEnum
from cookiecutter_aws_agentcore_runtime_basic_demo.runtime import Runtime

import pytest


@pytest.mark.parametrize(
    "env_vars,expected",
    [
        ({}, RuntimeNameEnum.local),
        ({"CI": "true"}, RuntimeNameEnum.ci),
        ({"IS_AGENTCORE_RUNTIME": "true"}, RuntimeNameEnum.agentcore),
        (
            {"IS_AGENTCORE_RUNTIME": "true", "LOCAL_DEV": "1"},
            RuntimeNameEnum.agentcore_local,
        ),
        # an AgentCore runtime wins over CI; only "true" counts
        ({"IS_AGENTCORE_RUNTIME": "true", "CI": "true"}, RuntimeNameEnum.agentcore),
        ({"IS_AGENTCORE_RUNTIME": "false"}, RuntimeNameEnum.local),
        # LOCAL_DEV alone is not an AgentCore runtime
        ({"LOCAL_DEV": "1"}, RuntimeNameEnum.local),
    ],
)
def test_get_current_runtime_name(monkeypatch, env_vars, expected):
    for name in ["CI", "IS_AGENTCORE_RUNTIME", "LOCAL_DEV"]:
        monkeypatch.delenv(name, raising=False)
    for name, value in env_vars.items():
        monkeypatch.setenv(name, value)
    runtime = Runtime()
    assert runtime.get_current_runtime_name() is expected
    assert runtime.current_runtime_name() == expected.value


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtime",
        preview=False,
    )
