# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.one.one_05_db import OneDbMixin

from cookiecutter_aws_agentcore_runtime_basic_demo.one.api import One
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries import get_site


def test_engine():
    """The engine of the config's database, seeded, and built once."""
    one = One()
    assert isinstance(one, OneDbMixin)
    assert one.engine.url.database == ":memory:"
    assert get_site(one.engine, "S-03")["name"] == "Ridge Wind"
    assert one.engine is one.engine


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.one.one_05_db",
        preview=False,
    )
