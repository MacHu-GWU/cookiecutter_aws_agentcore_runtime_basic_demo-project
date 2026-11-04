# -*- coding: utf-8 -*-

"""
What the queries return: Pydantic models, separate from the ORM models in
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm`.

A table and an answer are different things, even when they share fields: an
answer may leave out columns, add related rows, or reshape values, and the
database may change without changing the tool's contract. The MCP server turns
these models into the tools' output schemas, so the field descriptions are what
the LLM reads. ``from_attributes`` builds a model from an ORM row.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class SiteInfo(BaseModel):
    """
    A power plant site.
    """

    model_config = ConfigDict(from_attributes=True)

    # fmt: off
    id: str = Field(description="Site ID, such as S-01.")
    name: str = Field(description="Site name.")
    kind: str = Field(description="solar or wind.")
    lat: float = Field(description="Latitude in degrees.")
    lon: float = Field(description="Longitude in degrees.")
    capacity_mw: int = Field(description="Generating capacity in megawatts.")
    # fmt: on


class AssetInfo(BaseModel):
    """
    A piece of equipment at a site.
    """

    model_config = ConfigDict(from_attributes=True)

    # fmt: off
    id: str = Field(description="Asset ID, such as A-01.")
    site_id: str = Field(description="ID of the site the asset is at.")
    kind: str = Field(description="inverter, transformer, or turbine.")
    model: str = Field(description="Manufacturer model.")
    # fmt: on


class TechnicianInfo(BaseModel):
    """
    A field technician.
    """

    model_config = ConfigDict(from_attributes=True)

    # fmt: off
    id: str = Field(description="Technician ID, such as T-01.")
    name: str = Field(description="Full name.")
    skill: str = Field(description="solar, wind, or electrical.")
    # fmt: on


class SiteDetail(SiteInfo):
    """
    A site with its assets and the technicians assigned to it.
    """

    # fmt: off
    assets: list[AssetInfo] = Field(description="Equipment at the site, by ID.")
    technicians: list[TechnicianInfo] = Field(description="Technicians assigned to the site, by ID.")
    # fmt: on


class TechnicianDetail(TechnicianInfo):
    """
    A technician with the sites they are assigned to.
    """

    # fmt: off
    sites: list[SiteInfo] = Field(description="Sites the technician is assigned to, by ID.")
    # fmt: on


class WeatherForecast(BaseModel):
    """
    Tomorrow's weather forecast for a location.
    """

    # fmt: off
    lat: float = Field(description="Latitude in degrees.")
    lon: float = Field(description="Longitude in degrees.")
    condition: str = Field(description="sunny, cloudy, rain, or thunderstorm.")
    wind_speed_ms: int = Field(description="Wind speed in meters per second.")
    temperature_c: int = Field(description="Temperature in degrees Celsius.")
    safe_for_inspection: bool = Field(description="False on a thunderstorm or when the wind is above the safe limit for climbing a turbine or a roof.")
    # fmt: on
