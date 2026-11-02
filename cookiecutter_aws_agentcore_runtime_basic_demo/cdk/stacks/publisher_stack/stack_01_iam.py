# -*- coding: utf-8 -*-

"""
The IAM part of :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.publisher_stack.stack.PublisherStack`.
"""

from __future__ import annotations

import typing as T

import aws_cdk as cdk
from aws_cdk import aws_iam as iam

if T.TYPE_CHECKING:  # pragma: no cover
    from .stack import PublisherStack


class PublisherStackIamMixin:
    """
    The role allowed to publish alerts.
    """

    def s01_create_iam_role(self: PublisherStack) -> None:
        """
        Create the role, allow it to publish to the alert topic, and export its ARN.
        """
        self.publisher_role = iam.Role(
            self,
            "PublisherRole",
            role_name=self.config.iam_role_name_publisher,
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )
        # puts the topic ARN, exported by the alerts stack, into this role's policy
        self.alert_topic.grant_publish(self.publisher_role)
        self.output_publisher_role_arn = cdk.CfnOutput(
            self,
            "PublisherRoleArn",
            value=self.publisher_role.role_arn,
            export_name=self.config.cft_export_name_publisher_role_arn,
        )
