from typing import Dict, Any
from src.schemas.state import GraphState
from src.core.logger import get_logger

logger = get_logger(__name__)


def nodo_orquestador(state: GraphState) -> Dict[str, Any]:
    """Nodo validador de entrada y supervisor del grafo.

    Recibe el estado, valida que el texto tenga contenido suficiente y
    inicializa el identificador de analisis si no existe.
    """
    texto = state.texto_usuario.strip()
    if len(texto) < 20:
        return {"errores": ["La solicitud debe contener al menos 20 caracteres significativos."]}

    analisis_id = state.analisis_id or f"ANL-{abs(hash(texto)) % 100000:05d}"
    logger.info("Orquestador inicio analisis id=%s", analisis_id)

    return {
        "analisis_id": analisis_id,
        "etapa_actual": "valido",
        "errores": [],
    }
