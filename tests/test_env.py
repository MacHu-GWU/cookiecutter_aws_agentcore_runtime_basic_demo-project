# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.env import ENV_NAME_VAR
from cookiecutter_aws_agentcore_runtime_basic_demo.env import EnvNameEnum
from cookiecutter_aws_agentcore_runtime_basic_demo.env import Env

import pytest


class TestEnv:
    @pytest.mark.parametrize(
        "value,expected",
        [
            (None, EnvNameEnum.dev),
            ("", EnvNameEnum.dev),
            ("prd", EnvNameEnum.prd),
        ],
    )
    def test_get_current_env_name(self, monkeypatch, value, expected):
        if value is None:
            monkeypatch.delenv(ENV_NAME_VAR, raising=False)
        else:
            monkeypatch.setenv(ENV_NAME_VAR, value)
        env = Env()
        assert env.get_current_env_name() is expected
        assert env.current_env_name == expected.value

    def test_get_current_env_name_error(self, monkeypatch):
        monkeypatch.setenv(ENV_NAME_VAR, "qa")
        with pytest.raises(ValueError):
            Env().get_current_env_name()


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.env",
        preview=False,
    )
