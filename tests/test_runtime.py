# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.runtime import RuntimeNameEnum
from cookiecutter_aws_agentcore_runtime_basic_demo.runtime import Runtime
from cookiecutter_aws_agentcore_runtime_basic_demo.runtime import runtime

import pytest

# The signals are written out, not taken from constants.py: they are a contract
# with agentcore.json and the AgentCore CLI, and a renamed constant must fail here.
SIGNALS = ["CI", "IS_AGENTCORE_RUNTIME", "LOCAL_DEV"]


@pytest.mark.parametrize(
    "env_vars,expected",
    [
        ({}, RuntimeNameEnum.local),
        ({"CI": "true"}, RuntimeNameEnum.ci),
        # only the presence of CI counts
        ({"CI": ""}, RuntimeNameEnum.ci),
        ({"IS_AGENTCORE_RUNTIME": "true"}, RuntimeNameEnum.agentcore),
        (
            {"IS_AGENTCORE_RUNTIME": "true", "LOCAL_DEV": "1"},
            RuntimeNameEnum.agentcore_local,
        ),
        # only the presence of LOCAL_DEV counts
        (
            {"IS_AGENTCORE_RUNTIME": "true", "LOCAL_DEV": ""},
            RuntimeNameEnum.agentcore_local,
        ),
        # an AgentCore runtime wins over CI
        ({"IS_AGENTCORE_RUNTIME": "true", "CI": "true"}, RuntimeNameEnum.agentcore),
        # only "true" counts
        ({"IS_AGENTCORE_RUNTIME": "false"}, RuntimeNameEnum.local),
        ({"IS_AGENTCORE_RUNTIME": "True"}, RuntimeNameEnum.local),
        # LOCAL_DEV alone is not an AgentCore runtime
        ({"LOCAL_DEV": "1"}, RuntimeNameEnum.local),
    ],
)
def test_get_current_runtime_name(monkeypatch, env_vars, expected):
    for name in SIGNALS:
        monkeypatch.delenv(name, raising=False)
    for name, value in env_vars.items():
        monkeypatch.setenv(name, value)
    runtime = Runtime()
    assert runtime.get_current_runtime_name() is expected
    assert runtime.current_runtime_name() == expected.value


def test_current_runtime_name_is_not_cached(monkeypatch):
    for name in SIGNALS:
        monkeypatch.delenv(name, raising=False)
    assert runtime.current_runtime_name() == "local"
    monkeypatch.setenv("CI", "true")
    assert runtime.current_runtime_name() == "ci"


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.runtime",
        preview=False,
    )
