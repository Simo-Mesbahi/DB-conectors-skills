"""
tests/test_data_processing.py
---------------------------------
Tests unitaires sur les fonctions de traitement de données.
Ces tests ne nécessitent AUCUNE base de données réelle : ils valident
la logique pure sur des DataFrames construits à la main.

Lancer avec : pytest tests/
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest

from data_processing.clean_transform import (
    drop_duplicates_and_nulls,
    rename_columns,
    filter_rows,
    add_computed_column,
)
from data_processing.analyze_results import (
    summary_statistics,
    group_and_aggregate,
    top_n,
    detect_anomalies,
)
from data_processing.result_to_dataframe import rows_to_dataframe, dataframe_to_records


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "product": ["A", "B", "C", "A"],
        "category": ["X", "Y", "X", "X"],
        "amount": [10.0, 20.0, 30.0, 10.0],
    })


def test_rows_to_dataframe():
    rows = [{"id": 1, "name": "Simo"}, {"id": 2, "name": "Test"}]
    df = rows_to_dataframe(rows)
    assert len(df) == 2
    assert list(df.columns) == ["id", "name"]


def test_dataframe_to_records_roundtrip(sample_df):
    records = dataframe_to_records(sample_df)
    assert isinstance(records, list)
    assert records[0]["product"] == "A"


def test_drop_duplicates_and_nulls(sample_df):
    df_with_dup = pd.concat([sample_df, sample_df.iloc[[0]]], ignore_index=True)
    cleaned = drop_duplicates_and_nulls(df_with_dup)
    assert len(cleaned) == len(sample_df)


def test_rename_columns(sample_df):
    renamed = rename_columns(sample_df, {"product": "produit"})
    assert "produit" in renamed.columns
    assert "product" not in renamed.columns


def test_filter_rows_eq(sample_df):
    filtered = filter_rows(sample_df, column="category", condition="eq", value="X")
    assert len(filtered) == 3
    assert (filtered["category"] == "X").all()


def test_filter_rows_gt(sample_df):
    filtered = filter_rows(sample_df, column="amount", condition="gt", value=15)
    assert len(filtered) == 2


def test_add_computed_column(sample_df):
    df = add_computed_column(sample_df, "amount_ttc", lambda row: row["amount"] * 1.2)
    assert "amount_ttc" in df.columns
    assert df["amount_ttc"].iloc[0] == pytest.approx(12.0)


def test_summary_statistics(sample_df):
    stats = summary_statistics(sample_df, "amount")
    assert stats["count"] == 4
    assert stats["min"] == 10.0
    assert stats["max"] == 30.0


def test_group_and_aggregate(sample_df):
    result = group_and_aggregate(sample_df, group_by="category", agg_column="amount", agg_func="sum")
    x_total = result.loc[result["category"] == "X", "amount"].values[0]
    assert x_total == 50.0  # 10 + 30 + 10


def test_top_n(sample_df):
    top = top_n(sample_df, column="amount", n=2)
    assert len(top) == 2
    assert top["amount"].iloc[0] == 30.0


def test_detect_anomalies_no_crash(sample_df):
    # Vérifie juste que la fonction s'exécute et retourne un DataFrame
    result = detect_anomalies(sample_df, column="amount", n_std=1.0)
    assert isinstance(result, pd.DataFrame)
