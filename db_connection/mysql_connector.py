"""
db_connection/mysql_connector.py
----------------------------------
Connexion à une base MySQL / MariaDB.

- `get_mysql_connection()` -> connexion brute via mysql-connector-python.
- `get_mysql_engine()`     -> moteur SQLAlchemy (via PyMySQL) pour usage avec pandas/ORM.
"""

from __future__ import annotations

import time

import mysql.connector
from mysql.connector.connection import MySQLConnection
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL

from utils.env_loader import MySQLConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def get_mysql_connection(max_retries: int = 3, retry_delay: float = 2.0) -> MySQLConnection:
    """
    Connexion MySQL brute avec retry automatique.
    """
    config = MySQLConfig()
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            conn = mysql.connector.connect(
                host=config.host,
                port=int(config.port),
                database=config.db,
                user=config.user,
                password=config.password,
                connection_timeout=5,
            )
            logger.info("Connexion MySQL établie (tentative %s/%s).", attempt, max_retries)
            return conn
        except mysql.connector.Error as exc:
            last_error = exc
            logger.warning(
                "Échec de connexion MySQL (tentative %s/%s) : %s", attempt, max_retries, exc
            )
            if attempt < max_retries:
                time.sleep(retry_delay)

    logger.error("Impossible de se connecter à MySQL après %s tentatives.", max_retries)
    raise ConnectionError(f"Connexion MySQL impossible : {last_error}")


def get_mysql_engine(pool_size: int = 5, max_overflow: int = 10) -> Engine:
    """
    Moteur SQLAlchemy pour MySQL (driver PyMySQL), avec pool de connexions.
    """
    config = MySQLConfig()
    url = URL.create("mysql+pymysql", username=config.user, password=config.password, host=config.host, port=int(config.port), database=config.db)

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
        logger.info("Moteur SQLAlchemy MySQL initialisé avec succès.")
        return engine
    except Exception as exc:
        logger.error("Échec d'initialisation du moteur MySQL : %s", exc)
        raise ConnectionError("Impossible d'initialiser le moteur MySQL.") from exc


if __name__ == "__main__":
    conn = get_mysql_connection()
    conn.close()
    engine = get_mysql_engine()
    print("Connexion MySQL OK.")
