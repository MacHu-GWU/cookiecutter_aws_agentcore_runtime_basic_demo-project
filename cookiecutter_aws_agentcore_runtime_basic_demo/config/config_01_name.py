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
import urllib.parse
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

    @cached_property
    def cft_stack_name_agentcore_deps(self: Config) -> str:
        """
        Name of the stack of what the AgentCore runtimes depend on but is not
        AgentCore, such as ``my-project-dev-agentcore-deps``; deploy it before
        ``ac-deploy-<env>``.
        """
        return self.get_cft_stack_name("agentcore-deps")

    @cached_property
    def cft_stack_url_agentcore_deps(self: Config) -> str:
        """
        Console URL of :attr:`cft_stack_name_agentcore_deps`.
        """
        return self.get_cft_stack_url(self.cft_stack_name_agentcore_deps)

    @cached_property
    def cft_stack_name_agentcore(self: Config) -> str:
        """
        Name of the stack the AgentCore CLI deploys from ``agentcore/``, such as
        ``AgentCore-MyProject-dev``. The CLI's CDK app names it
        ``AgentCore-<project>-<target>``, with ``_`` turned into ``-``.
        """
        name = f"AgentCore-{self.agentcore_project_name}-{self.agentcore_target_name}"
        return name.replace("_", "-")

    @cached_property
    def cft_stack_url_agentcore(self: Config) -> str:
        """
        Console URL of :attr:`cft_stack_name_agentcore`.
        """
        return self.get_cft_stack_url(self.cft_stack_name_agentcore)

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

    def get_iam_role_url(self: Config, role_name: str) -> str:
        """
        The console URL of an IAM role, given its name.
        """
        return (
            f"https://{self.aws_region}.console.aws.amazon.com/iam/home"
            f"?region={self.aws_region}#/roles/details/{role_name}"
        )

    # --------------------------------------------------------------------------
    # IAM policies
    # --------------------------------------------------------------------------
    @cached_property
    def iam_policy_name_agentcore_runtime(self: Config) -> str:
        """
        Name of the managed policy attached to the execution role of every
        AgentCore runtime, such as ``my-project-dev-us-east-1-agentcore-runtime``.
        IAM is global, so the name includes the region.
        """
        return f"{self.prefix_name_slug}-{self.aws_region}-agentcore-runtime"

    @cached_property
    def iam_policy_arn_agentcore_runtime(self: Config) -> str:
        """
        ARN of :attr:`iam_policy_name_agentcore_runtime`; ``agentcore.json`` lists
        it in ``additionalPolicies`` of every runtime.
        """
        return (
            f"arn:aws:iam::{self.aws_account_id}:policy"
            f"/{self.iam_policy_name_agentcore_runtime}"
        )

    @cached_property
    def iam_policy_url_agentcore_runtime(self: Config) -> str:
        """
        Console URL of :attr:`iam_policy_name_agentcore_runtime`.
        """
        quoted_arn = urllib.parse.quote(self.iam_policy_arn_agentcore_runtime, safe="")
        return f"https://us-east-1.console.aws.amazon.com/iam/home#/policies/details/{quoted_arn}"

    # --------------------------------------------------------------------------
    # CloudWatch log groups
    # --------------------------------------------------------------------------
    def get_cloudwatch_log_group_url(self: Config, log_group_name: str) -> str:
        """
        The console URL of a CloudWatch log group, given its name.
        """
        # the console escapes "/" in the log group name as "$252F"
        name = log_group_name.replace("/", "$252F")
        return (
            f"https://{self.aws_region}.console.aws.amazon.com/cloudwatch/home"
            f"?region={self.aws_region}#logsV2:log-groups/log-group/{name}"
        )

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
    def ssm_param_name_config(self: Config) -> str:
        """
        Name of the parameter that holds the whole config of this environment as
        JSON, such as ``/my-project-dev/config``; written by ``mise run config-deploy-<env>``.
        """
        return f"/{self.prefix_name_slug}/config"

    @cached_property
    def ssm_param_url_config(self: Config) -> str:
        """
        Console URL of :attr:`ssm_param_name_config`.
        """
        return self.get_ssm_param_url(self.ssm_param_name_config)

    @cached_property
    def ssm_param_arn_config(self: Config) -> str:
        """
        ARN of :attr:`ssm_param_name_config`.
        """
        return self.get_ssm_param_arn(self.ssm_param_name_config)

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

    # --------------------------------------------------------------------------
    # AgentCore (the agentcore/ project, deployed by the AgentCore CLI)
    # --------------------------------------------------------------------------
    @cached_property
    def agentcore_target_name(self: Config) -> str:
        """
        The AgentCore CLI deployment target of this environment, named after it,
        such as ``dev``. The CLI puts the target in every physical name, so
        every AgentCore resource name contains the environment.
        """
        return self.env_name

    def get_agentcore_runtime_physical_name(self: Config, name: str) -> str:
        """
        The name AWS knows a runtime by, ``<project>_<target>_<name>``, such as
        ``MyProject_dev_PowerPlantMcp``; ``name`` is its name in ``agentcore.json``.

        :raises ValueError: if longer than the 48 characters AgentCore allows.
        """
        target = self.agentcore_target_name.replace("-", "_")
        physical_name = f"{self.agentcore_project_name}_{target}_{name}"
        if len(physical_name) > 48:
            raise ValueError(
                f"runtime name {physical_name!r} is longer than 48 characters, "
                "shorten agentcore_project_name or the runtime name"
            )
        return physical_name

    def get_agentcore_runtime_url(self: Config, runtime_id: str) -> str:
        """
        The AgentCore console URL of a deployed runtime, given its ID, such as
        ``MyProject_dev_PowerPlantMcp-abc``: the physical name plus a suffix
        AWS assigns at deploy time, so it is looked up, never built.
        """
        return (
            f"https://{self.aws_region}.console.aws.amazon.com"
            f"/bedrock-agentcore/agents/{runtime_id}"
        )

    @cached_property
    def agentcore_runtime_name_power_plant_mcp(self: Config) -> str:
        """
        Name of the MCP server runtime in ``agentcore.json``, ``PowerPlantMcp``.
        """
        return "PowerPlantMcp"

    @cached_property
    def agentcore_runtime_physical_name_power_plant_mcp(self: Config) -> str:
        """
        Physical name of :attr:`agentcore_runtime_name_power_plant_mcp`,
        such as ``MyProject_dev_PowerPlantMcp``.
        """
        return self.get_agentcore_runtime_physical_name(
            self.agentcore_runtime_name_power_plant_mcp
        )

    @cached_property
    def agentcore_runtime_name_site_agent(self: Config) -> str:
        """
        Name of the agent runtime in ``agentcore.json``, ``SiteAgent``.
        """
        return "SiteAgent"

    @cached_property
    def agentcore_runtime_physical_name_site_agent(self: Config) -> str:
        """
        Physical name of :attr:`agentcore_runtime_name_site_agent`,
        such as ``MyProject_dev_SiteAgent``.
        """
        return self.get_agentcore_runtime_physical_name(
            self.agentcore_runtime_name_site_agent
        )
