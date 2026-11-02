# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.alerts_stack_exports import STACK_NAMES
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.alerts_stack_exports import AlertsStackExports

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import one


def test():
    """
    The deployed stack of the current environment has every output this module reads.
    """
    env_name = one.env.current_env_name
    assert STACK_NAMES[env_name] == one.config.cft_stack_name_alerts
    exports = AlertsStackExports.load(
        cf_client=one.cloudformation_client, env_name=env_name
    )
    print(exports.to_dict())


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_unit_test

    run_unit_test(__file__)
