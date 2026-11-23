"""
db_connection/connection_utils.py
------------------------------------
Point d'entrée unique (factory) pour obtenir une connexion, quel que soit
le type de base de données. Évite d'importer manuellement le bon connecteur
partout dans le code : un seul appel suffit.

Usage:
    from db_connection.connection_utils import get_engine

    engine = get_engine("postgresql")   # ou "mysql", "sqlite", "supabase"
"""

from __future__ import annotations

from typing import Literal

from sqlalchemy.engine import Engine

from utils.logger import get_logger

logger = get_logger(__name__)

DBType = Literal["postgresql", "mysql", "sqlite", "supabase"]

_ENGINE_FACTORIES = {
    "postgresql": ("db_connection.postgresql_connector", "get_pg_engine"),
    "mysql": ("db_connection.mysql_connector", "get_mysql_engine"),
    "sqlite": ("db_connection.sqlite_connector", "get_sqlite_engine"),
    "supabase": ("db_connection.supabase_connector", "get_supabase_sql_engine"),
}


def get_engine(db_type: DBType) -> Engine:
    """
    Retourne un moteur SQLAlchemy pour le type de base demandé.

    Args:
        db_type: "postgresql" | "mysql" | "sqlite" | "supabase"

    Raises:
        ValueError: si db_type n'est pas reconnu.
    """
    factory = _ENGINE_FACTORIES.get(db_type)
    if factory is None:
        raise ValueError(
            f"Type de base inconnu : '{db_type}'. "
            f"Valeurs acceptées : {list(_ENGINE_FACTORIES.keys())}"
        )
    logger.info("Création du moteur de connexion pour : %s", db_type)
    from importlib import import_module
    module, function = factory
    return getattr(import_module(module), function)()


class DatabaseSession:
    """
    Context manager pratique pour ouvrir/fermer proprement une connexion,
    quel que soit le type de base.

    Usage:
        with DatabaseSession("sqlite") as engine:
            df = pd.read_sql("SELECT * FROM users", engine)
    """

    def __init__(self, db_type: DBType):
        self.db_type = db_type
        self.engine: Engine | None = None

    def __enter__(self) -> Engine:
        self.engine = get_engine(self.db_type)
        return self.engine

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.engine is not None:
            self.engine.dispose()
            logger.info("Connexion '%s' proprement fermée.", self.db_type)
