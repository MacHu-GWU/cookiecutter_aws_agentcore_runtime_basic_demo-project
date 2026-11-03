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
import sqlalchemy as sa

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas import SiteInfo
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas import (
    SiteDetail,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas import (
    TechnicianDetail,
)

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import (
    create_db_engine,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import (
    load_seed_data,
)


@pytest.fixture(scope="module")
def engine() -> sa.Engine:
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    load_seed_data(engine)
    return engine


def test_list_sites(engine):
    sites = list_sites(engine)
    assert len(sites) == 5
    assert sites[0] == SiteInfo(
        id="S-01",
        name="Sunrise Valley",
        kind="solar",
        lat=35.05,
        lon=-117.60,
        capacity_mw=120,
    )
    assert [site.id for site in list_sites(engine, kind="wind")] == ["S-03", "S-04"]
    assert list_sites(engine, kind="hydro") == []


@pytest.mark.parametrize(
    "site_id, kind, expected",
    [
        (None, None, 12),
        ("S-03", None, 3),
        (None, "transformer", 3),
        ("S-01", "inverter", 2),
    ],
)
def test_list_assets(engine, site_id, kind, expected):
    assert len(list_assets(engine, site_id=site_id, kind=kind)) == expected


def test_get_site(engine):
    site = get_site(engine, "S-03")
    assert isinstance(site, SiteDetail)
    assert site.name == "Ridge Wind"
    assert [asset.id for asset in site.assets] == ["A-06", "A-07", "A-08"]
    assert [technician.id for technician in site.technicians] == ["T-02", "T-04"]


def test_get_technician(engine):
    technician = get_technician(engine, "T-01")
    assert isinstance(technician, TechnicianDetail)
    assert technician.name == "Alice Chen"
    assert [site.id for site in technician.sites] == ["S-01", "S-02", "S-05"]


def test_not_found(engine):
    with pytest.raises(ValueError, match="site 'S-99' not found"):
        get_site(engine, "S-99")
    with pytest.raises(ValueError, match="technician 'T-99' not found"):
        get_technician(engine, "T-99")


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.queries",
        preview=False,
    )
