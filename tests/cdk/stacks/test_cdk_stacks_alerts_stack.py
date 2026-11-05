# -*- coding: utf-8 -*-

"""
Synth smoke test of the alerts stack: create it through ``StackEnum``, the way
``cdk/cdk_app.py`` does, and synthesize it. Passing means the constructs, names,
and cross-stack references are wired up; what each resource looks like is not
checked here (the names are checked in ``tests/config/test_config_config_01_name.py``).
"""

from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.alerts_stack import (
    AlertsStack,
)

import aws_cdk as cdk

from cookiecutter_aws_agentcore_runtime_basic_demo.config.api import Config
from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_enum import StackEnum


def test_synth(config: Config):
    one = One()
    one.config = config
    stack_enum = StackEnum(app=cdk.App(), one=one)
    assert isinstance(stack_enum.alerts, AlertsStack)
    stack_enum.app.synth()


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.alerts_stack",
        preview=False,
    )
