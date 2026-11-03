# -*- coding: utf-8 -*-

"""
Read-only queries over the power plant database, exposed as MCP tools by
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.runtimes.power_plant_mcp`.

Every function takes the engine first and returns plain JSON-friendly dicts,
ordered by ID. The first paragraph of each docstring is the tool description
the LLM reads, so it does not mention the engine.
"""

from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as orm

from .orm import Base
from .orm import Site
from .orm import Asset
from .orm import Technician
from .orm import SiteTechnician


def _to_dict(row: Base) -> dict:
    return {column.key: getattr(row, column.key) for column in row.__table__.columns}


def _get(session: orm.Session, model: type[Base], id: str, label: str) -> dict:
    row = session.get(model, id)
    if row is None:
        raise ValueError(f"{label} {id!r} not found")
    return _to_dict(row)


def list_sites(
    engine: sa.Engine,
    kind: str | None = None,
) -> list[dict]:
    """
    List all sites, optionally only those of one ``kind`` (``solar`` or ``wind``).
    """
    stmt = sa.select(Site).order_by(Site.id)
    if kind is not None:
        stmt = stmt.where(Site.kind == kind)
    with orm.Session(engine) as session:
        return [_to_dict(row) for row in session.scalars(stmt)]


def list_assets(
    engine: sa.Engine,
    site_id: str | None = None,
    kind: str | None = None,
) -> list[dict]:
    """
    List assets, optionally filtered by ``site_id`` and / or ``kind``.
    """
    stmt = sa.select(Asset).order_by(Asset.id)
    if site_id is not None:
        stmt = stmt.where(Asset.site_id == site_id)
    if kind is not None:
        stmt = stmt.where(Asset.kind == kind)
    with orm.Session(engine) as session:
        return [_to_dict(row) for row in session.scalars(stmt)]


def get_site(
    engine: sa.Engine,
    site_id: str,
) -> dict:
    """
    Get one site with its ``assets`` and assigned ``technicians``.

    :raises ValueError: if the site does not exist.
    """
    with orm.Session(engine) as session:
        site = _get(session, Site, site_id, "site")
        stmt = (
            sa.select(Technician)
            .join(SiteTechnician, SiteTechnician.technician_id == Technician.id)
            .where(SiteTechnician.site_id == site_id)
            .order_by(Technician.id)
        )
        technicians = [_to_dict(row) for row in session.scalars(stmt)]
    site["assets"] = list_assets(engine, site_id=site_id)
    site["technicians"] = technicians
    return site


def get_technician(
    engine: sa.Engine,
    technician_id: str,
) -> dict:
    """
    Get one technician with the ``sites`` they are assigned to.

    :raises ValueError: if the technician does not exist.
    """
    with orm.Session(engine) as session:
        technician = _get(session, Technician, technician_id, "technician")
        stmt = (
            sa.select(Site)
            .join(SiteTechnician, SiteTechnician.site_id == Site.id)
            .where(SiteTechnician.technician_id == technician_id)
            .order_by(Site.id)
        )
        technician["sites"] = [_to_dict(row) for row in session.scalars(stmt)]
    return technician
