from typing import Dict, Any
from langgraph.graph import StateGraph, END
from src.schemas.state import GraphState
from src.agents.orchestrator import nodo_orquestador
from src.agents.functional_agent import nodo_requisitos_funcionales
from src.agents.rnf_agent import nodo_requisitos_no_funcionales
from src.agents.inconsistency_agent import nodo_inconsistencias
from src.agents.cus_agent import nodo_casos_de_uso
from src.core.logger import get_logger

logger = get_logger(__name__)


def construir_grafo() -> StateGraph:
    """Construye el StateGraph con el flujo canonico:

    Orquestador -> Fork concurrente (RF y RNF) -> Join -> Inconsistencias -> CUS -> FIN
    """
    workflow = StateGraph(GraphState)

    # Nodos
    workflow.add_node("orquestador", nodo_orquestador)
    workflow.add_node("subrf", nodo_requisitos_funcionales)
    workflow.add_node("subrnf", nodo_requisitos_no_funcionales)
    workflow.add_node("subinc", nodo_inconsistencias)
    workflow.add_node("subcus", nodo_casos_de_uso)

    # Entrada
    workflow.set_entry_point("orquestador")

    # Fase 1: Orquestador valida entrada
    # Fase 2: Fork concurrente (RF y RNF en paralelo)
    workflow.add_edge("orquestador", "subrf")
    workflow.add_edge("orquestador", "subrnf")

    # Fase 3: Join sincronizacion hacia Inconsistencias
    workflow.add_edge("subrf", "subinc")
    workflow.add_edge("subrnf", "subinc")

    # Fase 4: Casos de Uso (se nutre de RF validados)
    workflow.add_edge("subinc", "subcus")

    # Fase 5: Fin
    workflow.add_edge("subcus", END)

    return workflow.compile()


def ejecutar_analisis(texto_usuario: str) -> Dict[str, Any]:
    """Ejecuta el pipeline multiagente completo y retorna el estado final."""
    grafo = construir_grafo()
    estado_inicial = GraphState(texto_usuario=texto_usuario)
    try:
        estado_final = grafo.invoke(estado_inicial)
        logger.info("Analisis completado: %d RF, %d RNF, %d inconsistencias, %d CUS",
                    len(estado_final.get("requisitos_funcionales", [])),
                    len(estado_final.get("requisitos_no_funcionales", [])),
                    len(estado_final.get("inconsistencias", [])),
                    len(estado_final.get("casos_de_uso", [])))
        return estado_final
    except Exception as exc:
        logger.error("Error ejecutando grafo: %s", str(exc))
        return {"errores": [f"Error ejecutando grafo: {str(exc)}"]}
