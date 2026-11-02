# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.config.config_01_name import ConfigNameMixin

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
    # ssm
    assert config.ssm_param_name_log_level == "/my-project-dev/log-level"
    assert config.ssm_param_arn_log_level == "arn:aws:ssm:us-east-1:111122223333:parameter/my-project-dev/log-level"
    assert "/parameters/my-project-dev/log-level/" in config.ssm_param_url_log_level
    assert config.ssm_param_name_alert_topic_arn == "/my-project-dev/alert-topic-arn"
    assert config.ssm_param_arn_alert_topic_arn == "arn:aws:ssm:us-east-1:111122223333:parameter/my-project-dev/alert-topic-arn"
    assert "/parameters/my-project-dev/alert-topic-arn/" in config.ssm_param_url_alert_topic_arn
    # fmt: on


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.config.config_01_name",
        preview=False,
    )
