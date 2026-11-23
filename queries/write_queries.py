"""
queries/write_queries.py
----------------------------
Requêtes d'écriture : INSERT, UPDATE, DELETE.
Toujours paramétrées -> aucune valeur utilisateur n'est jamais concaténée
directement dans la chaîne SQL (protection anti-injection).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from queries.identifiers import identifier
from utils.logger import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# (A) SQL BRUT
# ------------------------------------------------------------------


def insert_row(engine: Engine, table: str, data: dict[str, Any]) -> None:
    """
    Insère une ligne. `data` = {"colonne": valeur, ...}.

    Exemple:
        insert_row(engine, "users", {"name": "Simo", "email": "simo@test.com"})
    """
    if not data:
        raise ValueError("data must not be empty")
    table = identifier(engine, table, qualified=True)
    columns = ", ".join(identifier(engine, key) for key in data)
    placeholders = ", ".join(f":{k}" for k in data.keys())
    query = text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")

    with (
        engine.begin() as conn
    ):  # engine.begin() = transaction auto (commit/rollback géré)
        conn.execute(query, data)
    logger.info("insert_row(%s): one row inserted", table)


def update_rows(
    engine: Engine,
    table: str,
    updates: dict[str, Any],
    where_column: str,
    where_value: Any,
) -> int:
    """
    Met à jour les lignes correspondant à `where_column = where_value`.
    Retourne le nombre de lignes affectées.
    """
    if not updates:
        raise ValueError("updates must not be empty")
    table = identifier(engine, table, qualified=True)
    where_column = identifier(engine, where_column)
    set_clause = ", ".join(f"{identifier(engine, col)} = :set_{col}" for col in updates)
    params = {f"set_{col}": val for col, val in updates.items()}
    if where_value is not None:
        params["where_value"] = where_value
    predicate = (
        f"{where_column} IS NULL"
        if where_value is None
        else f"{where_column} = :where_value"
    )
    query = text(f"UPDATE {table} SET {set_clause} WHERE {predicate}")

    with engine.begin() as conn:
        result = conn.execute(query, params)
    logger.info("update_rows('%s') -> %s lignes modifiées.", table, result.rowcount)
    return result.rowcount


def delete_rows(engine: Engine, table: str, where_column: str, where_value: Any) -> int:
    """Supprime les lignes correspondant au filtre. Retourne le nombre de lignes supprimées."""
    table = identifier(engine, table, qualified=True)
    where_column = identifier(engine, where_column)
    predicate = (
        f"{where_column} IS NULL" if where_value is None else f"{where_column} = :value"
    )
    query = text(f"DELETE FROM {table} WHERE {predicate}")

    with engine.begin() as conn:
        result = conn.execute(
            query, {} if where_value is None else {"value": where_value}
        )
    logger.info("delete_rows('%s') -> %s lignes supprimées.", table, result.rowcount)
    return result.rowcount


def bulk_insert(engine: Engine, table: str, rows, *, batch_size: int = 1000) -> None:
    """Consume an iterable in bounded batches within ONE atomic transaction."""
    from itertools import islice

    if type(batch_size) is not int or not 1 <= batch_size <= 10000:
        raise ValueError("batch_size must be between 1 and 10000")
    table = identifier(engine, table, qualified=True)
    source = iter(rows)
    sentinel = object()
    first = next(source, sentinel)
    if first is sentinel:
        return
    if not isinstance(first, dict) or not first:
        raise ValueError("rows must contain nonempty dictionaries")
    keys = set(first)
    columns = ", ".join(identifier(engine, key) for key in first)
    placeholders = ", ".join(f":{key}" for key in first)
    statement = text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")
    from itertools import chain

    source = chain([first], source)
    count = 0
    with engine.begin() as conn:
        while batch := list(islice(source, batch_size)):
            if any(not isinstance(row, dict) or set(row) != keys for row in batch):
                raise ValueError("All rows must have the same keys")
            conn.execute(statement, batch)
            count += len(batch)
    logger.info("bulk_insert(%s): %s rows inserted", table, count)


# ------------------------------------------------------------------
# (B) CLIENT SUPABASE
# ------------------------------------------------------------------


def supabase_insert(client, table: str, data: dict[str, Any] | list[dict[str, Any]]):
    """Insert simple ou multiple via le SDK Supabase."""
    response = client.table(table).insert(data).execute()
    logger.info(
        "supabase_insert('%s') -> %s lignes insérées.", table, len(response.data)
    )
    return response.data


def supabase_update(
    client, table: str, updates: dict[str, Any], column: str, value: Any
):
    """Update via le SDK Supabase (équivalent UPDATE ... WHERE column = value)."""
    response = client.table(table).update(updates).eq(column, value).execute()
    logger.info(
        "supabase_update('%s') -> %s lignes modifiées.", table, len(response.data)
    )
    return response.data


def supabase_delete(client, table: str, column: str, value: Any):
    """Delete via le SDK Supabase."""
    response = client.table(table).delete().eq(column, value).execute()
    logger.info(
        "supabase_delete('%s') -> %s lignes supprimées.", table, len(response.data)
    )
    return response.data


def supabase_upsert(
    client, table: str, data: dict[str, Any] | list[dict[str, Any]], on_conflict: str
):
    """
    Upsert (insert si absent, update si existant) — pratique pour la synchro de données.
    `on_conflict` = nom de la colonne avec contrainte UNIQUE (ex: "email").
    """
    response = client.table(table).upsert(data, on_conflict=on_conflict).execute()
    logger.info(
        "supabase_upsert('%s') -> %s lignes traitées.", table, len(response.data)
    )
    return response.data
