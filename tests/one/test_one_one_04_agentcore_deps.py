# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_04_agentcore_deps import (
    check_agentcore_deps,
)

import json

import moto
import boto3

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One


def test_check_agentcore_deps(config: Config, capsys):
    # the policy ARN has the account ID in it, so use the account of moto
    data = config.model_dump()
    data["aws_account_id"] = moto.core.DEFAULT_ACCOUNT_ID
    config = Config(**data)
    with moto.mock_aws():
        one = One()
        one.config = config
        one.iam_client = boto3.client("iam", region_name="us-east-1")
        one.ssm_client = boto3.client("ssm", region_name="us-east-1")
        # neither exists
        assert one.check_agentcore_deps() is False
        out = capsys.readouterr().out
        assert "cdk-up-dev-agentcore-deps-stack" in out
        assert "config-deploy-dev" in out
        # only the policy exists
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
        assert one.check_agentcore_deps() is False
        assert "config-deploy-dev" in capsys.readouterr().out
        # both exist
        one.deploy_config()
        assert (
            check_agentcore_deps(
                config=config,
                iam_client=one.iam_client,
                ssm_client=one.ssm_client,
            )
            is True
        )


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_04_agentcore_deps",
        preview=False,
    )
