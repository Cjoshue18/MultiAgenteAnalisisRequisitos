from typing import Dict, Any, List
from src.schemas.state import GraphState
from src.schemas.functional import RequisitoFuncional
from src.services.llm_client import LLMClient
from src.core.logger import get_logger

logger = get_logger(__name__)


def nodo_requisitos_funcionales(state: GraphState) -> Dict[str, Any]:
    """Subagente 1: extrae requisitos funcionales atomicos.

    Usa structured output con Pydantic para garantizar contratos tipados.
    """
    texto = state.texto_usuario
    try:
        llm = LLMClient().with_structured_output(List[RequisitoFuncional])
        prompt = (
            "Extrae requisitos funcionales atomicos del siguiente texto. "
            "Cada requisito debe tener: id, nombre, descripcion (atomica: 'El sistema debe...'), "
            "actores (lista) y referencia_texto (cita exacta del texto original).\n\n"
            "Texto: " + texto
        )
        resultado: List[RequisitoFuncional] = llm.invoke(prompt)
        logger.info("Subagente RF extrajo %d requisitos", len(resultado))
        return {"requisitos_funcionales": resultado}
    except Exception as exc:
        logger.error("Error en Subagente RF: %s", str(exc))
        return {"errores": [f"Error en Subagente RF: {str(exc)}"]}