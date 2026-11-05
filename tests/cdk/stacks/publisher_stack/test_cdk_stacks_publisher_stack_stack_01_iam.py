# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.publisher_stack.stack_01_iam import (
    PublisherStackIamMixin,
)

from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.publisher_stack.stack import (
    PublisherStack,
)


def test():
    """
    The resources are tested through the stack, in test_cdk_stacks_publisher_stack_stack.py.
    """
    assert issubclass(PublisherStack, PublisherStackIamMixin)


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stacks.publisher_stack.stack_01_iam",
        preview=False,
    )
