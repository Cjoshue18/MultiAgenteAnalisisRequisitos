import json
from src.agents.common import ejecutar_agente
from src.schemas.contracts import SalidaCasosUso
from src.schemas.state import GraphState
from src.services.llm_client import ClienteEstructurado

def nodo_casos_uso(state: GraphState, cliente: ClienteEstructurado) -> dict[str, object]:
    # La producción debe esperar intervención humana: este nodo exige RF aprobados.
    rf = state.get("rf_aprobados", [])
    if not rf:
        return {"errores": ["Se requiere al menos un RF aprobado para elaborar casos de uso"]}
    instrucciones = ("Deriva casos de uso SOLO a partir de RF aprobados. Crea códigos CUS-01, "
                     "actor, precondiciones, flujo principal numerado, alternativas y postcondiciones. "
                     "Marca supuestos de negocio como pendientes de confirmación; vincula rf_relacionados.\n" +
                     json.dumps([r.model_dump() for r in rf], ensure_ascii=False))
    return ejecutar_agente(state, cliente, SalidaCasosUso, instrucciones, "casos_uso", "casos_uso")
