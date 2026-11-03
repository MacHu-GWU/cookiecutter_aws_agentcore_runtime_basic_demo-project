# -*- coding: utf-8 -*-

"""
Read-only queries over the fake power plant database, exposed as MCP tools.

Every function returns plain JSON-friendly dicts (copies, so callers cannot change the data).
"""

from __future__ import annotations

from .data import SITES
from .data import ASSETS
from .data import TECHNICIANS
from .data import SITE_TECHNICIANS


def _find(table: list[dict], id: str, table_name: str) -> dict:
    for row in table:
        if row["id"] == id:
            return dict(row)
    raise ValueError(f"{table_name} {id!r} not found")


def list_sites(kind: str | None = None) -> list[dict]:
    """
    List all sites, optionally only those of one ``kind`` (``solar`` or ``wind``).
    """
    rows = []
    for row in SITES:
        if kind is None or row["kind"] == kind:
            rows.append(dict(row))
    return rows


def list_assets(
    site_id: str | None = None,
    kind: str | None = None,
) -> list[dict]:
    """
    List assets, optionally filtered by ``site_id`` and / or ``kind``.
    """
    rows = []
    for row in ASSETS:
        if site_id is not None and row["site_id"] != site_id:
            continue
        if kind is not None and row["kind"] != kind:
            continue
        rows.append(dict(row))
    return rows


def get_site(site_id: str) -> dict:
    """
    Get one site with its ``assets`` and assigned ``technicians``.

    :raises ValueError: if the site does not exist.
    """
    site = _find(SITES, site_id, "site")
    site["assets"] = list_assets(site_id=site_id)
    technicians = []
    for link in SITE_TECHNICIANS:
        if link["site_id"] == site_id:
            technicians.append(_find(TECHNICIANS, link["technician_id"], "technician"))
    site["technicians"] = technicians
    return site


def get_technician(technician_id: str) -> dict:
    """
    Get one technician with the ``sites`` they are assigned to.

    :raises ValueError: if the technician does not exist.
    """
    technician = _find(TECHNICIANS, technician_id, "technician")
    sites = []
    for link in SITE_TECHNICIANS:
        if link["technician_id"] == technician_id:
            sites.append(_find(SITES, link["site_id"], "site"))
    technician["sites"] = sites
    return technician
