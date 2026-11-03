# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_02_boto_ses import (
    OneBotoSesMixin,
)

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One


def test_bsm_local(monkeypatch):
    """Locally: the region of the config."""
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    one = One()
    assert isinstance(one, OneBotoSesMixin)
    assert one.bsm.aws_region == one.config.aws_region == "us-east-1"


def test_bsm_agentcore(monkeypatch):
    """
    On an AgentCore runtime the region is AWS_REGION, and building the session
    does not load the config, which is read through it.
    """
    monkeypatch.setenv("IS_AGENTCORE_RUNTIME", "true")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    one = One()
    assert one.bsm.aws_region == "us-west-2"
    assert "config" not in one.__dict__


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_02_boto_ses",
        preview=False,
    )
