from concurrent.futures import ThreadPoolExecutor

import pytest
from sqlalchemy import create_engine, text

from queries.select_queries import select_after_id, select_paginated, select_with_filter
from queries.transactions import create_order_with_stock_update, transfer_funds
from queries.write_queries import bulk_insert, insert_row, update_rows


@pytest.fixture
def engine(tmp_path):
    db = create_engine(f"sqlite:///{tmp_path / 'contracts.db'}")
    with db.begin() as conn:
        conn.execute(
            text("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
        )
        conn.execute(
            text("CREATE TABLE accounts (id INTEGER PRIMARY KEY, balance NUMERIC)")
        )
        conn.execute(text("INSERT INTO accounts VALUES (1, 100), (2, 20)"))
        conn.execute(
            text("CREATE TABLE products (id INTEGER PRIMARY KEY, stock INTEGER)")
        )
        conn.execute(text("INSERT INTO products VALUES (1, 1)"))
        conn.execute(
            text(
                "CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER, product_id INTEGER, quantity INTEGER)"
            )
        )
    yield db
    db.dispose()


@pytest.mark.parametrize(
    "malicious",
    ["items; DROP TABLE accounts", "items --", "items WHERE 1=1", "x)y", ""],
)
def test_sql_fragments_are_rejected(engine, malicious):
    with pytest.raises(ValueError):
        insert_row(engine, malicious, {"name": "test"})
    with pytest.raises(ValueError):
        select_with_filter(engine, "items", malicious, "value")
    with pytest.raises(ValueError):
        update_rows(engine, "items", {malicious: "value"}, "id", 1)


def test_values_remain_bound_and_cursor_is_ordered(engine):
    value = "'); DROP TABLE accounts;--"
    bulk_insert(
        engine,
        "items",
        [{"id": i, "name": value + str(i)} for i in [3, 1, 2]],
        batch_size=2,
    )
    assert select_with_filter(engine, "items", "name", value + "2")[0]["id"] == 2
    assert [row["id"] for row in select_paginated(engine, "items", page_size=2)] == [
        1,
        2,
    ]
    assert [row["id"] for row in select_after_id(engine, "items", after_id=1)] == [2, 3]


def test_bulk_insert_rolls_back_previous_chunks(engine):
    with pytest.raises(ValueError, match="same keys"):
        bulk_insert(engine, "items", [{"name": "a"}, {"wrong": "b"}], batch_size=1)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM items")).scalar_one() == 0


@pytest.mark.parametrize("amount", [-1, 0, float("nan"), float("inf"), True, 1.001])
def test_invalid_money_never_changes_balances(engine, amount):
    with pytest.raises(ValueError):
        transfer_funds(engine, 1, 2, amount)
    with engine.connect() as conn:
        assert (
            conn.execute(text("SELECT balance FROM accounts WHERE id=1")).scalar_one()
            == 100
        )


def test_missing_destination_rolls_back_debit(engine):
    with pytest.raises(ValueError):
        transfer_funds(engine, 1, 999, 10)
    with engine.connect() as conn:
        assert (
            conn.execute(text("SELECT balance FROM accounts WHERE id=1")).scalar_one()
            == 100
        )


def test_transfer_and_atomic_stock_reservation(engine):
    transfer_funds(engine, 1, 2, 10)
    assert create_order_with_stock_update(engine, 1, 1, 42) == 1
    with pytest.raises(ValueError):
        create_order_with_stock_update(engine, 1, 1, 42)
    with engine.connect() as conn:
        assert (
            conn.execute(text("SELECT sum(balance) FROM accounts")).scalar_one() == 120
        )
        assert conn.execute(text("SELECT stock FROM products")).scalar_one() == 0


def test_concurrent_orders_cannot_oversell(engine):
    def buy(_):
        try:
            return create_order_with_stock_update(engine, 1, 1, 42)
        except ValueError:
            return None

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(buy, range(4)))
    assert len([value for value in results if value is not None]) == 1


@pytest.mark.parametrize(
    "kwargs", [{"page": 0}, {"page": True}, {"page_size": 0}, {"page_size": 1001}]
)
def test_pagination_limits_are_explicit(engine, kwargs):
    with pytest.raises(ValueError):
        select_paginated(engine, "items", **kwargs)


def test_sqlite_factory_does_not_require_remote_drivers(tmp_path, monkeypatch):
    from db_connection.connection_utils import get_engine

    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "factory.sqlite"))
    db = get_engine("sqlite")
    with db.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar_one() == 1
    db.dispose()


def test_explicit_empty_row_is_not_silently_ignored(engine):
    with pytest.raises(ValueError):
        bulk_insert(engine, "items", [None])
