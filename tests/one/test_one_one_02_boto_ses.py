# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_02_boto_ses import OneBotoSesMixin


def test():
    """
    Placeholder: the session logic is a few lines with nothing worth testing yet.
    """
    _ = OneBotoSesMixin


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_02_boto_ses",
        preview=False,
    )
