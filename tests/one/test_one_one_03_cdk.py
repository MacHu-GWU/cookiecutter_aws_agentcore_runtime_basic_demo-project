# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_03_cdk import OneCdkMixin

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_ctx_enum import StackCtxEnum
from cookiecutter_aws_agentcore_runtime_basic_demo.cdk.stack_enum import StackEnum


def test_cdk():
    one = One()
    assert isinstance(one, OneCdkMixin)
    assert isinstance(one.stack_ctx_enum, StackCtxEnum)
    assert isinstance(one.stack_enum, StackEnum)
    assert one.stack_ctx_enum.one is one
    assert one.stack_enum.one is one


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_03_cdk",
        preview=False,
    )
