# -*- coding: utf-8 -*-

"""
The database part of ``one``: :attr:`~cookiecutter_aws_agentcore_runtime_basic_demo.one.one_05_db.OneDbMixin.engine`.
"""

from __future__ import annotations

import typing as T
from functools import cached_property

import sqlalchemy as sa

from ..power_plant.orm import create_db_engine
from ..power_plant.orm import load_seed_data

if T.TYPE_CHECKING:  # pragma: no cover
    from .one_00_main import One


class OneDbMixin:
    """
    The lazily built SQLAlchemy engine.
    """

    @cached_property
    def engine(self: One) -> sa.Engine:
        """
        The engine of the power plant database, ``db_connection_string`` of the
        config, created once per process on first access, with the seed data loaded.

        **One engine per process:** an engine is a connection pool, meant to be
        shared. An AgentCore runtime serves each session in its own microVM, and
        the requests of a session in the same process, so this is one engine per
        session: nothing is shared across sessions. With a real database, every
        session holds its own pool, so keep the pool small (or put RDS Proxy in
        front) to stay under the database's connection limit.
        """
        engine = create_db_engine(self.config.db_connection_string)
        load_seed_data(engine)
        return engine
