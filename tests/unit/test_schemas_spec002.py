import pytest
from pydantic import ValidationError
from src.schemas.contracts import (
    CriterioAceptacion,
    DecisionRevision,
    HistoriaUsuario,
    RequisitoFuncional,
    consolidar_reporte,
    validar_decision_revision,
)
from src.schemas.state import GraphState

RF_BASE = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)


def _hu_base() -> HistoriaUsuario:
    return HistoriaUsuario(
        id="HU-01",
        titulo="Consulta de catálogo disponible",
        como="Alumno",
        quiero="buscar libros disponibles por título o autor",
        para_que="conocer qué ejemplares puedo solicitar en préstamo",
        criterios_aceptacion=[
            CriterioAceptacion(
                dado="que existen libros disponibles en catálogo",
                cuando="ingreso un criterio de búsqueda",
                entonces="el sistema muestra los ejemplares coincidentes",
            )
        ],
        rf_relacionados=["RF-01"],
    )


def test_req_04_historia_usuario_valida_narrativa_y_criterios_dado_cuando_entonces() -> None:
    hu = _hu_base()
    assert hu.id == "HU-01"
    assert hu.criterios_aceptacion[0].dado.startswith("que")
    assert not hasattr(hu, "prioridad")


def test_req_04_rechaza_hu_sin_criterios_o_narrativa_incompleta() -> None:
    with pytest.raises(ValidationError):
        HistoriaUsuario(
            id="HU-01",
            titulo="Consulta sin criterios",
            como="Alumno",
            quiero="buscar libros disponibles",
            para_que="solicitar un préstamo",
            criterios_aceptacion=[],
            rf_relacionados=["RF-01"],
        )
    with pytest.raises(ValidationError):
        HistoriaUsuario(
            id="HU-01",
            titulo="Consulta incompleta",
            como="A",
            quiero="x",
            para_que="y",
            criterios_aceptacion=[
                CriterioAceptacion(dado="hay libros", cuando="busco", entonces="los veo")
            ],
            rf_relacionados=["RF-01"],
        )


def test_req_05_validar_decision_revision_rechaza_cambio_de_modalidad() -> None:
    decision_valida = DecisionRevision(accion="regenerar_cus", modalidad_solicitada="HU")
    validar_decision_revision("HU", decision_valida)

    decision_cambio = DecisionRevision(accion="regenerar_cus", modalidad_solicitada="CUS")
    with pytest.raises(ValueError, match="fija"):
        validar_decision_revision("HU", decision_cambio)


def test_req_06_consolidar_reporte_preserva_modalidad_e_historias_aprobadas() -> None:
    hu = _hu_base()
    assert "modalidad_modelado" in GraphState.__annotations__
    assert "historias_usuario" in GraphState.__annotations__
    assert "advertencias" in GraphState.__annotations__
    reporte = consolidar_reporte(
        analisis_id="ANA-002",
        estado="APROBADO",
        modalidad_modelado="HU",
        requisitos_funcionales=[RF_BASE],
        requisitos_no_funcionales=[],
        inconsistencias=[],
        casos_uso=[],
        historias_usuario=[hu],
        respuestas_clarificacion={},
        comentarios_analista="Aprobado en modalidad ágil.",
    )
    assert reporte.modalidad_modelado == "HU"
    assert reporte.historias_usuario == [hu]
