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
    columns = ", ".join(data.keys())
    placeholders = ", ".join(f":{k}" for k in data.keys())
    query = text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")

    with engine.begin() as conn:  # engine.begin() = transaction auto (commit/rollback géré)
        conn.execute(query, data)
    logger.info("insert_row('%s') -> ligne insérée : %s", table, data)


def update_rows(engine: Engine, table: str, updates: dict[str, Any], where_column: str, where_value: Any) -> int:
    """
    Met à jour les lignes correspondant à `where_column = where_value`.
    Retourne le nombre de lignes affectées.
    """
    set_clause = ", ".join(f"{col} = :set_{col}" for col in updates.keys())
    params = {f"set_{col}": val for col, val in updates.items()}
    params["where_value"] = where_value

    query = text(f"UPDATE {table} SET {set_clause} WHERE {where_column} = :where_value")

    with engine.begin() as conn:
        result = conn.execute(query, params)
    logger.info("update_rows('%s') -> %s lignes modifiées.", table, result.rowcount)
    return result.rowcount


def delete_rows(engine: Engine, table: str, where_column: str, where_value: Any) -> int:
    """Supprime les lignes correspondant au filtre. Retourne le nombre de lignes supprimées."""
    query = text(f"DELETE FROM {table} WHERE {where_column} = :value")

    with engine.begin() as conn:
        result = conn.execute(query, {"value": where_value})
    logger.info("delete_rows('%s') -> %s lignes supprimées.", table, result.rowcount)
    return result.rowcount


def bulk_insert(engine: Engine, table: str, rows: list[dict[str, Any]]) -> None:
    """
    Insertion en masse (plus performant qu'une boucle d'insert_row()).
    Toutes les lignes de `rows` doivent avoir les mêmes clés.
    """
    if not rows:
        logger.warning("bulk_insert('%s') appelé avec une liste vide, rien à faire.", table)
        return

    columns = ", ".join(rows[0].keys())
    placeholders = ", ".join(f":{k}" for k in rows[0].keys())
    query = text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")

    with engine.begin() as conn:
        conn.execute(query, rows)  # SQLAlchemy exécute en batch avec une liste de dicts
    logger.info("bulk_insert('%s') -> %s lignes insérées.", table, len(rows))


# ------------------------------------------------------------------
# (B) CLIENT SUPABASE
# ------------------------------------------------------------------

def supabase_insert(client, table: str, data: dict[str, Any] | list[dict[str, Any]]):
    """Insert simple ou multiple via le SDK Supabase."""
    response = client.table(table).insert(data).execute()
    logger.info("supabase_insert('%s') -> %s lignes insérées.", table, len(response.data))
    return response.data


def supabase_update(client, table: str, updates: dict[str, Any], column: str, value: Any):
    """Update via le SDK Supabase (équivalent UPDATE ... WHERE column = value)."""
    response = client.table(table).update(updates).eq(column, value).execute()
    logger.info("supabase_update('%s') -> %s lignes modifiées.", table, len(response.data))
    return response.data


def supabase_delete(client, table: str, column: str, value: Any):
    """Delete via le SDK Supabase."""
    response = client.table(table).delete().eq(column, value).execute()
    logger.info("supabase_delete('%s') -> %s lignes supprimées.", table, len(response.data))
    return response.data


def supabase_upsert(client, table: str, data: dict[str, Any] | list[dict[str, Any]], on_conflict: str):
    """
    Upsert (insert si absent, update si existant) — pratique pour la synchro de données.
    `on_conflict` = nom de la colonne avec contrainte UNIQUE (ex: "email").
    """
    response = client.table(table).upsert(data, on_conflict=on_conflict).execute()
    logger.info("supabase_upsert('%s') -> %s lignes traitées.", table, len(response.data))
    return response.data
