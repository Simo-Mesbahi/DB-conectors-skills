"""
examples/exemple_3_alerte_anomalie_stock.py
------------------------------------------------
CAS D'USAGE COMPLET : détecter des anomalies de stock et DÉCLENCHER
une action métier (ici : insérer une alerte en base) selon le résultat
de l'exploitation. Montre que "exploiter un résultat" ne se limite pas
à l'affichage : ça peut déclencher une écriture derrière.

Pipeline complet illustré :
  1. CONNEXION      -> SQLite (exemple local, adaptable à n'importe quelle base)
  2. REQUÊTAGE      -> lecture des niveaux de stock
  3. EXPLOITATION   -> détection d'anomalies (analyze_results.detect_anomalies)
  4. ACTION         -> écriture d'alertes en base à partir du résultat exploité
"""

from db_connection.sqlite_connector import get_sqlite_engine
from data_processing.result_to_dataframe import query_to_dataframe, dataframe_to_records
from data_processing.analyze_results import detect_anomalies
from queries.write_queries import bulk_insert
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    # 1. CONNEXION ---------------------------------------------------------
    engine = get_sqlite_engine()

    # 2. REQUÊTAGE -----------------------------------------------------------
    df = query_to_dataframe(engine, "SELECT product_id, product_name, stock_level FROM inventory")

    # 3. EXPLOITATION : détection d'anomalies ---------------------------------
    anomalies = detect_anomalies(df, column="stock_level", n_std=2.5)

    if anomalies.empty:
        logger.info("Aucune anomalie de stock détectée.")
        return

    print(f"\n⚠️  {len(anomalies)} anomalie(s) de stock détectée(s) :")
    print(anomalies.to_string(index=False))

    # 4. ACTION MÉTIER : on réinjecte le résultat exploité sous forme d'alertes --
    alerts = [
        {"product_id": int(row["product_id"]), "message": f"Stock anormal : {row['stock_level']} unités"}
        for _, row in anomalies.iterrows()
    ]
    bulk_insert(engine, "stock_alerts", alerts)

    logger.info("%s alerte(s) créée(s) en base à partir du résultat exploité.", len(alerts))


if __name__ == "__main__":
    main()
