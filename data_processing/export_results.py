"""
data_processing/export_results.py
--------------------------------------
Étape 5 de l'exploitation : exporter le résultat traité vers un format
final utilisable (fichier ou réinjection en base).
"""

from __future__ import annotations

import os

import pandas as pd
from sqlalchemy.engine import Engine

from utils.logger import get_logger

logger = get_logger(__name__)


def export_to_csv(df: pd.DataFrame, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_csv(filepath, index=False, encoding="utf-8")
    logger.info("export_to_csv() -> fichier écrit : %s (%s lignes).", filepath, len(df))


def export_to_excel(df: pd.DataFrame, filepath: str, sheet_name: str = "Résultats") -> None:
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_excel(filepath, index=False, sheet_name=sheet_name)
    logger.info("export_to_excel() -> fichier écrit : %s (%s lignes).", filepath, len(df))


def export_to_json(df: pd.DataFrame, filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    df.to_json(filepath, orient="records", force_ascii=False, indent=2)
    logger.info("export_to_json() -> fichier écrit : %s (%s lignes).", filepath, len(df))


def export_to_table(df: pd.DataFrame, engine: Engine, table_name: str, if_exists: str = "append") -> None:
    """
    Réinjecte le DataFrame traité dans une table SQL (pipeline complet :
    lire -> transformer -> écrire ailleurs). `if_exists` ∈ {"append","replace","fail"}.
    """
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    logger.info(
        "export_to_table('%s') -> %s lignes écrites (mode=%s).", table_name, len(df), if_exists
    )
