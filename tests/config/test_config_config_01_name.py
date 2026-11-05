# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.config.config_01_name import (
    ConfigNameMixin,
)

import pytest

from cookiecutter_aws_agentcore_runtime_basic_demo.env import EnvNameEnum
from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config


def test_names(config: Config):
    """
    Every resource name, so a rename that would break what depends on it fails here.
    One name per line, kept unwrapped by ``fmt: off``, so the list reads like a table.
    """
    assert isinstance(config, ConfigNameMixin)
    # fmt: off
    # prefixes
    assert config.project_name_snake == "my_project"
    assert config.project_name_slug == "my-project"
    assert config.prefix_name_slug == "my-project-dev"
    # stacks
    assert config.cft_stack_name_alerts == "my-project-dev-alerts"
    assert config.cft_stack_name_publisher == "my-project-dev-publisher"
    assert config.cft_stack_name_agentcore_deps == "my-project-dev-agentcore-deps"
    assert "filteringText=my-project-dev-agentcore-deps&" in config.cft_stack_url_agentcore_deps
    assert config.cft_stack_url_alerts == "https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=my-project-dev-alerts&filteringStatus=active&viewNested=true"
    assert config.cft_stack_url_publisher == "https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=my-project-dev-publisher&filteringStatus=active&viewNested=true"
    # exports
    assert config.cft_export_name_alert_topic_arn == "my-project-dev-alert-topic-arn"
    assert config.cft_export_name_publisher_role_arn == "my-project-dev-publisher-role-arn"
    # sns
    assert config.sns_topic_name_alerts == "my-project-dev-alerts"
    assert config.sns_topic_arn_alerts == "arn:aws:sns:us-east-1:111122223333:my-project-dev-alerts"
    # iam
    assert config.iam_role_name_publisher == "my-project-dev-publisher"
    assert config.iam_role_arn_publisher == "arn:aws:iam::111122223333:role/my-project-dev-publisher"
    # iam policies
    assert config.iam_policy_name_agentcore_runtime == "my-project-dev-us-east-1-agentcore-runtime"
    assert config.iam_policy_arn_agentcore_runtime == "arn:aws:iam::111122223333:policy/my-project-dev-us-east-1-agentcore-runtime"
    assert config.iam_policy_url_agentcore_runtime == "https://us-east-1.console.aws.amazon.com/iam/home#/policies/details/arn%3Aaws%3Aiam%3A%3A111122223333%3Apolicy%2Fmy-project-dev-us-east-1-agentcore-runtime"
    # ssm
    assert config.ssm_param_name_config == "/my-project-dev/config"
    assert config.ssm_param_arn_config == "arn:aws:ssm:us-east-1:111122223333:parameter/my-project-dev/config"
    assert "/parameters/my-project-dev/config/" in config.ssm_param_url_config
    assert config.ssm_param_name_log_level == "/my-project-dev/log-level"
    assert config.ssm_param_arn_log_level == "arn:aws:ssm:us-east-1:111122223333:parameter/my-project-dev/log-level"
    assert "/parameters/my-project-dev/log-level/" in config.ssm_param_url_log_level
    assert config.ssm_param_name_alert_topic_arn == "/my-project-dev/alert-topic-arn"
    assert config.ssm_param_arn_alert_topic_arn == "arn:aws:ssm:us-east-1:111122223333:parameter/my-project-dev/alert-topic-arn"
    assert "/parameters/my-project-dev/alert-topic-arn/" in config.ssm_param_url_alert_topic_arn
    # agentcore
    assert config.cft_stack_name_agentcore == "AgentCore-MyProject-dev"
    assert config.cft_stack_url_agentcore == "https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/stackinfo?filteringText=AgentCore-MyProject-dev&filteringStatus=active&viewNested=true"
    assert config.agentcore_target_name == "dev"
    assert config.agentcore_runtime_name_power_plant_mcp == "PowerPlantMcp"
    assert config.agentcore_runtime_physical_name_power_plant_mcp == "MyProject_dev_PowerPlantMcp"
    assert config.agentcore_runtime_name_site_agent == "SiteAgent"
    assert config.agentcore_runtime_physical_name_site_agent == "MyProject_dev_SiteAgent"
    # urls of what is named at deploy time
    assert config.get_agentcore_runtime_url("MyProject_dev_SiteAgent-abc") == "https://us-east-1.console.aws.amazon.com/bedrock-agentcore/agents/MyProject_dev_SiteAgent-abc"
    assert config.get_iam_role_url("my-role") == "https://us-east-1.console.aws.amazon.com/iam/home?region=us-east-1#/roles/details/my-role"
    assert config.get_cloudwatch_log_group_url("/aws/x-DEFAULT") == "https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Fx-DEFAULT"
    # fmt: on


def test_agentcore_runtime_physical_name_too_long(config: Config):
    with pytest.raises(ValueError, match="longer than 48 characters"):
        config.get_agentcore_runtime_physical_name("X" * 40)


@pytest.mark.parametrize("env_name", [env_name.value for env_name in EnvNameEnum])
def test_agentcore_runtime_physical_names_fit(env_name: str):
    """
    With the committed config files, every runtime's physical name fits the
    48 characters AgentCore allows, in every environment.
    """
    config = Config.load_from_local_config_file(env_name=env_name)
    prefix = "agentcore_runtime_physical_name_"
    names = [name for name in dir(type(config)) if name.startswith(prefix)]
    assert names
    for name in names:
        assert len(getattr(config, name)) <= 48


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.config.config_01_name",
        preview=False,
    )
