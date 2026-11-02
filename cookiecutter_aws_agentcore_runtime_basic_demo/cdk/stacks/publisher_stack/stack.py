# -*- coding: utf-8 -*-

"""
The :class:`PublisherStack` class; its resources are in the ``stack_0N_*.py`` mixins.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import aws_sns as sns
from constructs import Construct

from ....config.api import Config
from .stack_01_iam import PublisherStackIamMixin
from .stack_02_ssm import PublisherStackSsmMixin


class PublisherStack(
    cdk.Stack,
    PublisherStackIamMixin,
    PublisherStackSsmMixin,
):
    """
    Like :class:`~cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.alerts_stack.AlertsStack`,
    plus ``alert_topic``, the topic of the alerts stack of the same environment,
    passed explicitly so the dependency shows in the signature.
    """

    def __init__(
        self,
        scope: Construct,
        id: str,
        stack_name: str,
        env: cdk.Environment,
        config: Config,
        alert_topic: sns.ITopic,
    ) -> None:
        super().__init__(
            scope=scope,
            id=id,
            stack_name=stack_name,
            env=env,
        )
        self.config = config
        self.alert_topic = alert_topic
        self.s01_create_iam_role()
        self.s02_create_ssm_parameter()
