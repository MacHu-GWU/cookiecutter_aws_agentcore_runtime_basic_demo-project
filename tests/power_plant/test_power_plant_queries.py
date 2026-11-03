# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries import list_sites
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries import (
    list_assets,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries import get_site
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries import (
    get_technician,
)

import pytest

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.data import SITES


def test_list_sites():
    assert len(list_sites()) == 5
    assert [row["id"] for row in list_sites(kind="wind")] == ["S-03", "S-04"]
    assert list_sites(kind="hydro") == []


@pytest.mark.parametrize(
    "site_id, kind, expected",
    [
        (None, None, 12),
        ("S-03", None, 3),
        (None, "transformer", 3),
        ("S-01", "inverter", 2),
    ],
)
def test_list_assets(site_id, kind, expected):
    assert len(list_assets(site_id=site_id, kind=kind)) == expected


def test_get_site():
    site = get_site("S-03")
    assert site["name"] == "Ridge Wind"
    assert [row["id"] for row in site["assets"]] == ["A-06", "A-07", "A-08"]
    assert [row["id"] for row in site["technicians"]] == ["T-02", "T-04"]


def test_get_site_returns_a_copy():
    """Changing a result must not change the fake database."""
    site = get_site("S-01")
    site["name"] = "changed"
    assert SITES[0]["name"] == "Sunrise Valley"


def test_get_technician():
    technician = get_technician("T-01")
    assert technician["name"] == "Alice Chen"
    assert [row["id"] for row in technician["sites"]] == ["S-01", "S-02", "S-05"]


def test_not_found():
    with pytest.raises(ValueError, match="site 'S-99' not found"):
        get_site("S-99")
    with pytest.raises(ValueError, match="technician 'T-99' not found"):
        get_technician("T-99")


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries",
        preview=False,
    )
