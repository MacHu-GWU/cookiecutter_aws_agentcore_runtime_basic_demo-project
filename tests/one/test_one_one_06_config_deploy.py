# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_06_config_deploy import (
    deploy_config,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_06_config_deploy import (
    delete_config,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_06_config_deploy import (
    OneConfigDeployMixin,
)

import moto
import boto3

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One


def test_deploy_and_delete_config(config: Config, capsys):
    """
    The parameter is written only when the config changed, so an unchanged
    deploy adds no version; each call prints its status and the console URL.
    """
    with moto.mock_aws():
        one = One()
        assert isinstance(one, OneConfigDeployMixin)
        one.config = config
        one.ssm_client = boto3.client("ssm", region_name="us-east-1")

        assert one.deploy_config() == "created"
        assert one.deploy_config() == "unchanged"
        out = capsys.readouterr().out
        assert "Config of 'dev' created (version 1, " in out
        assert "Config of 'dev' unchanged (version 1, nothing written, " in out
        assert config.ssm_param_url_config in out

        one.config = config.model_copy(update={"log_level": "INFO"})
        assert one.deploy_config() == "updated"
        assert "updated (version 1 -> 2, " in capsys.readouterr().out
        response = one.ssm_client.get_parameter(
            Name=config.ssm_param_name_config,
            WithDecryption=True,
        )
        assert response["Parameter"]["Type"] == "SecureString"
        value = response["Parameter"]["Value"]
        assert Config.model_validate_json(value).log_level == "INFO"

        assert one.delete_config() is True
        assert one.delete_config() is False
        out = capsys.readouterr().out
        assert "Config of 'dev' deleted: " in out
        assert "Config of 'dev' not found, nothing deleted: " in out

        # Any environment, with its config and client given.
        prd_config = Config.load_from_local_config_file(env_name="prd")
        assert deploy_config(config=prd_config, ssm_client=one.ssm_client) == "created"
        assert "Config of 'prd' created (version 1, " in capsys.readouterr().out
        assert delete_config(config=prd_config, ssm_client=one.ssm_client) is True


def test_deployed_config_loads_back(config: Config):
    """
    What :func:`deploy_config` writes is what an AgentCore runtime reads back.
    """
    with moto.mock_aws():
        ssm_client = boto3.client("ssm", region_name="us-east-1")
        deploy_config(config=config, ssm_client=ssm_client)
        loaded = Config.load_from_ssm(
            ssm_client=ssm_client,
            name=config.ssm_param_name_config,
        )
        assert loaded == config


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_06_config_deploy",
        preview=False,
    )
