from contextlib import closing

import pytest
from sqlalchemy import create_engine, text

from queries.select_queries import iter_rows


@pytest.fixture
def engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'stream.sqlite'}", pool_size=1, max_overflow=0)
    with engine.begin() as connection:
        connection.execute(text('CREATE TABLE items (id INTEGER PRIMARY KEY, "order" TEXT)'))
        connection.execute(text('INSERT INTO items VALUES (:id, :value)'),
                           [{"id": n, "value": f"value-{n}"} for n in reversed(range(105))])
    yield engine
    assert engine.pool.checkedout() == 0
    engine.dispose()


def test_stream_reads_all_rows_in_order_and_releases_the_connection(engine):
    result = list(iter_rows(engine, "items", batch_size=7))
    assert [row["id"] for row in result] == list(range(105))
    assert result[-1]["order"] == "value-104"
    assert engine.pool.checkedout() == 0


def test_early_exit_and_consumer_failure_release_the_connection(engine):
    with pytest.raises(RuntimeError, match="consumer failure"):
        with closing(iter_rows(engine, "items", batch_size=3)) as rows:
            assert next(rows)["id"] == 0
            assert engine.pool.checkedout() == 1
            raise RuntimeError("consumer failure")
    assert engine.pool.checkedout() == 0


@pytest.mark.parametrize("kwargs", [{"batch_size": 0}, {"batch_size": True},
                                  {"batch_size": 1001}, {"order_by": "id; DROP TABLE items"}])
def test_invalid_stream_contract_is_rejected_without_leaking_connections(engine, kwargs):
    with pytest.raises(ValueError):
        list(iter_rows(engine, "items", **kwargs))
    assert engine.pool.checkedout() == 0
