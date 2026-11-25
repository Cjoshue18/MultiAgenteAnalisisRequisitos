import logging


def configurar_logging(nivel: int = logging.INFO) -> None:
    """Configura el formato base de logging bajo demanda sin efectos al importar."""
    logging.basicConfig(level=nivel, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
