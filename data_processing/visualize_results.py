"""
data_processing/visualize_results.py
-----------------------------------------
Étape 4 de l'exploitation : visualiser les résultats de requêtes.
Deux moteurs proposés :
- matplotlib -> simple, statique, parfait pour un rapport/export image.
- plotly     -> interactif, idéal dans un notebook ou un dashboard web.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px

from utils.logger import get_logger

logger = get_logger(__name__)


def plot_bar_matplotlib(df: pd.DataFrame, x: str, y: str, title: str = "") -> None:
    """Graphique en barres simple (matplotlib) — pour export statique/rapport."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(df[x], df[y], color="#4C72B0")
    ax.set_title(title or f"{y} par {x}")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
    logger.info("plot_bar_matplotlib() -> graphique généré (%s lignes).", len(df))


def plot_line_matplotlib(df: pd.DataFrame, x: str, y: str, title: str = "") -> None:
    """Graphique en courbe (évolution temporelle typiquement)."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df[x], df[y], marker="o", color="#DD8452")
    ax.set_title(title or f"Évolution de {y}")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()
    logger.info("plot_line_matplotlib() -> graphique généré (%s lignes).", len(df))


def plot_interactive(df: pd.DataFrame, x: str, y: str, kind: str = "bar", title: str = ""):
    """
    Graphique interactif via Plotly (survol, zoom...) — idéal en notebook.
    `kind` ∈ {"bar", "line", "scatter", "pie"}
    """
    plot_funcs = {
        "bar": px.bar,
        "line": px.line,
        "scatter": px.scatter,
        "pie": lambda d, x, y, title: px.pie(d, names=x, values=y, title=title),
    }
    if kind not in plot_funcs:
        raise ValueError(f"kind inconnu : '{kind}'. Valeurs valides : {list(plot_funcs.keys())}")

    fig = plot_funcs[kind](df, x=x, y=y, title=title or f"{y} par {x}")
    fig.show()
    logger.info("plot_interactive(kind=%s) -> graphique généré (%s lignes).", kind, len(df))
    return fig
