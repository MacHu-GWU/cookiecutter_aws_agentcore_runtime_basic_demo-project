# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas import SiteInfo
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas import (
    SiteDetail,
)

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import Site
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import Asset


def test_from_orm_row():
    """A model is built from an ORM row, and keeps only its own fields."""
    row = Site(
        id="S-01",
        name="a",
        kind="solar",
        lat=1.0,
        lon=2.0,
        capacity_mw=3,
        assets=[Asset(id="A-01", site_id="S-01", kind="inverter", model="m")],
    )
    assert SiteInfo.model_validate(row).model_dump() == {
        "id": "S-01",
        "name": "a",
        "kind": "solar",
        "lat": 1.0,
        "lon": 2.0,
        "capacity_mw": 3,
    }
    detail = SiteDetail.model_validate(row)
    assert detail.assets[0].model == "m"
    assert detail.technicians == []


def test_json_schema_has_descriptions():
    """The descriptions become the MCP output schema the LLM reads."""
    properties = SiteDetail.model_json_schema()["properties"]
    assert (
        properties["capacity_mw"]["description"] == "Generating capacity in megawatts."
    )


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas",
        preview=False,
    )
