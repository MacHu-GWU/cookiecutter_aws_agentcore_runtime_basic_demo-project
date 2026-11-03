# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.data import SITES
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.data import ASSETS
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.data import TECHNICIANS
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.data import (
    SITE_TECHNICIANS,
)


def test_ids_are_unique():
    for table in [SITES, ASSETS, TECHNICIANS]:
        ids = [row["id"] for row in table]
        assert len(ids) == len(set(ids))


def test_foreign_keys_resolve():
    """Every asset and link row points at rows that exist."""
    site_ids = {row["id"] for row in SITES}
    technician_ids = {row["id"] for row in TECHNICIANS}
    for row in ASSETS:
        assert row["site_id"] in site_ids
    for row in SITE_TECHNICIANS:
        assert row["site_id"] in site_ids
        assert row["technician_id"] in technician_ids


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.data",
        preview=False,
    )
