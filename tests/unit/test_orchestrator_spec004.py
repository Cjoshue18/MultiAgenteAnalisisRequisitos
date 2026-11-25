from pathlib import Path
from unittest.mock import Mock
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
import pytest
from src.persistence.repository import RepositorioSQLite
from src.schemas.contracts import (
    CasoUso,
    CriterioAceptacion,
    DecisionRevision,
    HistoriaUsuario,
    Inconsistencia,
    RequisitoFuncional,
    RequisitoNoFuncional,
    SalidaCasosUso,
    SalidaHU,
    SalidaInconsistencias,
    SalidaRF,
    SalidaRNF,
)
from src.services.orchestrator import OrquestadorService

TEXTO = "El alumno debe consultar libros disponibles en el catálogo y solicitar préstamos."
RF_1 = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)
RNF_1 = RequisitoNoFuncional(
    id="RNF-01",
    categoria_iso="Rendimiento",
    descripcion="La consulta debe responder en menos de 2 segundos.",
    metrica_objetiva="Latencia",
    valor_umbral="2 s",
)
INC_1 = Inconsistencia(
    tipo="vacío",
    severidad="Alta",
    descripcion="No se especifica límite de préstamos.",
    pregunta_clarificacion="¿Cuántos libros puede prestar un alumno?",
)
CUS_1 = CasoUso(
    id="CUS-01",
    nombre="Consultar catálogo",
    actor_principal="Alumno",
    precondiciones=["Estar autenticado"],
    flujo_principal=["1. Ingresar búsqueda", "2. Mostrar resultados"],
    flujos_alternativos=[],
    postcondiciones=["Resultados mostrados"],
    rf_relacionados=["RF-01"],
)
HU_1 = HistoriaUsuario(
    id="HU-01",
    titulo="Consulta de catálogo",
    como="Alumno",
    quiero="buscar libros disponibles",
    para_que="solicitar préstamos",
    criterios_aceptacion=[
        CriterioAceptacion(
            dado="que existen libros",
            cuando="busco por título",
            entonces="veo disponibilidad",
        )
    ],
    rf_relacionados=["RF-01"],
)


def _cliente_mock() -> Mock:
    def _generar(esquema: type, _instrucciones: str) -> object:
        if esquema is SalidaRF:
            return SalidaRF(requisitos=[RF_1])
        if esquema is SalidaRNF:
            return SalidaRNF(requisitos=[RNF_1])
        if esquema is SalidaInconsistencias:
            return SalidaInconsistencias(inconsistencias=[INC_1])
        if esquema is SalidaCasosUso:
            return SalidaCasosUso(casos_uso=[CUS_1])
        if esquema is SalidaHU:
            return SalidaHU(historias_usuario=[HU_1])
        raise ValueError(f"Esquema inesperado: {esquema}")

    return Mock(generar=Mock(side_effect=_generar))


def test_req_01_fachada_rechaza_proyecto_inexistente_y_soporta_multiples_corridas(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'f1.db'}")
    servicio = OrquestadorService(_cliente_mock(), repo, InMemorySaver(), tmp_path / "rep")

    with pytest.raises(ValueError, match="Proyecto"):
        servicio.iniciar_analisis("PRY-INEXISTENTE", "CUS", texto=TEXTO)

    proy = servicio.crear_proyecto("Biblioteca")
    a1 = servicio.iniciar_analisis(proy.proyecto_id, "CUS", texto=TEXTO)
    a2 = servicio.iniciar_analisis(proy.proyecto_id, "HU", texto=TEXTO)
    assert a1.analisis_id != a2.analisis_id
    assert len(servicio.listar_analisis(proyecto_id=proy.proyecto_id)) == 2


def test_req_02_fachada_ejecuta_ciclo_completo_y_consulta_historial(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'f2.db'}")
    servicio = OrquestadorService(_cliente_mock(), repo, InMemorySaver(), tmp_path / "rep")
    proy = servicio.crear_proyecto("Biblioteca")

    iniciado = servicio.iniciar_analisis(proy.proyecto_id, "HU", texto=TEXTO)
    assert iniciado.estado == "PENDIENTE_APROBACION"
    assert iniciado.version == 1

    consultado = servicio.obtener_analisis(iniciado.analisis_id)
    assert consultado.historias_usuario == [HU_1]

    aprobado = servicio.enviar_revision(
        iniciado.analisis_id,
        DecisionRevision(accion="aprobar", respuestas_clarificacion={"0": "3 libros"}, comentarios_analista="OK"),
    )
    assert aprobado.estado == "APROBADO"
    assert aprobado.reporte_consolidado is not None
    assert len(servicio.listar_analisis()) == 1


def test_req_04_fachada_bloquea_revision_sobre_aprobado_y_permite_nueva_version(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'f4.db'}")
    servicio = OrquestadorService(_cliente_mock(), repo, InMemorySaver(), tmp_path / "rep")
    proy = servicio.crear_proyecto("Biblioteca")

    v1 = servicio.iniciar_analisis(proy.proyecto_id, "CUS", texto=TEXTO)
    v1_ok = servicio.enviar_revision(v1.analisis_id, DecisionRevision(accion="aprobar"))
    assert v1_ok.estado == "APROBADO"

    with pytest.raises(ValueError, match="inmutable"):
        servicio.enviar_revision(v1.analisis_id, DecisionRevision(accion="aprobar"))

    v2 = servicio.crear_nueva_version(v1.analisis_id)
    assert v2.version == 2
    assert v2.estado == "PENDIENTE_APROBACION"
    v2_ok = servicio.enviar_revision(v2.analisis_id, DecisionRevision(accion="aprobar", comentarios_analista="v2"))
    assert v2_ok.estado == "APROBADO"
    assert servicio.obtener_analisis(v1.analisis_id).estado == "APROBADO"


def test_req_05_fachada_bloquea_exportacion_sin_aprobacion(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'f5.db'}")
    servicio = OrquestadorService(_cliente_mock(), repo, InMemorySaver(), tmp_path / "rep")
    proy = servicio.crear_proyecto("Biblioteca")
    pendiente = servicio.iniciar_analisis(proy.proyecto_id, "CUS", texto=TEXTO)

    with pytest.raises(ValueError, match="APROBADO"):
        servicio.exportar_analisis(pendiente.analisis_id, ["md", "json"])


def test_req_06_fachada_e2e_sqlite_exporta_los_cuatro_formatos(tmp_path: Path) -> None:
    repo = RepositorioSQLite(f"sqlite:///{tmp_path / 'negocio.db'}")
    with SqliteSaver.from_conn_string(str(tmp_path / "checkpoints.db")) as saver:
        servicio = OrquestadorService(_cliente_mock(), repo, saver, tmp_path / "reportes")
        proy = servicio.crear_proyecto("Biblioteca E2E")
        analisis = servicio.iniciar_analisis(proy.proyecto_id, "AMBOS", texto=TEXTO)
        aprobado = servicio.enviar_revision(
            analisis.analisis_id,
            DecisionRevision(accion="aprobar", respuestas_clarificacion={"0": "Máximo 3 libros"}),
        )
        assert aprobado.estado == "APROBADO"

        archivos = servicio.exportar_analisis(analisis.analisis_id, ["md", "json", "pdf", "docx"])
        assert set(archivos.keys()) == {"md", "json", "pdf", "docx"}
        assert all(ruta.exists() and ruta.stat().st_size > 0 for ruta in archivos.values())
