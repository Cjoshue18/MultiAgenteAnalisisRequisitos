from typing import Dict, Any, List
from src.schemas.state import GraphState
from src.schemas.cus import CasoUso
from src.schemas.functional import RequisitoFuncional
from src.services.llm_client import LLMClient
from src.core.logger import get_logger

logger = get_logger(__name__)


def nodo_casos_de_uso(state: GraphState) -> Dict[str, Any]:
    """Subagente 4: modela casos de uso formales a partir de RF aprobados.

    Genera actores, precondiciones, flujo principal, alternativos y postcondiciones.
    """
    if state.errores:
        return {}

    rf = state.requisitos_funcionales
    try:
        llm = LLMClient().with_structured_output(List[CasoUso])
        rf_resumen = "\n".join(
            [f"- {r.id}: {r.descripcion} (Actores: {', '.join(r.actores)})" for r in rf]
        ) or "(ninguno)"
        prompt = (
            "A partir de los requisitos funcionales siguientes, genera casos de uso formales. "
            "Cada caso de uso debe tener: id, nombre, actor_principal, precondiciones (lista), "
            "flujo_principal (lista numerada), flujos_alternativos (lista) y postcondiciones (lista).\n\n"
            "Requisitos funcionales:\n" + rf_resumen
        )
        resultado: List[CasoUso] = llm.invoke(prompt)
        logger.info("Subagente CUS genero %d casos de uso", len(resultado))
        return {"casos_de_uso": resultado}
    except Exception as exc:
        logger.error("Error en Subagente CUS: %s", str(exc))
        return {"errores": [f"Error en Subagente CUS: {str(exc)}"]}