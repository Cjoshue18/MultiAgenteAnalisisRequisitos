from datetime import datetime, timezone
from typing import Literal
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from src.agents.functional_agent import nodo_requisitos_funcionales
from src.agents.inconsistency_agent import nodo_inconsistencias
from src.agents.nonfunctional_agent import nodo_requisitos_no_funcionales
from src.agents.use_case_agent import nodo_casos_uso
from src.schemas.contracts import (
    DecisionRevision,
    Inconsistencia,
    TrazaEjecucion,
    consolidar_reporte,
)
from src.schemas.state import GraphState
from src.services.ingesta import preparar_ingesta
from src.services.llm_client import ClienteEstructurado


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ultimo_estado_traza(state: GraphState, nodo: str) -> str | None:
    for traza in reversed(state.get("trazas") or []):
        nombre = traza.nodo if isinstance(traza, TrazaEjecucion) else traza.get("nodo")
        if nombre == nodo:
            return traza.estado if isinstance(traza, TrazaEjecucion) else traza.get("estado")
    return None


def _ya_completo(state: GraphState, nodo: str, clave_datos: str) -> bool:
    return bool(state.get(clave_datos)) and _ultimo_estado_traza(state, nodo) == "COMPLETADO"


def _aplicar_respuestas_inconsistencias(
    inconsistencias: list[Inconsistencia],
    respuestas: dict[str, str],
) -> list[Inconsistencia]:
    actualizadas: list[Inconsistencia] = []
    for idx, item in enumerate(inconsistencias):
        modelo = item if isinstance(item, Inconsistencia) else Inconsistencia.model_validate(item)
        respuesta = respuestas.get(str(idx)) or respuestas.get(f"INC-{idx + 1}")
        actualizadas.append(modelo.model_copy(update={"respuesta_analista": respuesta}) if respuesta else modelo)
    return actualizadas


def construir_grafo(
    cliente: ClienteEstructurado,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Construye y compila el StateGraph multiagente con Fork/Join, checkpoints y HITL."""

    def nodo_ingesta(state: GraphState) -> dict[str, object]:
        inicio = _ahora_iso()
        try:
            res = preparar_ingesta(
                texto=state.get("texto_usuario"),
                ruta_archivo=state.get("ruta_archivo"),
                tamano_bytes_override=state.get("tamano_bytes") or None,
            )
            return {
                "estado": "EN_PROCESO",
                "texto_usuario": res.texto_limpio,
                "tamano_bytes": res.tamano_bytes,
                "estrategia_ingesta": res.estrategia,
                "fragmentos": res.fragmentos,
                "trazas": [
                    TrazaEjecucion(
                        nodo="nodo_ingesta",
                        estado="COMPLETADO",
                        inicio_iso=inicio,
                        fin_iso=_ahora_iso(),
                        detalle=f"{res.estrategia}:{len(res.fragmentos)}",
                    )
                ],
            }
        except ValueError as exc:
            return {
                "estado": "FALLIDO",
                "errores": [str(exc)],
                "trazas": [
                    TrazaEjecucion(
                        nodo="nodo_ingesta",
                        estado="FALLIDO",
                        inicio_iso=inicio,
                        fin_iso=_ahora_iso(),
                        detalle=str(exc),
                    )
                ],
            }

    def nodo_rf(state: GraphState) -> dict[str, object]:
        if _ya_completo(state, "nodo_rf", "requisitos_funcionales"):
            return {}
        return nodo_requisitos_funcionales(state, cliente)

    def nodo_rnf(state: GraphState) -> dict[str, object]:
        if _ya_completo(state, "nodo_rnf", "requisitos_no_funcionales"):
            return {}
        return nodo_requisitos_no_funcionales(state, cliente)

    def nodo_sincronizar(state: GraphState) -> dict[str, object]:
        rf_ok = _ultimo_estado_traza(state, "nodo_rf") == "COMPLETADO"
        rnf_ok = _ultimo_estado_traza(state, "nodo_rnf") == "COMPLETADO"
        return {"estado": "EN_PROCESO" if (rf_ok and rnf_ok) else "FALLIDO"}

    def nodo_inc(state: GraphState) -> dict[str, object]:
        return nodo_inconsistencias(state, cliente)

    def nodo_cus(state: GraphState) -> dict[str, object]:
        return nodo_casos_uso(state, cliente)

    def nodo_marcar_fallido(_state: GraphState) -> dict[str, object]:
        return {"estado": "FALLIDO"}

    def nodo_preparar_revision(_state: GraphState) -> dict[str, object]:
        return {"estado": "PENDIENTE_APROBACION"}

    def nodo_revision_humana(
        state: GraphState,
    ) -> Command[Literal["nodo_casos_uso", "nodo_consolidador"]]:
        decision_raw = interrupt(
            {
                "estado": "PENDIENTE_APROBACION",
                "requisitos_funcionales": state.get("requisitos_funcionales", []),
                "requisitos_no_funcionales": state.get("requisitos_no_funcionales", []),
                "inconsistencias": state.get("inconsistencias", []),
                "casos_uso": state.get("casos_uso", []),
            }
        )
        decision = DecisionRevision.model_validate(decision_raw)
        rf_final = decision.rf_editados if decision.rf_editados is not None else state.get("requisitos_funcionales", [])
        rnf_final = (
            decision.rnf_editados if decision.rnf_editados is not None else state.get("requisitos_no_funcionales", [])
        )
        cus_final = decision.casos_uso_editados if decision.casos_uso_editados is not None else state.get("casos_uso", [])
        inc_act = _aplicar_respuestas_inconsistencias(
            state.get("inconsistencias", []),
            decision.respuestas_clarificacion,
        )
        updates: dict[str, object] = {
            "rf_aprobados": rf_final,
            "requisitos_funcionales": rf_final,
            "requisitos_no_funcionales": rnf_final,
            "inconsistencias": inc_act,
            "respuestas_clarificacion": decision.respuestas_clarificacion,
            "comentarios_analista": decision.comentarios_analista,
        }
        if decision.accion == "regenerar_cus":
            updates["estado"] = "EN_PROCESO"
            return Command(update=updates, goto="nodo_casos_uso")
        updates["casos_uso"] = cus_final
        return Command(update=updates, goto="nodo_consolidador")

    def nodo_consolidador(state: GraphState) -> dict[str, object]:
        inicio = _ahora_iso()
        reporte = consolidar_reporte(
            analisis_id=state.get("analisis_id") or "ANA-000",
            estado="APROBADO",
            requisitos_funcionales=state.get("requisitos_funcionales", []),
            requisitos_no_funcionales=state.get("requisitos_no_funcionales", []),
            inconsistencias=state.get("inconsistencias", []),
            casos_uso=state.get("casos_uso", []),
            respuestas_clarificacion=state.get("respuestas_clarificacion", {}),
            comentarios_analista=state.get("comentarios_analista", ""),
        )
        return {
            "estado": "APROBADO",
            "reporte_consolidado": reporte,
            "trazas": [
                TrazaEjecucion(
                    nodo="nodo_consolidador",
                    estado="COMPLETADO",
                    inicio_iso=inicio,
                    fin_iso=_ahora_iso(),
                    detalle="Reporte consolidado aprobado",
                )
            ],
        }

    def _ruta_ingesta(state: GraphState) -> list[str] | str:
        if state.get("estado") == "FALLIDO":
            return END
        return ["nodo_rf", "nodo_rnf"]

    def _ruta_sincronizar(state: GraphState) -> str:
        return END if state.get("estado") == "FALLIDO" else "nodo_inconsistencias"

    def _ruta_tras_nodo(nombre_nodo: str, siguiente: str) -> object:
        def _decidir(state: GraphState) -> str:
            return siguiente if _ultimo_estado_traza(state, nombre_nodo) == "COMPLETADO" else "nodo_marcar_fallido"

        return _decidir

    grafo = StateGraph(GraphState)
    grafo.add_node("nodo_ingesta", nodo_ingesta)
    grafo.add_node("nodo_rf", nodo_rf)
    grafo.add_node("nodo_rnf", nodo_rnf)
    grafo.add_node("nodo_sincronizar", nodo_sincronizar)
    grafo.add_node("nodo_inconsistencias", nodo_inc)
    grafo.add_node("nodo_casos_uso", nodo_cus)
    grafo.add_node("nodo_marcar_fallido", nodo_marcar_fallido)
    grafo.add_node("nodo_preparar_revision", nodo_preparar_revision)
    grafo.add_node("nodo_revision_humana", nodo_revision_humana)
    grafo.add_node("nodo_consolidador", nodo_consolidador)

    grafo.add_edge(START, "nodo_ingesta")
    grafo.add_conditional_edges("nodo_ingesta", _ruta_ingesta, ["nodo_rf", "nodo_rnf", END])
    grafo.add_edge("nodo_rf", "nodo_sincronizar")
    grafo.add_edge("nodo_rnf", "nodo_sincronizar")
    grafo.add_conditional_edges("nodo_sincronizar", _ruta_sincronizar, ["nodo_inconsistencias", END])
    grafo.add_conditional_edges(
        "nodo_inconsistencias",
        _ruta_tras_nodo("nodo_inconsistencias", "nodo_casos_uso"),
        ["nodo_casos_uso", "nodo_marcar_fallido"],
    )
    grafo.add_conditional_edges(
        "nodo_casos_uso",
        _ruta_tras_nodo("nodo_casos_uso", "nodo_preparar_revision"),
        ["nodo_preparar_revision", "nodo_marcar_fallido"],
    )
    grafo.add_edge("nodo_marcar_fallido", END)
    grafo.add_edge("nodo_preparar_revision", "nodo_revision_humana")
    grafo.add_edge("nodo_consolidador", END)
    return grafo.compile(checkpointer=checkpointer)
