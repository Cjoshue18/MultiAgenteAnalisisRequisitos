import json
from src.agents.common import ejecutar_agente, serializar_elementos
from src.schemas.contracts import SalidaCasosUso, SalidaHU
from src.schemas.state import GraphState
from src.services.llm_client import ClienteEstructurado


def _modelar_desde_rf(
    state: GraphState,
    cliente: ClienteEstructurado,
    esquema: type[SalidaCasosUso] | type[SalidaHU],
    instrucciones_base: str,
    clave: str,
    atributo: str,
    nodo: str,
) -> dict[str, object]:
    rf = state.get("rf_aprobados") or state.get("requisitos_funcionales") or []
    if not rf:
        return {"errores": ["Se requiere al menos un RF para elaborar el modelado"]}
    instrucciones = f"{instrucciones_base}\n{json.dumps(serializar_elementos(rf), ensure_ascii=False)}"
    return ejecutar_agente(cliente, esquema, instrucciones, clave, atributo, nodo=nodo)


def nodo_casos_uso(state: GraphState, cliente: ClienteEstructurado) -> dict[str, object]:
    return _modelar_desde_rf(
        state=state,
        cliente=cliente,
        esquema=SalidaCasosUso,
        instrucciones_base=(
            "Deriva casos de uso a partir de los RF proporcionados. Crea códigos CUS-01, "
            "actor, precondiciones, flujo principal numerado, alternativas y postcondiciones. "
            "Marca supuestos de negocio como pendientes de confirmación; vincula rf_relacionados."
        ),
        clave="casos_uso",
        atributo="casos_uso",
        nodo="nodo_casos_uso",
    )


def nodo_historias_usuario(state: GraphState, cliente: ClienteEstructurado) -> dict[str, object]:
    return _modelar_desde_rf(
        state=state,
        cliente=cliente,
        esquema=SalidaHU,
        instrucciones_base=(
            "Deriva historias de usuario ágiles a partir de los RF proporcionados. Crea códigos HU-01, "
            "titulo, narrativa COMO/QUIERO/PARA QUE, al menos un criterio de aceptación DADO/CUANDO/ENTONCES "
            "por historia y vincula rf_relacionados. No incluyas prioridad."
        ),
        clave="historias_usuario",
        atributo="historias_usuario",
        nodo="nodo_historias_usuario",
    )


def nodo_modelado(state: GraphState, cliente: ClienteEstructurado) -> dict[str, object]:
    """Ejecuta Subagente 4 en modalidad CUS, HU o AMBOS según la selección fija de la corrida."""
    modalidad = state.get("modalidad_modelado")
    if modalidad not in {"CUS", "HU", "AMBOS"}:
        return {"errores": ["Debe especificar modalidad_modelado válida: CUS, HU o AMBOS"]}

    if modalidad == "CUS":
        res_cus = nodo_casos_uso(state, cliente)
        return res_cus if "errores" in res_cus else {**res_cus, "historias_usuario": []}

    if modalidad == "HU":
        res_hu = nodo_historias_usuario(state, cliente)
        return res_hu if "errores" in res_hu else {**res_hu, "casos_uso": []}

    res_cus = nodo_casos_uso(state, cliente)
    res_hu = nodo_historias_usuario(state, cliente)
    trazas = list(res_cus.get("trazas", [])) + list(res_hu.get("trazas", []))  # type: ignore[arg-type]
    errores = list(res_cus.get("errores", [])) + list(res_hu.get("errores", []))  # type: ignore[arg-type]
    if errores:
        return {"errores": errores, "trazas": trazas}
    return {
        "casos_uso": res_cus.get("casos_uso", []),
        "historias_usuario": res_hu.get("historias_usuario", []),
        "trazas": trazas,
    }
