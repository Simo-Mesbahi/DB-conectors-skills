"""
db_connection/supabase_connector.py
------------------------------------
Deux façons de se connecter à Supabase, chacune avec son cas d'usage :

1. `get_supabase_client()`   -> via le SDK officiel `supabase-py`.
   Utilise l'API REST auto-générée (PostgREST) + Auth + Realtime + Storage.
   Recommandé pour la majorité des usages applicatifs.

2. `get_supabase_sql_engine()` -> connexion SQL directe (SQLAlchemy / psycopg2).
   Utile pour des requêtes SQL complexes (jointures avancées, fonctions
   PostgreSQL natives, migrations) que l'API REST ne permet pas facilement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from supabase import Client
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from utils.env_loader import SupabaseConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def get_supabase_client() -> Client:
    """
    Retourne un client Supabase prêt à l'emploi (API REST + Auth + Realtime).

    Exemple:
        client = get_supabase_client()
        response = client.table("users").select("*").execute()
    """
    from supabase import create_client
    config = SupabaseConfig()
    try:
        client = create_client(config.url, config.key)
        logger.info("Connexion Supabase (client SDK) établie avec succès.")
        return client
    except Exception as exc:
        logger.error("Échec de connexion au client Supabase : %s", exc)
        raise ConnectionError("Impossible d'initialiser le client Supabase.") from exc


def get_supabase_sql_engine(pool_size: int = 5, max_overflow: int = 10) -> Engine:
    """
    Retourne un moteur SQLAlchemy connecté directement à la base Postgres
    sous-jacente de Supabase (utile pour du SQL brut ou des requêtes avancées).

    Args:
        pool_size: nombre de connexions maintenues dans le pool.
        max_overflow: connexions supplémentaires autorisées en pic de charge.
    """
    config = SupabaseConfig(sql=True)
    try:
        engine = create_engine(
            config.db_url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # vérifie que la connexion est vivante avant usage (évite les timeouts silencieux)
            pool_recycle=1800,   # recycle les connexions toutes les 30 min
        )
        # Test de connexion immédiat pour échouer vite si la config est mauvaise
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        logger.info("Connexion SQL directe à Supabase (Postgres) établie avec succès.")
        return engine
    except Exception as exc:
        logger.error("Échec de connexion SQL directe à Supabase : %s", exc)
        raise ConnectionError("Impossible d'établir la connexion SQL à Supabase.") from exc


if __name__ == "__main__":
    # Petit auto-test manuel : python -m db_connection.supabase_connector
    client = get_supabase_client()
    engine = get_supabase_sql_engine()
    print("Client SDK :", client)
    print("Engine SQL :", engine)
