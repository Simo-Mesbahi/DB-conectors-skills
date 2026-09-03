"""
data_processing/analyze_results.py
--------------------------------------
Étape 3 de l'exploitation : calculs et statistiques simples côté Python
sur les données déjà récupérées et nettoyées (plutôt que de tout faire
en SQL, parfois plus lisible/flexible de calculer côté pandas).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)


def summary_statistics(df: pd.DataFrame, numeric_column: str) -> dict[str, float]:
    """Statistiques descriptives de base sur une colonne numérique."""
    stats = {
        "count": df[numeric_column].count(),
        "mean": df[numeric_column].mean(),
        "median": df[numeric_column].median(),
        "std": df[numeric_column].std(),
        "min": df[numeric_column].min(),
        "max": df[numeric_column].max(),
    }
    logger.info("summary_statistics('%s') -> %s", numeric_column, stats)
    return stats


def group_and_aggregate(
    df: pd.DataFrame, group_by: str, agg_column: str, agg_func: str = "sum"
) -> pd.DataFrame:
    """
    Agrégation façon "GROUP BY" côté pandas.
    `agg_func` ∈ {"sum", "mean", "count", "min", "max"}
    """
    result = df.groupby(group_by)[agg_column].agg(agg_func).reset_index()
    logger.info("group_and_aggregate(by=%s, func=%s) -> %s groupes.", group_by, agg_func, len(result))
    return result


def top_n(df: pd.DataFrame, column: str, n: int = 10, ascending: bool = False) -> pd.DataFrame:
    """Retourne les N lignes avec les plus grandes (ou plus petites) valeurs d'une colonne."""
    return df.sort_values(by=column, ascending=ascending).head(n)


def pivot_summary(df: pd.DataFrame, index: str, columns: str, values: str, agg_func: str = "sum") -> pd.DataFrame:
    """Tableau croisé dynamique (pivot table), pratique pour des rapports."""
    pivot = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=agg_func, fill_value=0)
    logger.info("pivot_summary() -> tableau de forme %s.", pivot.shape)
    return pivot


def detect_anomalies(df: pd.DataFrame, column: str, n_std: float = 3.0) -> pd.DataFrame:
    """
    Détection simple d'anomalies (valeurs aberrantes) via écart-type.
    Utile pour un cas d'usage type "déclencher une alerte métier".
    """
    mean, std = df[column].mean(), df[column].std()
    lower, upper = mean - n_std * std, mean + n_std * std
    anomalies = df[(df[column] < lower) | (df[column] > upper)]
    logger.info("detect_anomalies('%s') -> %s anomalies détectées.", column, len(anomalies))
    return anomalies
