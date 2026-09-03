"""
db_connection/postgresql_connector.py
--------------------------------------
Connexion à une base PostgreSQL "classique" (serveur auto-hébergé, RDS, etc.)

Deux options fournies :
- `get_pg_connection()`  -> connexion brute psycopg2 (curseur SQL direct).
- `get_pg_engine()`      -> moteur SQLAlchemy (ORM ou requêtes via pandas).
"""

from __future__ import annotations

import time

import psycopg2
from psycopg2.extensions import connection as PGConnection
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from utils.env_loader import PostgresConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def get_pg_connection(max_retries: int = 3, retry_delay: float = 2.0) -> PGConnection:
    """
    Connexion psycopg2 brute, avec retry automatique en cas d'échec temporaire
    (base en train de redémarrer, réseau instable, etc.).

    Args:
        max_retries: nombre de tentatives avant abandon.
        retry_delay: délai (secondes) entre deux tentatives.
    """
    config = PostgresConfig()
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(
                host=config.host,
                port=config.port,
                dbname=config.db,
                user=config.user,
                password=config.password,
                connect_timeout=5,
            )
            logger.info("Connexion PostgreSQL établie (tentative %s/%s).", attempt, max_retries)
            return conn
        except psycopg2.OperationalError as exc:
            last_error = exc
            logger.warning(
                "Échec de connexion PostgreSQL (tentative %s/%s) : %s", attempt, max_retries, exc
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.error("Impossible de se connecter à PostgreSQL après %s tentatives.", max_retries)
    raise ConnectionError(f"Connexion PostgreSQL impossible : {last_error}")


def get_pg_engine(pool_size: int = 5, max_overflow: int = 10) -> Engine:
    """
    Moteur SQLAlchemy pour PostgreSQL, avec pool de connexions.
    Recommandé pour un usage combiné avec pandas (pd.read_sql).
    """
    config = PostgresConfig()
    url = f"postgresql+psycopg2://{config.user}:{config.password}@{config.host}:{config.port}/{config.db}"

    try:
        engine = create_engine(
            url,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Moteur SQLAlchemy PostgreSQL initialisé avec succès.")
        return engine
    except Exception as exc:
        logger.error("Échec d'initialisation du moteur PostgreSQL : %s", exc)
        raise ConnectionError("Impossible d'initialiser le moteur PostgreSQL.") from exc


if __name__ == "__main__":
    conn = get_pg_connection()
    conn.close()
    engine = get_pg_engine()
    print("Connexion PostgreSQL OK.")
