import json
from src.agents.common import comprobar_texto, ejecutar_agente
from src.schemas.contracts import SalidaInconsistencias
from src.schemas.state import GraphState
from src.services.llm_client import ClienteEstructurado

def nodo_inconsistencias(state: GraphState, cliente: ClienteEstructurado) -> dict[str, object]:
    try:
        texto = comprobar_texto(state)
    except ValueError as exc:
        return {"errores": [str(exc)]}
    datos = {
        "rf": [r.model_dump() for r in state.get("requisitos_funcionales", [])],
        "rnf": [r.model_dump() for r in state.get("requisitos_no_funcionales", [])],
    }
    instrucciones = ("Revisa contradicciones, ambigüedades y vacíos reales comparando documento, RF y RNF. "
                     "Describe evidencia, severidad y pregunta de clarificación concreta. "
                     "No afirmes errores sin sustento.\nDOCUMENTO:\n" + texto + "\nSALIDAS:\n" + json.dumps(datos, ensure_ascii=False))
    return ejecutar_agente(state, cliente, SalidaInconsistencias, instrucciones, "inconsistencias", "inconsistencias")
