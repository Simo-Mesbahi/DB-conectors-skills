"""
data_processing/clean_transform.py
--------------------------------------
Étape 2 de l'exploitation : nettoyer, typer et transformer les données
obtenues d'une requête AVANT toute analyse ou action métier.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


def drop_duplicates_and_nulls(df: pd.DataFrame, subset: list[str] | None = None) -> pd.DataFrame:
    """Supprime les doublons et les lignes totalement vides."""
    before = len(df)
    df = df.drop_duplicates(subset=subset).dropna(how="all")
    logger.info("drop_duplicates_and_nulls() -> %s lignes supprimées (%s -> %s).", before - len(df), before, len(df))
    return df


def rename_columns(df: pd.DataFrame, mapping: dict[str, str]) -> pd.DataFrame:
    """Renomme des colonnes pour plus de lisibilité métier (ex: 'usr_nm' -> 'nom_utilisateur')."""
    return df.rename(columns=mapping)


def cast_types(df: pd.DataFrame, dtypes: dict[str, str]) -> pd.DataFrame:
    """
    Force le typage de certaines colonnes (utile car SQL peut renvoyer des
    types imprécis, ex: Decimal, texte de date, etc.)

    Exemple:
        df = cast_types(df, {"created_at": "datetime64[ns]", "amount": "float64"})
    """
    for col, dtype in dtypes.items():
        if col not in df.columns:
            logger.warning("cast_types() : colonne '%s' absente du DataFrame, ignorée.", col)
            continue
        if dtype.startswith("datetime"):
            df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            df[col] = df[col].astype(dtype, errors="ignore")
    return df


def filter_rows(df: pd.DataFrame, column: str, condition: str, value) -> pd.DataFrame:
    """
    Filtre générique sur une colonne.
    `condition` ∈ {"eq", "gt", "lt", "gte", "lte", "contains"}
    """
    ops = {
        "eq": lambda s: s == value,
        "gt": lambda s: s > value,
        "lt": lambda s: s < value,
        "gte": lambda s: s >= value,
        "lte": lambda s: s <= value,
        "contains": lambda s: s.astype(str).str.contains(str(value), case=False, na=False),
    }
    if condition not in ops:
        raise ValueError(f"Condition inconnue : '{condition}'. Valeurs valides : {list(ops.keys())}")

    filtered = df[ops[condition](df[column])]
    logger.info("filter_rows(%s %s %s) -> %s/%s lignes conservées.", column, condition, value, len(filtered), len(df))
    return filtered


def add_computed_column(df: pd.DataFrame, new_column: str, func) -> pd.DataFrame:
    """
    Ajoute une colonne calculée à partir d'une fonction appliquée ligne par ligne.

    Exemple:
        df = add_computed_column(df, "total_ttc", lambda row: row["total_ht"] * 1.2)
    """
    df = df.copy()
    df[new_column] = df.apply(func, axis=1)
    return df
