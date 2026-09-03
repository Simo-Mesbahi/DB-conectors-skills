"""
data_processing/result_to_dataframe.py
-----------------------------------------
Étape 1 de l'exploitation : transformer le résultat BRUT d'une requête
(liste de dicts, tuples, ou objets Supabase) en structures manipulables,
principalement des `pandas.DataFrame`.

C'est le pont entre "queries/" (récupération) et le reste de
"data_processing/" (nettoyage, analyse, visualisation, export).
"""

from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from utils.logger import get_logger

logger = get_logger(__name__)


def rows_to_dataframe(rows: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Convertit une liste de dictionnaires (résultat typique de select_* ou
    d'un appel Supabase) en DataFrame pandas.
    """
    df = pd.DataFrame(rows)
    logger.info("rows_to_dataframe() -> DataFrame de forme %s.", df.shape)
    return df


def query_to_dataframe(engine: Engine, sql_query: str, params: dict[str, Any] | None = None) -> pd.DataFrame:
    """
    Exécute directement une requête SQL et retourne un DataFrame.
    Le moyen le PLUS DIRECT d'aller de la base de données à un objet exploitable
    (pandas gère la connexion, l'exécution et le typage des colonnes).

    Exemple:
        df = query_to_dataframe(engine, "SELECT * FROM orders WHERE total > :min", {"min": 100})
    """
    df = pd.read_sql(text(sql_query), engine, params=params or {})
    logger.info("query_to_dataframe() -> DataFrame de forme %s.", df.shape)
    return df


def supabase_response_to_dataframe(response) -> pd.DataFrame:
    """
    Convertit une réponse du SDK Supabase (client.table(...).select(...).execute())
    en DataFrame.
    """
    df = pd.DataFrame(response.data)
    logger.info("supabase_response_to_dataframe() -> DataFrame de forme %s.", df.shape)
    return df


def dataframe_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Conversion inverse : DataFrame -> liste de dicts.
    Utile pour réinjecter des données traitées via bulk_insert() ou supabase_insert().
    """
    return df.to_dict(orient="records")
