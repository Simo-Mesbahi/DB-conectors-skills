"""
data_processing/export_results.py
--------------------------------------
Étape 5 de l'exploitation : exporter le résultat traité vers un format
final utilisable (fichier ou réinjection en base).
"""

from __future__ import annotations

import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype
from sqlalchemy.engine import Engine

from utils.logger import get_logger

logger = get_logger(__name__)


@contextmanager
def _atomic_destination(filepath):
    target = Path(filepath)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{target.name}.",
        suffix="".join(target.suffixes),
        dir=target.parent,
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
    try:
        yield temporary
        with temporary.open("rb+") as handle:
            os.fsync(handle.fileno())
        if target.exists():
            temporary.chmod(stat.S_IMODE(target.stat().st_mode))
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def _literal_cell(value):
    if isinstance(value, str) and (
        value.lstrip().startswith(("=", "+", "-", "@"))
        or value.startswith(("\t", "\r", "\n"))
    ):
        return "'" + value
    return value


def _literal_label(value):
    return (
        tuple(_literal_cell(part) for part in value)
        if isinstance(value, tuple)
        else _literal_cell(value)
    )


def _spreadsheet_frame(df):
    # Replace only text/object columns; keep numeric columns and the input intact.
    safe = df.copy(deep=False)
    for position in range(len(df.columns)):
        column = df.iloc[:, position]
        if is_object_dtype(column.dtype) or is_string_dtype(column.dtype):
            safe.isetitem(position, column.map(_literal_cell))
    safe.columns = safe.columns.map(_literal_label)
    return safe


def _compression(filepath):
    # Preserve compression inference and stable member names across atomic writes.
    name = Path(filepath).name
    if name.endswith(".zip"):
        return {"method": "zip", "archive_name": name[:-4]}
    for suffix in (".tar.gz", ".tar.bz2", ".tar.xz", ".tar"):
        if name.endswith(suffix):
            return {"method": "tar", "archive_name": name[: -len(suffix)]}
    return "infer"


def export_to_csv(df: pd.DataFrame, filepath: str, *, safe_cells: bool = True) -> None:
    frame = _spreadsheet_frame(df) if safe_cells else df
    with _atomic_destination(filepath) as temporary:
        frame.to_csv(
            temporary, index=False, encoding="utf-8", compression=_compression(filepath)
        )
    logger.info("export_to_csv() -> fichier écrit : %s (%s lignes).", filepath, len(df))


def export_to_excel(
    df: pd.DataFrame,
    filepath: str,
    sheet_name: str = "Résultats",
    *,
    safe_cells: bool = True,
) -> None:
    if (
        not isinstance(sheet_name, str)
        or not sheet_name
        or len(sheet_name) > 31
        or any(character in sheet_name for character in "\\/*?:[]")
        or sheet_name.startswith("'")
        or sheet_name.endswith("'")
    ):
        raise ValueError("sheet_name must be a valid Excel name of 1 to 31 characters")
    frame = _spreadsheet_frame(df) if safe_cells else df
    with _atomic_destination(filepath) as temporary:
        frame.to_excel(temporary, index=False, sheet_name=sheet_name, engine="openpyxl")
    logger.info(
        "export_to_excel() -> fichier écrit : %s (%s lignes).", filepath, len(df)
    )


def export_to_json(df: pd.DataFrame, filepath: str) -> None:
    with _atomic_destination(filepath) as temporary:
        df.to_json(
            temporary,
            orient="records",
            force_ascii=False,
            indent=2,
            compression=_compression(filepath),
        )
    logger.info(
        "export_to_json() -> fichier écrit : %s (%s lignes).", filepath, len(df)
    )


def export_to_table(
    df: pd.DataFrame, engine: Engine, table_name: str, if_exists: str = "append"
) -> None:
    """
    Réinjecte le DataFrame traité dans une table SQL (pipeline complet :
    lire -> transformer -> écrire ailleurs). `if_exists` ∈ {"append","replace","fail"}.
    """
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    logger.info(
        "export_to_table('%s') -> %s lignes écrites (mode=%s).",
        table_name,
        len(df),
        if_exists,
    )
