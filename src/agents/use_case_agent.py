import json
from src.agents.common import ejecutar_agente, serializar_elementos
from src.schemas.contracts import SalidaCasosUso
from src.schemas.state import GraphState
from src.services.llm_client import ClienteEstructurado


def nodo_casos_uso(state: GraphState, cliente: ClienteEstructurado) -> dict[str, object]:
    rf = state.get("rf_aprobados") or state.get("requisitos_funcionales") or []
    if not rf:
        return {"errores": ["Se requiere al menos un RF para elaborar casos de uso"]}
    instrucciones = (
        "Deriva casos de uso a partir de los RF proporcionados. Crea códigos CUS-01, "
        "actor, precondiciones, flujo principal numerado, alternativas y postcondiciones. "
        "Marca supuestos de negocio como pendientes de confirmación; vincula rf_relacionados.\n"
        + json.dumps(serializar_elementos(rf), ensure_ascii=False)
    )
    return ejecutar_agente(
        cliente,
        SalidaCasosUso,
        instrucciones,
        "casos_uso",
        "casos_uso",
        nodo="nodo_casos_uso",
    )
