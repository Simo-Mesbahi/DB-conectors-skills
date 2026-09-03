"""
examples/exemple_1_rapport_ventes_supabase.py
------------------------------------------------
CAS D'USAGE COMPLET : générer un rapport de ventes à partir de Supabase.

Pipeline complet illustré :
  1. CONNEXION      -> à Supabase (SQL direct)
  2. REQUÊTAGE      -> récupération des ventes du mois
  3. EXPLOITATION   -> nettoyage, agrégation par produit, graphique, export Excel

Lance ce script avec : python -m examples.exemple_1_rapport_ventes_supabase
(nécessite un fichier .env valide, voir .env.example)
"""

from db_connection.supabase_connector import get_supabase_sql_engine
from data_processing.result_to_dataframe import query_to_dataframe
from data_processing.clean_transform import drop_duplicates_and_nulls, cast_types
from data_processing.analyze_results import group_and_aggregate, top_n
from data_processing.visualize_results import plot_bar_matplotlib
from data_processing.export_results import export_to_excel
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    # 1. CONNEXION -----------------------------------------------------
    engine = get_supabase_sql_engine()

    # 2. REQUÊTAGE -------------------------------------------------------
    query = """
        SELECT product_name, quantity, unit_price, created_at
        FROM sales
        WHERE created_at >= :start_date
    """
    df = query_to_dataframe(engine, query, params={"start_date": "2025-01-01"})

    # 3. EXPLOITATION DU RÉSULTAT -----------------------------------------
    df = drop_duplicates_and_nulls(df)
    df = cast_types(df, {"created_at": "datetime64[ns]", "quantity": "int64", "unit_price": "float64"})
    df["total"] = df["quantity"] * df["unit_price"]

    ventes_par_produit = group_and_aggregate(df, group_by="product_name", agg_column="total", agg_func="sum")
    top_produits = top_n(ventes_par_produit, column="total", n=10)

    print("\n=== Top 10 produits par chiffre d'affaires ===")
    print(top_produits.to_string(index=False))

    plot_bar_matplotlib(top_produits, x="product_name", y="total", title="Top produits par CA")
    export_to_excel(top_produits, "exports/rapport_ventes.xlsx")

    logger.info("Rapport de ventes généré avec succès.")


if __name__ == "__main__":
    main()
