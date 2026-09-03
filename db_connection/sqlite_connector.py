"""
db_connection/sqlite_connector.py
------------------------------------
Connexion à une base SQLite locale (fichier unique, pas de serveur).
Idéal pour prototyper, faire des tests, ou du stockage embarqué.

- `get_sqlite_connection()` -> connexion brute via le module standard `sqlite3`.
- `get_sqlite_engine()`     -> moteur SQLAlchemy (pratique avec pandas).
"""

from __future__ import annotations

import os
import sqlite3
from sqlite3 import Connection as SQLiteConnection

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from utils.env_loader import SQLiteConfig
from utils.logger import get_logger

logger = get_logger(__name__)


def get_sqlite_connection() -> SQLiteConnection:
    """
    Connexion SQLite brute. Crée automatiquement le dossier/fichier si absent.
    """
    config = SQLiteConfig()
    try:
        os.makedirs(os.path.dirname(config.path) or ".", exist_ok=True)
        conn = sqlite3.connect(config.path)
        conn.row_factory = sqlite3.Row  # permet d'accéder aux colonnes par nom (row["col"])
        logger.info("Connexion SQLite établie sur '%s'.", config.path)
        return conn
    except sqlite3.Error as exc:
        logger.error("Échec de connexion SQLite : %s", exc)
        raise ConnectionError("Impossible d'ouvrir la base SQLite.") from exc


def get_sqlite_engine() -> Engine:
    """
    Moteur SQLAlchemy pour SQLite.
    """
    config = SQLiteConfig()
    os.makedirs(os.path.dirname(config.path) or ".", exist_ok=True)
    url = f"sqlite:///{config.path}"

    try:
        engine = create_engine(url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Moteur SQLAlchemy SQLite initialisé sur '%s'.", config.path)
        return engine
    except Exception as exc:
        logger.error("Échec d'initialisation du moteur SQLite : %s", exc)
        raise ConnectionError("Impossible d'initialiser le moteur SQLite.") from exc


if __name__ == "__main__":
    conn = get_sqlite_connection()
    conn.close()
    engine = get_sqlite_engine()
    print("Connexion SQLite OK.")
