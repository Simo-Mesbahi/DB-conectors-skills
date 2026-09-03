"""
utils/env_loader.py
--------------------
Chargement centralisé et sécurisé des variables d'environnement.

But : ne JAMAIS écrire de clés/mots de passe en dur dans le code.
Toutes les fonctions de connexion du repo passent par ce module.
"""

import os
from dotenv import load_dotenv

# Charge le fichier .env situé à la racine du projet (une seule fois).
load_dotenv()


def get_env(key: str, required: bool = True, default: str | None = None) -> str | None:
    """
    Récupère une variable d'environnement de façon contrôlée.

    Args:
        key: nom de la variable (ex: "SUPABASE_URL")
        required: si True, lève une erreur explicite si la variable est absente.
        default: valeur par défaut si la variable est optionnelle.

    Returns:
        La valeur de la variable, ou `default` si non requise et absente.

    Raises:
        EnvironmentError: si `required=True` et que la variable n'existe pas.
    """
    value = os.getenv(key, default)
    if required and not value:
        raise EnvironmentError(
            f"[Config manquante] La variable d'environnement '{key}' est requise "
            f"mais absente. Vérifie ton fichier .env (voir .env.example)."
        )
    return value


class SupabaseConfig:
    """Regroupe la config Supabase pour éviter de répéter get_env() partout."""

    def __init__(self) -> None:
        self.url: str = get_env("SUPABASE_URL")
        self.key: str = get_env("SUPABASE_KEY")
        self.db_url: str = get_env("SUPABASE_DB_URL")


class PostgresConfig:
    def __init__(self) -> None:
        self.host: str = get_env("POSTGRES_HOST")
        self.port: str = get_env("POSTGRES_PORT", default="5432")
        self.db: str = get_env("POSTGRES_DB")
        self.user: str = get_env("POSTGRES_USER")
        self.password: str = get_env("POSTGRES_PASSWORD")


class MySQLConfig:
    def __init__(self) -> None:
        self.host: str = get_env("MYSQL_HOST")
        self.port: str = get_env("MYSQL_PORT", default="3306")
        self.db: str = get_env("MYSQL_DB")
        self.user: str = get_env("MYSQL_USER")
        self.password: str = get_env("MYSQL_PASSWORD")


class SQLiteConfig:
    def __init__(self) -> None:
        self.path: str = get_env("SQLITE_DB_PATH", required=False, default="./data/local_database.db")
