"""
queries/transactions.py
----------------------------
Gestion des transactions : plusieurs opérations qui doivent réussir
ou échouer ENSEMBLE (tout ou rien). Cas d'usage classique : transfert
d'argent entre deux comptes, création de commande + décrément de stock.
"""

from __future__ import annotations

from typing import Any

from decimal import Decimal, InvalidOperation
from sqlalchemy import text, bindparam, Numeric
from sqlalchemy.engine import Engine

from utils.logger import get_logger

logger = get_logger(__name__)


def transfer_funds(
    engine: Engine, from_account_id: int, to_account_id: int, amount: float
) -> None:
    """
    Exemple classique de transaction : débite un compte et crédite un autre.
    Si la moindre étape échoue, TOUT est annulé (rollback automatique).
    """
    if from_account_id == to_account_id:
        raise ValueError("Source and destination accounts must differ")
    try:
        money = Decimal(str(amount))
        if (
            isinstance(amount, bool)
            or not money.is_finite()
            or not 0 < money < Decimal("1e16")
            or money != money.quantize(Decimal("0.01"))
        ):
            raise ValueError(
                "amount must be positive, finite, and have at most two decimal places"
            )
    except (InvalidOperation, TypeError) as error:
        raise ValueError("Invalid amount") from error
    debit_query = text(
        "UPDATE accounts SET balance = balance - :amount WHERE id = :id AND balance >= :amount"
    )
    credit_query = text(
        "UPDATE accounts SET balance = balance + :amount WHERE id = :id"
    )
    debit_query = debit_query.bindparams(bindparam("amount", type_=Numeric(18, 2)))
    credit_query = credit_query.bindparams(bindparam("amount", type_=Numeric(18, 2)))

    try:
        with (
            engine.begin() as conn
        ):  # transaction : commit auto si tout va bien, rollback si exception
            result = conn.execute(debit_query, {"amount": money, "id": from_account_id})
            if result.rowcount == 0:
                raise ValueError(
                    f"Solde insuffisant ou compte {from_account_id} introuvable — transaction annulée."
                )
            credited = conn.execute(
                credit_query, {"amount": money, "id": to_account_id}
            )
            if credited.rowcount != 1:
                raise ValueError("Destination account not found; debit rolled back")

        logger.info(
            "Transfert réussi : %s -> %s (%.2f).",
            from_account_id,
            to_account_id,
            amount,
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
    if type(quantity) is not int or quantity < 1:
        raise ValueError("quantity must be a positive integer")
    # A conditional write takes the lock and checks stock in the same statement.
    # It is portable across SQLite, PostgreSQL and MySQL; SELECT FOR UPDATE is not.
    with engine.begin() as conn:
        reserved = conn.execute(
            text(
                "UPDATE products SET stock = stock - :qty WHERE id = :id AND stock >= :qty"
            ),
            {"qty": quantity, "id": product_id},
        )
        if reserved.rowcount != 1:
            raise ValueError("Product missing or insufficient stock")
        statement = "INSERT INTO orders (customer_id, product_id, quantity) VALUES (:customer_id, :product_id, :quantity)"
        if engine.dialect.insert_returning:
            result = conn.execute(
                text(statement + " RETURNING id"),
                {
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "quantity": quantity,
                },
            )
            order_id = result.scalar_one()
        else:
            result = conn.execute(
                text(statement),
                {
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "quantity": quantity,
                },
            )
            order_id = result.lastrowid

    logger.info(
        "Commande #%s créée avec succès (produit=%s, qte=%s).",
        order_id,
        product_id,
        quantity,
    )
    return order_id


def run_in_transaction(
    engine: Engine, operations: list[tuple[str, dict[str, Any]]]
) -> None:
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
    logger.info(
        "Transaction générique exécutée avec succès (%s opérations).", len(operations)
    )
