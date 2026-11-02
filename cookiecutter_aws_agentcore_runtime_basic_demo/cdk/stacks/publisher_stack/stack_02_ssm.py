# -*- coding: utf-8 -*-

"""
The SSM part of :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.publisher_stack.stack.PublisherStack`.
"""

from __future__ import annotations

import typing as T

from aws_cdk import aws_ssm as ssm

if T.TYPE_CHECKING:  # pragma: no cover
    from .stack import PublisherStack


class PublisherStackSsmMixin:
    """
    The parameter that records where to send alerts.
    """

    def s02_create_ssm_parameter(self: PublisherStack) -> None:
        """
        Create the parameter valued with the alert topic ARN.
        """
        self.alert_topic_arn_parameter = ssm.StringParameter(
            self,
            "AlertTopicArnParameter",
            parameter_name=self.config.ssm_param_name_alert_topic_arn,
            string_value=self.alert_topic.topic_arn,
        )
