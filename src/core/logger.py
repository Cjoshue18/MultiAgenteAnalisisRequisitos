import logging
import sys
from src.core.settings import settings


def get_logger(name: str) -> logging.Logger:
    """Configura y devuelve un logger estandar para el modulo indicado.

    Prohibido el uso de print() en codigo productivo; usar siempre logging.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    return logger
