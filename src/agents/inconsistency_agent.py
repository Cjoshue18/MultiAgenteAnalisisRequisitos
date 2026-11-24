from typing import Dict, Any, List
from src.schemas.state import GraphState
from src.schemas.inconsistency import Inconsistencia
from src.services.llm_client import LLMClient
from src.core.logger import get_logger

logger = get_logger(__name__)


def nodo_inconsistencias(state: GraphState) -> Dict[str, Any]:
    """Subagente 3: detecta inconsistencias, ambigüedades y vacíos.

    Cruza la entrada del usuario frente a los RF y RNF consolidados.
    """
    texto = state.texto_usuario
    rf = state.requisitos_funcionales
    rnf = state.requisitos_no_funcionales

    try:
        llm = LLMClient().with_structured_output(List[Inconsistencia])
        rf_resumen = "\n".join([f"- {r.id}: {r.descripcion}" for r in rf]) or "(ninguno)"
        rnf_resumen = "\n".join([f"- {r.id}: {r.descripcion}" for r in rnf]) or "(ninguno)"
        prompt = (
            "Analiza el texto original junto con los requisitos funcionales y no funcionales extraidos. "
            "Detecta inconsistencias semanticas, ambiguedades lexico y vacios de informacion. "
            "Para cada hallazgo asigna severidad (Alta, Media o Baja) y redacta una pregunta de clarificacion.\n\n"
            "Texto original: " + texto + "\n\n"
            "RF:\n" + rf_resumen + "\n\n"
            "RNF:\n" + rnf_resumen
        )
        resultado: List[Inconsistencia] = llm.invoke(prompt)
        logger.info("Subagente Inconsistencias detecto %d hallazgos", len(resultado))
        return {"inconsistencias": resultado}
    except Exception as exc:
        logger.error("Error en Subagente Inconsistencias: %s", str(exc))
        return {"errores": [f"Error en Subagente Inconsistencias: {str(exc)}"]}