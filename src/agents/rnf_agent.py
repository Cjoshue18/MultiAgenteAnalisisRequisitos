from typing import Dict, Any, List
from src.schemas.state import GraphState
from src.schemas.rnf import RequisitoNoFuncional
from src.services.llm_client import LLMClient
from src.core.logger import get_logger

logger = get_logger(__name__)


def nodo_requisitos_no_funcionales(state: GraphState) -> Dict[str, Any]:
    """Subagente 2: clasifica requisitos no funcionales bajo ISO/IEC 25010.

    Convierte adjetivos abstractos en metricas cuantificables.
    """
    texto = state.texto_usuario
    try:
        llm = LLMClient().with_structured_output(List[RequisitoNoFuncional])
        prompt = (
            "Clasifica requisitos no funcionales del siguiente texto bajo la norma ISO/IEC 25010. "
            "Categorias validas: Rendimiento, Seguridad, Fiabilidad, Usabilidad, Compatibilidad, "
            "Mantenibilidad, Escalabilidad, Portabilidad. "
            "Cada requisito debe tener: id, categoria_iso, descripcion, metrica_objetiva, valor_umbral.\n\n"
            "Texto: " + texto
        )
        resultado: List[RequisitoNoFuncional] = llm.invoke(prompt)
        logger.info("Subagente RNF extrajo %d requisitos", len(resultado))
        return {"requisitos_no_funcionales": resultado}
    except Exception as exc:
        logger.error("Error en Subagente RNF: %s", str(exc))
        return {"errores": [f"Error en Subagente RNF: {str(exc)}"]}