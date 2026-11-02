# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_00_main import One
from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_00_main import one

from cookiecutter_aws_agentcore_runtime_basic_demo.env import env
from cookiecutter_aws_agentcore_runtime_basic_demo.runtime import runtime


def test_one():
    """
    ``one`` exposes the module-level env and runtime singletons, not copies.
    """
    assert isinstance(one, One)
    assert one.env is env
    assert one.runtime is runtime


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_00_main",
        preview=False,
    )
