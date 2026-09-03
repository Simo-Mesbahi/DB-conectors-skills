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

from sqlalchemy import text
from sqlalchemy.engine import Engine

from utils.logger import get_logger

logger = get_logger(__name__)


# ------------------------------------------------------------------
# (A) SQL BRUT — via SQLAlchemy (fonctionne pour Postgres/MySQL/SQLite)
# ------------------------------------------------------------------

def select_all(engine: Engine, table: str) -> list[dict[str, Any]]:
    """SELECT * FROM table (à réserver aux petites tables / debug)."""
    query = text(f"SELECT * FROM {table}")  # nom de table non paramétrable en SQL -> valider en amont si dynamique
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
    query = text(f"SELECT * FROM {table} WHERE {column} = :value")
    with engine.connect() as conn:
        result = conn.execute(query, {"value": value})
        rows = [dict(row._mapping) for row in result]
    logger.info(
        "select_with_filter('%s', %s=%s) -> %s lignes.", table, column, value, len(rows)
    )
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


def select_aggregation(engine: Engine, table: str, group_by_column: str) -> list[dict[str, Any]]:
    """Exemple d'agrégation : compte + moyenne, groupés par colonne."""
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


def select_paginated(engine: Engine, table: str, page: int = 1, page_size: int = 50) -> list[dict[str, Any]]:
    """Pagination simple avec OFFSET/LIMIT — utile pour gros volumes de données."""
    offset = (page - 1) * page_size
    query = text(f"SELECT * FROM {table} LIMIT :limit OFFSET :offset")
    with engine.connect() as conn:
        result = conn.execute(query, {"limit": page_size, "offset": offset})
        rows = [dict(row._mapping) for row in result]
    logger.info("select_paginated('%s', page=%s) -> %s lignes.", table, page, len(rows))
    return rows


# ------------------------------------------------------------------
# (B) CLIENT SUPABASE — via l'API REST auto-générée (PostgREST)
# ------------------------------------------------------------------

def supabase_select_all(client, table: str) -> list[dict[str, Any]]:
    """Équivalent select_all() mais via le SDK Supabase (API REST)."""
    response = client.table(table).select("*").execute()
    logger.info("supabase_select_all('%s') -> %s lignes.", table, len(response.data))
    return response.data


def supabase_select_with_filter(client, table: str, column: str, value: Any) -> list[dict[str, Any]]:
    """Équivalent select_with_filter() via le SDK Supabase."""
    response = client.table(table).select("*").eq(column, value).execute()
    logger.info(
        "supabase_select_with_filter('%s', %s=%s) -> %s lignes.",
        table, column, value, len(response.data),
    )
    return response.data


def supabase_select_paginated(client, table: str, page: int = 1, page_size: int = 50) -> list[dict[str, Any]]:
    """Pagination via .range() du SDK Supabase."""
    start = (page - 1) * page_size
    end = start + page_size - 1
    response = client.table(table).select("*").range(start, end).execute()
    logger.info("supabase_select_paginated('%s', page=%s) -> %s lignes.", table, page, len(response.data))
    return response.data
