"""
queries/select_queries.py
----------------------------
Exemples de requêtes SELECT, du plus simple au plus avancé, avec DEUX
approches systématiquement montrées :
  (A) SQL brut via SQLAlchemy   -> flexible, performant, requêtes complexes
  (B) Client Supabase (PostgREST) -> pratique pour du CRUD simple côté API

Toutes les fonctions retournent des données "brutes" (liste de tuples/dicts).
La transformation en DataFrame/exploitation se fait dans data_processing/.
"""

from __future__ import annotations

from typing import Any
from collections.abc import Iterator

from sqlalchemy import text
from sqlalchemy.engine import Engine
from queries.identifiers import identifier, pagination

from utils.logger import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# (A) SQL BRUT — via SQLAlchemy (fonctionne pour Postgres/MySQL/SQLite)
# ------------------------------------------------------------------


def select_all(engine: Engine, table: str) -> list[dict[str, Any]]:
    """SELECT * FROM table (à réserver aux petites tables / debug)."""
    query = text(
        f"SELECT * FROM {identifier(engine, table, qualified=True)}"
    )  # nom de table non paramétrable en SQL -> valider en amont si dynamique
    with engine.connect() as conn:
        result = conn.execute(query)
        rows = [dict(row._mapping) for row in result]
    logger.info("select_all('%s') -> %s lignes récupérées.", table, len(rows))
    return rows


def select_with_filter(
    engine: Engine, table: str, column: str, value: Any
) -> list[dict[str, Any]]:
    """
    SELECT filtré avec requête PARAMÉTRÉE (protection anti-injection SQL).
    Ne JAMAIS faire de f-string avec une valeur utilisateur dans le WHERE.
    """
    query = text(
        f"SELECT * FROM {identifier(engine, table, qualified=True)} WHERE {identifier(engine, column)} = :value"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"value": value})
        rows = [dict(row._mapping) for row in result]
    logger.info("select_with_filter(%s): column=%s, rows=%s", table, column, len(rows))
    return rows


def select_with_join(engine: Engine) -> list[dict[str, Any]]:
    """
    Exemple de jointure avancée : commandes + clients + total par commande.
    Adapte les noms de tables/colonnes à ton propre schéma.
    """
    query = text(
        """
        SELECT
            o.id            AS order_id,
            c.name          AS customer_name,
            o.total_amount,
            o.created_at
        FROM orders o
        JOIN customers c ON c.id = o.customer_id
        WHERE o.total_amount > :min_amount
        ORDER BY o.created_at DESC
        LIMIT :limit
        """
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"min_amount": 0, "limit": 100})
        rows = [dict(row._mapping) for row in result]
    logger.info("select_with_join() -> %s lignes.", len(rows))
    return rows


def select_aggregation(
    engine: Engine, table: str, group_by_column: str
) -> list[dict[str, Any]]:
    """Exemple d'agrégation : compte + moyenne, groupés par colonne."""
    table = identifier(engine, table, qualified=True)
    group_by_column = identifier(engine, group_by_column)
    query = text(
        f"""
        SELECT
            {group_by_column},
            COUNT(*) AS total_rows
        FROM {table}
        GROUP BY {group_by_column}
        ORDER BY total_rows DESC
        """
    )
    with engine.connect() as conn:
        result = conn.execute(query)
        rows = [dict(row._mapping) for row in result]
    logger.info("select_aggregation('%s') -> %s groupes.", table, len(rows))
    return rows


def select_paginated(
    engine: Engine,
    table: str,
    page: int = 1,
    page_size: int = 50,
    *,
    order_by: str = "id",
) -> list[dict[str, Any]]:
    """Pagination simple avec OFFSET/LIMIT — utile pour gros volumes de données."""
    offset = pagination(page, page_size)
    query = text(
        f"SELECT * FROM {identifier(engine, table, qualified=True)} ORDER BY {identifier(engine, order_by)} LIMIT :limit OFFSET :offset"
    )
    with engine.connect() as conn:
        result = conn.execute(query, {"limit": page_size, "offset": offset})
        rows = [dict(row._mapping) for row in result]
    logger.info("select_paginated('%s', page=%s) -> %s lignes.", table, page, len(rows))
    return rows


def iter_rows(
    engine: Engine,
    table: str,
    *,
    batch_size: int = 1000,
    order_by: str = "id",
) -> Iterator[dict[str, Any]]:
    """Read ordered rows in batches, keeping one connection until closed.

    Use a unique ordering key. Drivers supporting server-side cursors receive
    yield_per; other drivers may still buffer internally. Close an unfinished
    iterator explicitly (for example with contextlib.closing).
    """
    pagination(1, batch_size)
    statement = text(
        f"SELECT * FROM {identifier(engine, table, qualified=True)} "
        f"ORDER BY {identifier(engine, order_by)}"
    )
    with engine.connect().execution_options(yield_per=batch_size) as connection:
        with connection.execute(statement) as result:
            for partition in result.mappings().partitions(batch_size):
                for row in partition:
                    yield dict(row)


# ------------------------------------------------------------------
# (B) CLIENT SUPABASE — via l'API REST auto-générée (PostgREST)
# ------------------------------------------------------------------


def supabase_select_all(client, table: str) -> list[dict[str, Any]]:
    """Équivalent select_all() mais via le SDK Supabase (API REST)."""
    response = client.table(table).select("*").execute()
    logger.info("supabase_select_all('%s') -> %s lignes.", table, len(response.data))
    return response.data


def supabase_select_with_filter(
    client, table: str, column: str, value: Any
) -> list[dict[str, Any]]:
    """Équivalent select_with_filter() via le SDK Supabase."""
    response = client.table(table).select("*").eq(column, value).execute()
    logger.info(
        "supabase_select_with_filter(%s): column=%s, rows=%s",
        table,
        column,
        len(response.data),
    )
    return response.data


def supabase_select_paginated(
    client, table: str, page: int = 1, page_size: int = 50
) -> list[dict[str, Any]]:
    """Pagination via .range() du SDK Supabase."""
    start = pagination(page, page_size)
    end = start + page_size - 1
    response = client.table(table).select("*").range(start, end).execute()
    logger.info(
        "supabase_select_paginated('%s', page=%s) -> %s lignes.",
        table,
        page,
        len(response.data),
    )
    return response.data


def select_after_id(
    engine: Engine,
    table: str,
    after_id: int = 0,
    page_size: int = 100,
    *,
    id_column: str = "id",
) -> list[dict[str, Any]]:
    """Indexed keyset pagination. id_column must be a unique, immutable integer key."""
    pagination(1, page_size)
    if type(after_id) is not int:
        raise ValueError("after_id must be an integer")
    name = identifier(engine, table, qualified=True)
    key = identifier(engine, id_column)
    with engine.connect() as conn:
        result = conn.execute(
            text(
                f"SELECT * FROM {name} WHERE {key} > :cursor ORDER BY {key} LIMIT :size"
            ),
            {"cursor": after_id, "size": page_size},
        )
        return [dict(row._mapping) for row in result]
