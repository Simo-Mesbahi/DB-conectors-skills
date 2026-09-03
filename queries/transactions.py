"""
queries/transactions.py
----------------------------
Gestion des transactions : plusieurs opérations qui doivent réussir
ou échouer ENSEMBLE (tout ou rien). Cas d'usage classique : transfert
d'argent entre deux comptes, création de commande + décrément de stock.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from utils.logger import get_logger

logger = get_logger(__name__)


def transfer_funds(engine: Engine, from_account_id: int, to_account_id: int, amount: float) -> None:
    """
    Exemple classique de transaction : débite un compte et crédite un autre.
    Si la moindre étape échoue, TOUT est annulé (rollback automatique).
    """
    debit_query = text(
        "UPDATE accounts SET balance = balance - :amount WHERE id = :id AND balance >= :amount"
    )
    credit_query = text("UPDATE accounts SET balance = balance + :amount WHERE id = :id")

    try:
        with engine.begin() as conn:  # transaction : commit auto si tout va bien, rollback si exception
            result = conn.execute(debit_query, {"amount": amount, "id": from_account_id})
            if result.rowcount == 0:
                raise ValueError(
                    f"Solde insuffisant ou compte {from_account_id} introuvable — transaction annulée."
                )
            conn.execute(credit_query, {"amount": amount, "id": to_account_id})

        logger.info(
            "Transfert réussi : %s -> %s (%.2f).", from_account_id, to_account_id, amount
        )
    except Exception as exc:
        logger.error("Transaction annulée (rollback) : %s", exc)
        raise


def create_order_with_stock_update(
    engine: Engine, product_id: int, quantity: int, customer_id: int
) -> int:
    """
    Autre exemple : création d'une commande ET décrément du stock, de façon atomique.
    Retourne l'id de la commande créée.
    """
    check_stock_query = text("SELECT stock FROM products WHERE id = :id FOR UPDATE")
    update_stock_query = text("UPDATE products SET stock = stock - :qty WHERE id = :id")
    insert_order_query = text(
        """
        INSERT INTO orders (customer_id, product_id, quantity)
        VALUES (:customer_id, :product_id, :quantity)
        RETURNING id
        """
    )

    with engine.begin() as conn:
        stock = conn.execute(check_stock_query, {"id": product_id}).scalar_one()
        if stock < quantity:
            raise ValueError(f"Stock insuffisant pour le produit {product_id} (dispo: {stock}).")

        conn.execute(update_stock_query, {"qty": quantity, "id": product_id})
        order_id = conn.execute(
            insert_order_query,
            {"customer_id": customer_id, "product_id": product_id, "quantity": quantity},
        ).scalar_one()

    logger.info("Commande #%s créée avec succès (produit=%s, qte=%s).", order_id, product_id, quantity)
    return order_id


def run_in_transaction(engine: Engine, operations: list[tuple[str, dict[str, Any]]]) -> None:
    """
    Fonction générique : exécute une liste de requêtes (query, params) dans
    UNE SEULE transaction. Pratique quand la logique métier est déjà décidée
    en amont (ex: génération dynamique de plusieurs requêtes).

    Exemple:
        run_in_transaction(engine, [
            ("UPDATE stock SET qty = qty - :q WHERE id = :id", {"q": 1, "id": 42}),
            ("INSERT INTO logs (message) VALUES (:msg)", {"msg": "stock décrémenté"}),
        ])
    """
    with engine.begin() as conn:
        for query_str, params in operations:
            conn.execute(text(query_str), params)
    logger.info("Transaction générique exécutée avec succès (%s opérations).", len(operations))
