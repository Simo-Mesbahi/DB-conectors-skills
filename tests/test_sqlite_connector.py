"""
tests/test_sqlite_connector.py
----------------------------------
Tests d'intégration légers sur le connecteur SQLite (aucun credential externe
requis, contrairement à Supabase/PostgreSQL/MySQL qui nécessitent un serveur).

Lancer avec : pytest tests/
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import text


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch, tmp_path):
    """Redirige SQLITE_DB_PATH vers un fichier temporaire pour ne pas polluer le vrai projet."""
    test_db = tmp_path / "test.db"
    monkeypatch.setenv("SQLITE_DB_PATH", str(test_db))
    yield


def test_get_sqlite_connection_creates_file(tmp_path):
    from db_connection.sqlite_connector import get_sqlite_connection

    conn = get_sqlite_connection()
    assert conn is not None
    conn.close()


def test_get_sqlite_engine_executes_query():
    from db_connection.sqlite_connector import get_sqlite_engine

    engine = get_sqlite_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS value")).scalar_one()
    assert result == 1


def test_write_and_read_queries():
    from db_connection.sqlite_connector import get_sqlite_engine
    from queries.write_queries import insert_row
    from queries.select_queries import select_all

    engine = get_sqlite_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t_users (id INTEGER PRIMARY KEY, name TEXT)"))

    insert_row(engine, "t_users", {"name": "Test User"})
    rows = select_all(engine, "t_users")

    assert len(rows) == 1
    assert rows[0]["name"] == "Test User"


def test_update_and_delete_queries():
    from db_connection.sqlite_connector import get_sqlite_engine
    from queries.write_queries import insert_row, update_rows, delete_rows
    from queries.select_queries import select_all

    engine = get_sqlite_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE t_items (id INTEGER PRIMARY KEY, name TEXT, qty INTEGER)"))

    insert_row(engine, "t_items", {"name": "Widget", "qty": 5})

    updated = update_rows(engine, "t_items", {"qty": 10}, where_column="name", where_value="Widget")
    assert updated == 1

    rows = select_all(engine, "t_items")
    assert rows[0]["qty"] == 10

    deleted = delete_rows(engine, "t_items", where_column="name", where_value="Widget")
    assert deleted == 1
    assert len(select_all(engine, "t_items")) == 0
