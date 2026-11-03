# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_04_devops import (
    deploy_config,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_04_devops import (
    delete_config,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_04_devops import (
    check_agentcore_deps,
)

import json

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


def test_check_agentcore_deps(config: Config, capsys):
    # the policy ARN has the account ID in it, so use the account of moto
    data = config.model_dump()
    data["aws_account_id"] = moto.core.DEFAULT_ACCOUNT_ID
    config = Config(**data)
    with moto.mock_aws():
        one = One()
        one.config = config
        one.iam_client = boto3.client("iam", region_name="us-east-1")
        assert one.check_agentcore_deps() is False
        assert "cdk-up-dev-agentcore-deps-stack" in capsys.readouterr().out
        one.iam_client.create_policy(
            PolicyName=config.iam_policy_name_agentcore_runtime,
            PolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": "ssm:GetParameter",
                            "Resource": "*",
                        }
                    ],
                }
            ),
        )
        assert check_agentcore_deps(config=config, iam_client=one.iam_client) is True


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_04_devops",
        preview=False,
    )
