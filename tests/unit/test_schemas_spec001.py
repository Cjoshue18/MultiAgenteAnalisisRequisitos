import operator
from typing import get_args, get_origin, get_type_hints
import pytest
from pydantic import ValidationError
from src.schemas.contracts import (
    CasoUso,
    DecisionRevision,
    Inconsistencia,
    ReporteConsolidado,
    RequisitoFuncional,
    TrazaEjecucion,
    consolidar_reporte,
)
from src.schemas.state import GraphState

RF_BASE = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)


def test_req_03_graph_state_acumula_errores_con_reducer() -> None:
    hints = get_type_hints(GraphState, include_extras=True)
    assert "errores" in hints
    args = get_args(hints["errores"])
    assert operator.add in args


def test_req_06_inconsistencia_acepta_respuesta_analista_y_decision_revision() -> None:
    inc = Inconsistencia(
        tipo="vacío",
        severidad="Alta",
        descripcion="Falta definir límite de préstamos simultáneos.",
        pregunta_clarificacion="¿Cuántos libros puede prestar un alumno?",
        respuesta_analista="Hasta 3 libros por 7 días.",
    )
    decision = DecisionRevision(
        accion="regenerar_cus",
        rf_editados=[RF_BASE],
        respuestas_clarificacion={"INC-1": "Hasta 3 libros por 7 días."},
        comentarios_analista="Se actualizó RF-01 con el límite.",
    )
    assert inc.respuesta_analista == "Hasta 3 libros por 7 días."
    assert decision.accion == "regenerar_cus"
    assert decision.rf_editados == [RF_BASE]


@pytest.mark.parametrize("estado_no_aprobado", ["EN_PROCESO", "PENDIENTE_APROBACION", "FALLIDO"])
def test_req_07_reporte_consolidado_rechaza_estado_no_aprobado(estado_no_aprobado: str) -> None:
    with pytest.raises(ValueError, match="aprobación"):
        consolidar_reporte(
            analisis_id="ANA-001",
            estado=estado_no_aprobado,
            requisitos_funcionales=[RF_BASE],
            requisitos_no_funcionales=[],
            inconsistencias=[],
            casos_uso=[],
            respuestas_clarificacion={},
            comentarios_analista="",
        )


def test_req_07_reporte_consolidado_aprobado_es_inmutable() -> None:
    reporte = consolidar_reporte(
        analisis_id="ANA-001",
        estado="APROBADO",
        requisitos_funcionales=[RF_BASE],
        requisitos_no_funcionales=[],
        inconsistencias=[],
        casos_uso=[],
        respuestas_clarificacion={"0": "Confirmado"},
        comentarios_analista="Aprobado por analista.",
    )
    assert isinstance(reporte, ReporteConsolidado)
    assert reporte.estado == "APROBADO"
    with pytest.raises(ValidationError):
        reporte.comentarios_analista = "Mutación ilegal"  # type: ignore[misc]


def test_req_08_traza_ejecucion_registra_estado_y_timestamps() -> None:
    hints = get_type_hints(GraphState, include_extras=True)
    assert operator.add in get_args(hints["trazas"])
    traza = TrazaEjecucion(
        nodo="nodo_rf",
        estado="COMPLETADO",
        inicio_iso="2026-11-25T16:00:00Z",
        fin_iso="2026-11-25T16:00:01Z",
        detalle="1 RF extraído",
    )
    assert traza.estado == "COMPLETADO"
    assert get_origin(hints["trazas"]) is not None


def test_req_03_rechaza_elementos_vacios_en_listas_de_contratos() -> None:
    with pytest.raises(ValidationError):
        RequisitoFuncional(
            id="RF-01",
            nombre="Consultar catálogo",
            descripcion="El sistema debe permitir consultar libros.",
            actores=[""],
            referencia_texto="consultar libros",
        )
    with pytest.raises(ValidationError):
        CasoUso(
            id="CUS-01",
            nombre="Consultar catálogo",
            actor_principal="Alumno",
            precondiciones=[""],
            flujo_principal=["1. Ingresar búsqueda"],
            flujos_alternativos=[],
            postcondiciones=[],
        )
