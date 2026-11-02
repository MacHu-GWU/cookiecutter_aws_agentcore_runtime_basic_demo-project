# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one import api


def test():
    _ = api
    _ = api.One
    _ = api.one


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.api",
        preview=False,
    )
