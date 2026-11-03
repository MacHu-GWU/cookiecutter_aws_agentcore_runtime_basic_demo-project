# -*- coding: utf-8 -*-

from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import Site
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import SiteTechnician
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import (
    is_in_memory_sqlite,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import (
    create_db_engine,
)
from cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm import (
    load_seed_data,
)

import threading

import pytest
import sqlalchemy as sa
import sqlalchemy.orm as orm


@pytest.mark.parametrize(
    "url, expected",
    [
        ("sqlite://", True),
        ("sqlite+pysqlite:///:memory:", True),
        ("sqlite:///path/to/file.db", False),
        ("postgresql+psycopg://user:pwd@host/db", False),
    ],
)
def test_is_in_memory_sqlite(url, expected):
    assert is_in_memory_sqlite(url) is expected


def count(engine: sa.Engine, model) -> int:
    with orm.Session(engine) as session:
        return session.scalar(sa.select(sa.func.count()).select_from(model))


def test_load_seed_data_is_idempotent():
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    load_seed_data(engine)
    load_seed_data(engine)
    assert count(engine, Site) == 5
    assert count(engine, SiteTechnician) == 8


def test_in_memory_database_is_shared_across_threads():
    """Every connection, from any thread, sees the same in-memory database."""
    engine = create_db_engine("sqlite+pysqlite:///:memory:")
    load_seed_data(engine)
    results = []
    thread = threading.Thread(target=lambda: results.append(count(engine, Site)))
    thread.start()
    thread.join()
    assert results == [5]


if __name__ == "__main__":
    from cookiecutter_aws_agentcore_runtime_basic_demo.tests import run_cov_test

    run_cov_test(
        __file__,
        "cookiecutter_aws_agentcore_runtime_basic_demo.power_plant.orm",
        preview=False,
    )
