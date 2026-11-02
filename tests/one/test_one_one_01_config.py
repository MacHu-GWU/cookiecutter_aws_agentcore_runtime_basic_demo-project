# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_01_config import OneConfigMixin

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One


def test_config():
    one = One()
    assert isinstance(one, OneConfigMixin)
    assert isinstance(one.config, Config)
    assert one.config.project_name == "cookiecutter_aws_agentcore_runtime_basic_demo"
    assert one.config.env_name == one.env.current_env_name
    # cached: built once
    assert one.config is one.config


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_01_config",
        preview=False,
    )
