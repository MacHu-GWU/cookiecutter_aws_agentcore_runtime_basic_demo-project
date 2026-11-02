#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The CDK app entry point, run by the cdk CLI (see ``cdk.json``).

It creates the stacks of the current environment, the one ``ENV_NAME`` selects,
such as ``ENV_NAME=prd cdk synth``.
"""

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import one

one.stack_enum.synth()
