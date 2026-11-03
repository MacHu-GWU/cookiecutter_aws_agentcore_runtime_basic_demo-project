# -*- coding: utf-8 -*-

"""
The power plant database: SQLAlchemy models of the 4 tables, with their
relationships, the engine, and the seed data load. What the queries return is
not these models but those of
:mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.schemas`.

The demo runs on an in-memory SQLite database (``sqlite+pysqlite:///:memory:``),
filled from :mod:`~cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.data`
when the engine is created. A real project points ``db_connection_string`` of
the config at its database and drops the seed load.
"""

from __future__ import annotations

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.pool import StaticPool

from .data import SITES
from .data import ASSETS
from .data import TECHNICIANS
from .data import SITE_TECHNICIANS


class Base(orm.DeclarativeBase):
    """
    The declarative base of every table.
    """

    #: The tables of every model; ``Base.metadata.create_all(engine)`` creates them.
    metadata = sa.MetaData()


class Site(Base):
    """
    A power plant site. ``kind`` is ``solar`` or ``wind``.
    """

    __tablename__ = "sites"

    # fmt: off
    id: orm.Mapped[str] = orm.mapped_column(sa.String, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(sa.String)
    kind: orm.Mapped[str] = orm.mapped_column(sa.String)
    lat: orm.Mapped[float] = orm.mapped_column(sa.Float)
    lon: orm.Mapped[float] = orm.mapped_column(sa.Float)
    capacity_mw: orm.Mapped[int] = orm.mapped_column(sa.Integer)
    # fmt: on

    # fmt: off
    assets: orm.Mapped[list[Asset]] = orm.relationship(back_populates="site", order_by="Asset.id")
    technicians: orm.Mapped[list[Technician]] = orm.relationship(secondary="site_technicians", back_populates="sites", order_by="Technician.id")
    # fmt: on


class Asset(Base):
    """
    Equipment at a site; each asset belongs to exactly one site.
    """

    __tablename__ = "assets"

    # fmt: off
    id: orm.Mapped[str] = orm.mapped_column(sa.String, primary_key=True)
    site_id: orm.Mapped[str] = orm.mapped_column(sa.ForeignKey("sites.id"))
    kind: orm.Mapped[str] = orm.mapped_column(sa.String)
    model: orm.Mapped[str] = orm.mapped_column(sa.String)
    # fmt: on

    # fmt: off
    site: orm.Mapped[Site] = orm.relationship(back_populates="assets")
    # fmt: on


class Technician(Base):
    """
    A field technician who inspects sites.
    """

    __tablename__ = "technicians"

    # fmt: off
    id: orm.Mapped[str] = orm.mapped_column(sa.String, primary_key=True)
    name: orm.Mapped[str] = orm.mapped_column(sa.String)
    skill: orm.Mapped[str] = orm.mapped_column(sa.String)
    # fmt: on

    # fmt: off
    sites: orm.Mapped[list[Site]] = orm.relationship(secondary="site_technicians", back_populates="technicians", order_by="Site.id")
    # fmt: on


class SiteTechnician(Base):
    """
    Which technician is assigned to which site (the many-to-many link table).
    """

    __tablename__ = "site_technicians"

    # fmt: off
    site_id: orm.Mapped[str] = orm.mapped_column(sa.ForeignKey("sites.id"), primary_key=True)
    technician_id: orm.Mapped[str] = orm.mapped_column(sa.ForeignKey("technicians.id"), primary_key=True)
    # fmt: on


#: Each model with its seed rows, parents before children.
SEED_DATA: list[tuple[type[Base], list[dict]]] = [
    (Site, SITES),
    (Asset, ASSETS),
    (Technician, TECHNICIANS),
    (SiteTechnician, SITE_TECHNICIANS),
]


def is_in_memory_sqlite(url: str) -> bool:
    """
    Whether ``url`` is an in-memory SQLite database, such as ``sqlite://`` or
    ``sqlite+pysqlite:///:memory:``.
    """
    url_obj = sa.make_url(url)
    return url_obj.get_backend_name() == "sqlite" and url_obj.database in (
        None,
        "",
        ":memory:",
    )


def create_db_engine(url: str) -> sa.Engine:
    """
    The engine of the database at ``url``.

    An in-memory SQLite database lives in one connection and disappears with it,
    so it gets one shared connection (``StaticPool``), usable from any thread:
    the MCP server answers requests on worker threads.
    """
    if is_in_memory_sqlite(url):
        return sa.create_engine(
            url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
    return sa.create_engine(url)  # pragma: no cover


def load_seed_data(engine: sa.Engine) -> None:
    """
    Create the tables if missing, and write the seed rows. Idempotent: a row is
    inserted, or updated to the seed values, by its primary key (``merge``), so
    loading twice leaves the same data.
    """
    Base.metadata.create_all(engine)
    with orm.Session(engine) as session:
        for model, rows in SEED_DATA:
            for row in rows:
                session.merge(model(**row))
        session.commit()
