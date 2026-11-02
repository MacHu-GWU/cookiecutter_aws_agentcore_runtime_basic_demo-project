# -*- coding: utf-8 -*-

"""
The alerts stack, the single-file form of a stack: an SNS topic that other stacks
publish alerts to, and the log level of the environment in SSM.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import aws_sns as sns
from aws_cdk import aws_ssm as ssm
from constructs import Construct

from ...config.api import Config


class AlertsStack(cdk.Stack):
    """
    Takes the standard arguments of :meth:`cdk_mate.stack_ctx.StackCtx.to_stack_kwargs`
    plus the config of its environment; every name comes from the config.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        stack_name: str,
        env: cdk.Environment,
        config: Config,
    ) -> None:
        super().__init__(
            scope=scope,
            id=id,
            stack_name=stack_name,
            env=env,
        )
        self.config = config
        self.s01_create_sns_topic()
        self.s02_create_ssm_parameter()
        self.s03_create_outputs()

    def s01_create_sns_topic(self) -> None:
        """
        Create the alert topic. Other stacks receive it as an argument, see
        :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.publisher_stack.stack.PublisherStack`.
        """
        self.alert_topic = sns.Topic(
            self,
            "AlertTopic",
            topic_name=self.config.sns_topic_name_alerts,
        )

    def s02_create_ssm_parameter(self) -> None:
        """
        Create the log level parameter; its value differs per environment.
        """
        self.log_level_parameter = ssm.StringParameter(
            self,
            "LogLevelParameter",
            parameter_name=self.config.ssm_param_name_log_level,
            string_value=self.config.log_level,
        )

    def s03_create_outputs(self) -> None:
        """
        Export the values other projects may use. Each output has a property in
        :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.alerts_stack_exports`.
        """
        self.output_alert_topic_arn = cdk.CfnOutput(
            self,
            "AlertTopicArn",
            value=self.alert_topic.topic_arn,
            export_name=self.config.cft_export_name_alert_topic_arn,
        )
