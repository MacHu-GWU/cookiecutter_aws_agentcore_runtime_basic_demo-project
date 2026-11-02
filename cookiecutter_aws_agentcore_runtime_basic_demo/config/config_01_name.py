# -*- coding: utf-8 -*-

"""
Every AWS resource name of the project, with its console URL and ARN.

Names are built here, never in the CDK code, so stacks, scripts, and tests all
refer to the same value (``one.config.ssm_param_name_log_level``) instead of
repeating a string template.

Naming pattern: ``<resource type>_<attribute>_<short name>``, such as
``cft_stack_name_alerts``, ``cft_stack_url_alerts``, ``ssm_param_arn_log_level``.
CloudFormation stacks have no ARN property, because the ARN ends in a random ID
assigned at creation.
"""

from __future__ import annotations

import typing as T
from functools import cached_property

if T.TYPE_CHECKING:  # pragma: no cover
    from .config_00_main import Config


class ConfigNameMixin:
    """
    Resource names, console URLs, and ARNs derived from the config values.
    """

    # --------------------------------------------------------------------------
    # Prefixes
    # --------------------------------------------------------------------------
    @cached_property
    def project_name_snake(self: Config) -> str:
        """
        Project name in snake_case, such as ``my_project``.
        """
        return self.project_name.replace("-", "_")

    @cached_property
    def project_name_slug(self: Config) -> str:
        """
        Project name in slug-case, such as ``my-project``.
        """
        return self.project_name_snake.replace("_", "-")

    @cached_property
    def prefix_name_slug(self: Config) -> str:
        """
        Prefix of every resource name of this environment, such as ``my-project-dev``.
        """
        return f"{self.project_name_slug}-{self.env_name}"

    # --------------------------------------------------------------------------
    # CloudFormation stacks
    # --------------------------------------------------------------------------
    def get_cft_stack_name(self: Config, short_name: str) -> str:
        """
        The name of a stack, ``<prefix_name_slug>-<short_name>``; also its construct ID.
        """
        return f"{self.prefix_name_slug}-{short_name}"

    def get_cft_stack_url(self: Config, stack_name: str) -> str:
        """
        The CloudFormation console URL of the stack, found by its name, so it needs
        no stack ARN (which ends in an ID assigned at creation) and works before the
        stack exists.
        """
        return (
            f"https://{self.aws_region}.console.aws.amazon.com/cloudformation/home"
            f"?region={self.aws_region}#/stacks/stackinfo?filteringText={stack_name}"
            f"&filteringStatus=active&viewNested=true"
        )

    @cached_property
    def cft_stack_name_alerts(self: Config) -> str:
        """
        Name of the alerts stack, such as ``my-project-dev-alerts``.
        """
        return self.get_cft_stack_name("alerts")

    @cached_property
    def cft_stack_url_alerts(self: Config) -> str:
        """
        Console URL of :attr:`cft_stack_name_alerts`.
        """
        return self.get_cft_stack_url(self.cft_stack_name_alerts)

    @cached_property
    def cft_stack_name_publisher(self: Config) -> str:
        """
        Name of the publisher stack, such as ``my-project-dev-publisher``.
        """
        return self.get_cft_stack_name("publisher")

    @cached_property
    def cft_stack_url_publisher(self: Config) -> str:
        """
        Console URL of :attr:`cft_stack_name_publisher`.
        """
        return self.get_cft_stack_url(self.cft_stack_name_publisher)

    # --------------------------------------------------------------------------
    # CloudFormation exports, read by other projects through *_stack_exports.py
    # --------------------------------------------------------------------------
    @cached_property
    def cft_export_name_alert_topic_arn(self: Config) -> str:
        """
        Export name of the alert topic ARN, such as ``my-project-dev-alert-topic-arn``.
        """
        return f"{self.prefix_name_slug}-alert-topic-arn"

    @cached_property
    def cft_export_name_publisher_role_arn(self: Config) -> str:
        """
        Export name of the publisher role ARN, such as ``my-project-dev-publisher-role-arn``.
        """
        return f"{self.prefix_name_slug}-publisher-role-arn"

    # --------------------------------------------------------------------------
    # SNS topics
    # --------------------------------------------------------------------------
    @cached_property
    def sns_topic_name_alerts(self: Config) -> str:
        """
        Name of the alert topic, such as ``my-project-dev-alerts``.
        """
        return f"{self.prefix_name_slug}-alerts"

    @cached_property
    def sns_topic_arn_alerts(self: Config) -> str:
        """
        ARN of :attr:`sns_topic_name_alerts`.
        """
        return (
            f"arn:aws:sns:{self.aws_region}:{self.aws_account_id}"
            f":{self.sns_topic_name_alerts}"
        )

    # --------------------------------------------------------------------------
    # IAM roles
    # --------------------------------------------------------------------------
    @cached_property
    def iam_role_name_publisher(self: Config) -> str:
        """
        Name of the role allowed to publish alerts, such as ``my-project-dev-publisher``.
        """
        return f"{self.prefix_name_slug}-publisher"

    @cached_property
    def iam_role_arn_publisher(self: Config) -> str:
        """
        ARN of :attr:`iam_role_name_publisher`.
        """
        return f"arn:aws:iam::{self.aws_account_id}:role/{self.iam_role_name_publisher}"

    # --------------------------------------------------------------------------
    # SSM parameters
    # --------------------------------------------------------------------------
    def get_ssm_param_url(self: Config, name: str) -> str:
        """
        The console URL of an SSM parameter, given its name (which starts with ``/``).
        """
        return (
            f"https://{self.aws_region}.console.aws.amazon.com/systems-manager"
            f"/parameters{name}/description?region={self.aws_region}&tab=Table"
        )

    def get_ssm_param_arn(self: Config, name: str) -> str:
        """
        The ARN of an SSM parameter, given its name (which starts with ``/``).
        """
        return f"arn:aws:ssm:{self.aws_region}:{self.aws_account_id}:parameter{name}"

    @cached_property
    def ssm_param_name_log_level(self: Config) -> str:
        """
        Name of the log level parameter, such as ``/my-project-dev/log-level``.
        """
        return f"/{self.prefix_name_slug}/log-level"

    @cached_property
    def ssm_param_url_log_level(self: Config) -> str:
        """
        Console URL of :attr:`ssm_param_name_log_level`.
        """
        return self.get_ssm_param_url(self.ssm_param_name_log_level)

    @cached_property
    def ssm_param_arn_log_level(self: Config) -> str:
        """
        ARN of :attr:`ssm_param_name_log_level`.
        """
        return self.get_ssm_param_arn(self.ssm_param_name_log_level)

    @cached_property
    def ssm_param_name_alert_topic_arn(self: Config) -> str:
        """
        Name of the parameter that records the alert topic ARN,
        such as ``/my-project-dev/alert-topic-arn``.
        """
        return f"/{self.prefix_name_slug}/alert-topic-arn"

    @cached_property
    def ssm_param_url_alert_topic_arn(self: Config) -> str:
        """
        Console URL of :attr:`ssm_param_name_alert_topic_arn`.
        """
        return self.get_ssm_param_url(self.ssm_param_name_alert_topic_arn)

    @cached_property
    def ssm_param_arn_alert_topic_arn(self: Config) -> str:
        """
        ARN of :attr:`ssm_param_name_alert_topic_arn`.
        """
        return self.get_ssm_param_arn(self.ssm_param_name_alert_topic_arn)
