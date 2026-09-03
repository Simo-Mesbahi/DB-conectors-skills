"""
utils/logger.py
----------------
Logger réutilisable pour tout le projet.
Évite les `print()` disséminés partout et donne un format uniforme et daté.
"""

import logging
import os
import sys

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def get_logger(name: str) -> logging.Logger:
    """
    Crée (ou récupère) un logger nommé, avec un format standard.

    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Connexion établie")
        logger.error("Échec de la requête : %s", err)
    """
    logger = logging.getLogger(name)

    if not logger.handlers:  # évite les doublons de handlers si appelé plusieurs fois
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(_LOG_LEVEL)

    return logger
