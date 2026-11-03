# -*- coding: utf-8 -*-

"""
Read-only queries over the power plant database, exposed as MCP tools by
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp`.

Every function takes the engine first, queries the ORM models, and returns the
Pydantic models of :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas`,
ordered by ID. The first paragraph of each docstring is the tool description the
LLM reads, so it does not mention the engine.
"""

from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as orm

from .orm import Site
from .orm import Asset
from .orm import Technician
from .schemas import SiteInfo
from .schemas import AssetInfo
from .schemas import SiteDetail
from .schemas import TechnicianDetail


def list_sites(
    engine: sa.Engine,
    kind: str | None = None,
) -> list[SiteInfo]:
    """
    List all sites, optionally only those of one ``kind`` (``solar`` or ``wind``).
    """
    stmt = sa.select(Site).order_by(Site.id)
    if kind is not None:
        stmt = stmt.where(Site.kind == kind)
    with orm.Session(engine) as session:
        return [SiteInfo.model_validate(row) for row in session.scalars(stmt)]


def list_assets(
    engine: sa.Engine,
    site_id: str | None = None,
    kind: str | None = None,
) -> list[AssetInfo]:
    """
    List assets, optionally filtered by ``site_id`` and / or ``kind``.
    """
    stmt = sa.select(Asset).order_by(Asset.id)
    if site_id is not None:
        stmt = stmt.where(Asset.site_id == site_id)
    if kind is not None:
        stmt = stmt.where(Asset.kind == kind)
    with orm.Session(engine) as session:
        return [AssetInfo.model_validate(row) for row in session.scalars(stmt)]


def get_site(
    engine: sa.Engine,
    site_id: str,
) -> SiteDetail:
    """
    Get one site with its ``assets`` and assigned ``technicians``.

    :raises ValueError: if the site does not exist.
    """
    with orm.Session(engine) as session:
        site = session.get(Site, site_id)
        if site is None:
            raise ValueError(f"site {site_id!r} not found")
        # reads site.assets and site.technicians while the session is open
        return SiteDetail.model_validate(site)


def get_technician(
    engine: sa.Engine,
    technician_id: str,
) -> TechnicianDetail:
    """
    Get one technician with the ``sites`` they are assigned to.

    :raises ValueError: if the technician does not exist.
    """
    with orm.Session(engine) as session:
        technician = session.get(Technician, technician_id)
        if technician is None:
            raise ValueError(f"technician {technician_id!r} not found")
        # reads technician.sites while the session is open
        return TechnicianDetail.model_validate(technician)
