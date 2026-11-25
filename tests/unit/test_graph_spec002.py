from pathlib import Path
from unittest.mock import Mock
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command
from src.graph.workflow import construir_grafo
from src.schemas.contracts import (
    CasoUso,
    CriterioAceptacion,
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

TEXTO = "El alumno debe consultar libros disponibles en el catálogo y solicitar préstamos."
RF_1 = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)
RF_EDIT = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo por sede",
    descripcion="El sistema debe permitir filtrar libros disponibles por sede.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)
RNF_1 = RequisitoNoFuncional(
    id="RNF-01",
    categoria_iso="Rendimiento",
    descripcion="La consulta debe responder en menos de 2 segundos.",
    metrica_objetiva="Tiempo de respuesta",
    valor_umbral="2 s",
)
INC_1 = Inconsistencia(
    tipo="vacío",
    severidad="Alta",
    descripcion="No se especifica el límite de libros por alumno.",
    pregunta_clarificacion="¿Cuántos libros puede prestar simultáneamente?",
)
CUS_1 = CasoUso(
    id="CUS-01",
    nombre="Consultar catálogo",
    actor_principal="Alumno",
    precondiciones=["Estar autenticado"],
    flujo_principal=["1. Ingresar búsqueda", "2. Mostrar resultados"],
    flujos_alternativos=[],
    postcondiciones=["Catálogo consultado"],
    rf_relacionados=["RF-01"],
)
HU_1 = HistoriaUsuario(
    id="HU-01",
    titulo="Consulta de catálogo",
    como="Alumno",
    quiero="buscar libros disponibles por título",
    para_que="conocer qué libros puedo solicitar",
    criterios_aceptacion=[
        CriterioAceptacion(
            dado="que existen libros disponibles",
            cuando="busco por título",
            entonces="veo los ejemplares disponibles",
        )
    ],
    rf_relacionados=["RF-01"],
)
HU_2 = HistoriaUsuario(
    id="HU-02",
    titulo="Consulta de catálogo por sede",
    como="Alumno",
    quiero="filtrar libros disponibles por sede",
    para_que="solicitar ejemplares cercanos",
    criterios_aceptacion=[
        CriterioAceptacion(
            dado="que selecciono una sede",
            cuando="ejecuto la búsqueda",
            entonces="solo aparecen libros de esa sede",
        )
    ],
    rf_relacionados=["RF-01"],
)


def _cliente_dual(contadores: dict[str, int] | None = None) -> Mock:
    registro = contadores if contadores is not None else {}

    def _generar(esquema: type, _instrucciones: str) -> object:
        nombre = esquema.__name__
        registro[nombre] = registro.get(nombre, 0) + 1
        if esquema is SalidaRF:
            return SalidaRF(requisitos=[RF_1])
        if esquema is SalidaRNF:
            return SalidaRNF(requisitos=[RNF_1])
        if esquema is SalidaInconsistencias:
            return SalidaInconsistencias(inconsistencias=[INC_1])
        if esquema is SalidaCasosUso:
            return SalidaCasosUso(casos_uso=[CUS_1])
        if esquema is SalidaHU:
            return SalidaHU(historias_usuario=[HU_2] if registro[nombre] > 1 else [HU_1])
        raise ValueError(f"Esquema inesperado: {nombre}")

    return Mock(generar=Mock(side_effect=_generar))


def test_req_01_grafo_rechaza_envio_sin_modalidad_y_guarda_advertencias_en_ambos() -> None:
    contadores: dict[str, int] = {}
    grafo = construir_grafo(_cliente_dual(contadores), checkpointer=InMemorySaver())
    sin_mod = grafo.invoke(
        {"analisis_id": "S2-01", "texto_usuario": TEXTO},
        config={"configurable": {"thread_id": "s2-01a"}},
    )
    assert sin_mod["estado"] == "FALLIDO"
    assert contadores == {}

    ambos = grafo.invoke(
        {"analisis_id": "S2-01b", "texto_usuario": TEXTO, "modalidad_modelado": "AMBOS"},
        config={"configurable": {"thread_id": "s2-01b"}},
    )
    assert len(ambos["advertencias"]) == 2
    assert "demorará más" in " ".join(ambos["advertencias"]).lower()


def test_req_02_grafo_genera_exclusivamente_hu_cuando_se_elige_hu() -> None:
    contadores: dict[str, int] = {}
    grafo = construir_grafo(_cliente_dual(contadores), checkpointer=InMemorySaver())
    res = grafo.invoke(
        {"analisis_id": "S2-02", "texto_usuario": TEXTO, "modalidad_modelado": "HU"},
        config={"configurable": {"thread_id": "s2-02"}},
    )
    assert res["estado"] == "PENDIENTE_APROBACION"
    assert res["historias_usuario"] == [HU_1]
    assert res["casos_uso"] == []
    assert "SalidaCasosUso" not in contadores


def test_req_02_grafo_genera_cus_y_hu_cuando_se_elige_ambos() -> None:
    grafo = construir_grafo(_cliente_dual(), checkpointer=InMemorySaver())
    res = grafo.invoke(
        {"analisis_id": "S2-03", "texto_usuario": TEXTO, "modalidad_modelado": "AMBOS"},
        config={"configurable": {"thread_id": "s2-03"}},
    )
    assert res["estado"] == "PENDIENTE_APROBACION"
    assert res["casos_uso"] == [CUS_1]
    assert res["historias_usuario"] == [HU_1]


def test_req_05_grafo_rechaza_cambio_modalidad_en_hitl_y_regenera_en_modalidad_original() -> None:
    grafo = construir_grafo(_cliente_dual(), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "s2-05"}}
    pausado = grafo.invoke(
        {"analisis_id": "S2-05", "texto_usuario": TEXTO, "modalidad_modelado": "HU"},
        config=cfg,
    )
    assert pausado["estado"] == "PENDIENTE_APROBACION"

    rechazado = grafo.invoke(
        Command(resume={"accion": "regenerar_cus", "modalidad_solicitada": "CUS"}),
        config=cfg,
    )
    assert rechazado["estado"] == "PENDIENTE_APROBACION"
    assert "fija" in rechazado["errores"][-1].lower()
    assert rechazado["modalidad_modelado"] == "HU"

    regenerado = grafo.invoke(
        Command(resume={"accion": "regenerar_cus", "rf_editados": [RF_EDIT]}),
        config=cfg,
    )
    assert regenerado["estado"] == "PENDIENTE_APROBACION"
    assert regenerado["modalidad_modelado"] == "HU"
    assert regenerado["historias_usuario"] == [HU_2]
    assert regenerado["casos_uso"] == []


def test_req_06_grafo_e2e_sqlite_consolida_reporte_inmutable_con_modalidad_ambos(tmp_path: Path) -> None:
    archivo = tmp_path / "solicitud.txt"
    archivo.write_text(TEXTO, encoding="utf-8")
    db_path = tmp_path / "checkpoints.db"

    with SqliteSaver.from_conn_string(str(db_path)) as saver:
        grafo = construir_grafo(_cliente_dual(), checkpointer=saver)
        cfg = {"configurable": {"thread_id": "e2e-ambos"}}

        pausado = grafo.invoke(
            {"analisis_id": "E2E-01", "ruta_archivo": str(archivo), "modalidad_modelado": "AMBOS"},
            config=cfg,
        )
        assert pausado["estado"] == "PENDIENTE_APROBACION"
        assert pausado["casos_uso"] == [CUS_1]
        assert pausado["historias_usuario"] == [HU_1]

        re_pausado = grafo.invoke(
            Command(resume={"accion": "regenerar_cus", "rf_editados": [RF_EDIT]}),
            config=cfg,
        )
        assert re_pausado["historias_usuario"] == [HU_2]

        final = grafo.invoke(
            Command(
                resume={
                    "accion": "aprobar",
                    "respuestas_clarificacion": {"0": "Máximo 3 libros"},
                    "comentarios_analista": "E2E validado",
                }
            ),
            config=cfg,
        )
        assert final["estado"] == "APROBADO"
        reporte = final["reporte_consolidado"]
        assert reporte is not None
        assert reporte.modalidad_modelado == "AMBOS"
        assert reporte.casos_uso == [CUS_1]
        assert reporte.historias_usuario == [HU_2]
        assert final["inconsistencias"][0].respuesta_analista == "Máximo 3 libros"
