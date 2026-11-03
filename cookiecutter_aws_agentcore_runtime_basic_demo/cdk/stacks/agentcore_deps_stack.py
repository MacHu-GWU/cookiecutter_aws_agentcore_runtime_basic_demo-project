# -*- coding: utf-8 -*-

"""
The agentcore_deps stack: what the AgentCore runtimes depend on but is not
AgentCore. The AgentCore CLI deploys the runtimes in its own stack
(``agentcore/``, ``mise run ac-deploy-<env>``), which only refers to what is
here, by the names in the config: deploy this stack first.

Today it holds one managed policy, attached to the execution role of every
runtime through ``additionalPolicies`` in ``agentcore.json``. Give the runtimes
a new permission here, such as access to a database secret.
"""

from __future__ import annotations

import aws_cdk as cdk
from aws_cdk import aws_iam as iam
from constructs import Construct

from ...config.api import Config


class AgentCoreDepsStack(cdk.Stack):
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
        self.s01_create_runtime_policy()

    def s01_create_runtime_policy(self) -> None:
        """
        Create the policy of every AgentCore runtime: read the config parameter.
        The parameter is a ``SecureString`` with the AWS-managed key ``aws/ssm``,
        whose key policy already allows its use through SSM in the account, so
        no ``kms:Decrypt`` is needed.
        """
        self.runtime_policy = iam.ManagedPolicy(
            self,
            "AgentCoreRuntimePolicy",
            managed_policy_name=self.config.iam_policy_name_agentcore_runtime,
            statements=[
                iam.PolicyStatement(
                    actions=["ssm:GetParameter"],
                    resources=[self.config.ssm_param_arn_config],
                ),
            ],
        )
