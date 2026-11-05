# -*- coding: utf-8 -*-

"""
Print the CloudFormation console URL of every stack in every environment.
An environment that fails gets an error line; the others are still printed.
"""

from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.mise_tasks import (
    print_cdk_stack_urls,
)


if __name__ == "__main__":
    print_cdk_stack_urls()
