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


def test_new_boto_ses(monkeypatch):
    """A new session each call, with the region of the current environment."""
    monkeypatch.setenv("IS_AGENTCORE_RUNTIME", "true")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    one = One()
    first = one.new_boto_ses()
    assert first.region_name == "us-west-2"
    assert one.new_boto_ses() is not first


def test_get_bsm_kwargs_profile(monkeypatch):
    """Locally, the profile of the environment when it is set."""
    monkeypatch.setenv("AWS_PROFILE_FOR_DEV", "my-dev-profile")
    assert One().get_bsm_kwargs() == {
        "region_name": "us-east-1",
        "profile_name": "my-dev-profile",
    }


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_02_boto_ses",
        preview=False,
    )
