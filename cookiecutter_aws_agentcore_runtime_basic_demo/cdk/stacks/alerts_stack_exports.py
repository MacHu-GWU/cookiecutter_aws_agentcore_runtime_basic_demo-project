# -*- coding: utf-8 -*-

"""
Read the outputs of the alerts stack, from this project or from any other.

**Copy this file as is.** It imports only the standard library (and a type stub
when type checking), so another project that needs a value of this stack, such as
:attr:`AlertsStackExports.alert_topic_arn`, copies this one file instead of depending on this
project or guessing output names::

    import boto3

    cf_client = boto3.Session(profile_name="my_dev_profile").client("cloudformation")
    exports = AlertsStackExports.load(cf_client=cf_client, env_name="dev")
    print(exports.alert_topic_arn)

The stack names below are literal values, not built from the config, so the file
stays self-contained. ``tests_int/`` checks them, and every output key, against
the deployed stack.

To add a value: add a ``cdk.CfnOutput`` to the stack, then a property here that
reads it by its output key, and add the property to :meth:`AlertsStackExports.to_dict`.
"""

import typing as T
import dataclasses

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_cloudformation.client import CloudFormationClient

STACK_NAMES: dict[str, str] = {
    "dev": "cookiecutter-aws-agentcore-runtime-basic-demo-dev-alerts",
    "tst": "cookiecutter-aws-agentcore-runtime-basic-demo-tst-alerts",
    "prd": "cookiecutter-aws-agentcore-runtime-basic-demo-prd-alerts",
}
"""
The CloudFormation stack name of each environment.
"""


@dataclasses.dataclass
class AlertsStackExports:
    """
    The outputs of one deployed alerts stack. Create it with :meth:`load`.
    """

    # fmt: off
    env_name: str = dataclasses.field()  #: The environment, such as ``dev``.
    stack_name: str = dataclasses.field()  #: The CloudFormation stack name.
    outputs: dict[str, str] = dataclasses.field()  #: Every output, ``OutputKey`` to ``OutputValue``.
    exports: dict[str, str] = dataclasses.field()  #: Every exported output, ``ExportName`` to ``OutputValue``.
    # fmt: on

    @classmethod
    def from_describe_stacks_response(
        cls,
        env_name: str,
        response: dict[str, T.Any],
    ) -> "AlertsStackExports":
        """
        Build it from the response of ``cloudformation.describe_stacks``.
        """
        stack = response["Stacks"][0]
        outputs = {}
        exports = {}
        for dct in stack.get("Outputs", []):
            outputs[dct["OutputKey"]] = dct["OutputValue"]
            if "ExportName" in dct:
                exports[dct["ExportName"]] = dct["OutputValue"]
        return cls(
            env_name=env_name,
            stack_name=stack["StackName"],
            outputs=outputs,
            exports=exports,
        )

    @classmethod
    def load(
        cls,
        cf_client: "CloudFormationClient",
        env_name: str,
    ) -> "AlertsStackExports":  # pragma: no cover
        """
        Read the outputs of the stack of ``env_name`` with one ``describe_stacks`` call.

        :param cf_client: a CloudFormation client of the account of ``env_name``.
        :param env_name: a key of :data:`STACK_NAMES`, such as ``dev``.
        """
        response = cf_client.describe_stacks(StackName=STACK_NAMES[env_name])
        return cls.from_describe_stacks_response(env_name=env_name, response=response)

    @property
    def alert_topic_arn(self) -> str:
        """
        The ARN of the SNS topic to publish alerts to.
        """
        return self.outputs["AlertTopicArn"]

    def to_dict(self) -> dict[str, str]:
        """
        Every value this module provides, by property name. Reading them all
        raises ``KeyError`` if the deployed stack lacks one of the outputs.
        """
        return {
            "alert_topic_arn": self.alert_topic_arn,
        }
