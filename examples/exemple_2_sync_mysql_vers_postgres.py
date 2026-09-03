"""
examples/exemple_2_sync_mysql_vers_postgres.py
--------------------------------------------------
CAS D'USAGE COMPLET : lire des données dans MySQL, les transformer,
et les réinjecter dans PostgreSQL (migration / synchronisation).

Pipeline complet illustré :
  1. CONNEXION      -> aux DEUX bases (MySQL en lecture, PostgreSQL en écriture)
  2. REQUÊTAGE      -> extraction depuis MySQL
  3. EXPLOITATION   -> transformation + écriture dans PostgreSQL (export_to_table)
"""

from db_connection.mysql_connector import get_mysql_engine
from db_connection.postgresql_connector import get_pg_engine
from data_processing.result_to_dataframe import query_to_dataframe
from data_processing.clean_transform import rename_columns, cast_types, drop_duplicates_and_nulls
from data_processing.export_results import export_to_table
from utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    # 1. CONNEXION AUX DEUX BASES -----------------------------------------
    mysql_engine = get_mysql_engine()
    pg_engine = get_pg_engine()

    # 2. REQUÊTAGE (source : MySQL) ---------------------------------------
    df = query_to_dataframe(mysql_engine, "SELECT id, nom_client, mail, date_creation FROM clients_legacy")

    # 3. EXPLOITATION : transformation + écriture (cible : PostgreSQL) ----
    df = drop_duplicates_and_nulls(df, subset=["mail"])
    df = rename_columns(df, {"nom_client": "customer_name", "mail": "email", "date_creation": "created_at"})
    df = cast_types(df, {"created_at": "datetime64[ns]"})

    export_to_table(df, pg_engine, table_name="customers", if_exists="append")

    logger.info("Synchronisation MySQL -> PostgreSQL terminée (%s lignes).", len(df))


if __name__ == "__main__":
    main()
