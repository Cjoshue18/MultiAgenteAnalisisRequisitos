import json
from src.agents.common import comprobar_texto, ejecutar_agente, serializar_elementos
from src.schemas.contracts import SalidaInconsistencias
from src.schemas.state import GraphState
from src.services.llm_client import ClienteEstructurado


def nodo_inconsistencias(state: GraphState, cliente: ClienteEstructurado) -> dict[str, object]:
    try:
        texto = comprobar_texto(state)
    except ValueError as exc:
        return {"errores": [str(exc)]}
    datos = {
        "rf": serializar_elementos(state.get("requisitos_funcionales") or []),
        "rnf": serializar_elementos(state.get("requisitos_no_funcionales") or []),
    }
    instrucciones = (
        "Revisa contradicciones, ambigüedades y vacíos reales comparando documento, RF y RNF. "
        "Describe evidencia, severidad y pregunta de clarificación concreta. "
        "No afirmes errores sin sustento.\nDOCUMENTO:\n"
        + texto
        + "\nSALIDAS:\n"
        + json.dumps(datos, ensure_ascii=False)
    )
    return ejecutar_agente(
        cliente,
        SalidaInconsistencias,
        instrucciones,
        "inconsistencias",
        "inconsistencias",
        nodo="nodo_inconsistencias",
    )
