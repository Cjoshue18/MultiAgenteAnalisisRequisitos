from unittest.mock import Mock
import pytest
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from src.graph.workflow import construir_grafo
from src.schemas.contracts import (
    CasoUso,
    Inconsistencia,
    RequisitoFuncional,
    RequisitoNoFuncional,
    SalidaCasosUso,
    SalidaInconsistencias,
    SalidaRF,
    SalidaRNF,
    consolidar_reporte,
)

TEXTO_CORTO = "El alumno debe consultar libros disponibles y solicitar préstamos en línea."
RF_1 = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)
RF_EDIT = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo por facultad",
    descripcion="El sistema debe permitir consultar libros filtrando por facultad.",
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
    descripcion="No se indica el límite de libros por préstamo.",
    pregunta_clarificacion="¿Cuántos libros puede prestar simultáneamente un alumno?",
)
CUS_1 = CasoUso(
    id="CUS-01",
    nombre="Consultar catálogo",
    actor_principal="Alumno",
    precondiciones=["Estar autenticado"],
    flujo_principal=["1. Ingresar criterio de búsqueda", "2. Mostrar resultados disponibles"],
    flujos_alternativos=["Sin resultados: mostrar aviso"],
    postcondiciones=["Catálogo consultado"],
    rf_relacionados=["RF-01"],
)
CUS_2 = CasoUso(
    id="CUS-02",
    nombre="Consultar catálogo por facultad",
    actor_principal="Alumno",
    precondiciones=["Estar autenticado"],
    flujo_principal=["1. Seleccionar facultad", "2. Mostrar resultados filtrados"],
    flujos_alternativos=[],
    postcondiciones=["Resultados filtrados"],
    rf_relacionados=["RF-01"],
)


def _cliente_por_esquema(contadores: dict[str, int] | None = None) -> Mock:
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
            return SalidaCasosUso(casos_uso=[CUS_2] if registro[nombre] > 1 else [CUS_1])
        raise ValueError(f"Esquema inesperado: {nombre}")

    return Mock(generar=Mock(side_effect=_generar))


def test_req_01_grafo_rechaza_entrada_invalida_sin_ejecutar_extractores() -> None:
    contadores: dict[str, int] = {}
    grafo = construir_grafo(_cliente_por_esquema(contadores), checkpointer=InMemorySaver())
    res = grafo.invoke(
        {"analisis_id": "A-01", "texto_usuario": "muy corto"},
        config={"configurable": {"thread_id": "t-01"}},
    )
    assert res["estado"] == "FALLIDO"
    assert res["errores"]
    assert contadores == {}


def test_req_02_grafo_procesa_camino_directo_y_camino_por_lotes() -> None:
    cont_dir: dict[str, int] = {}
    grafo_dir = construir_grafo(_cliente_por_esquema(cont_dir), checkpointer=InMemorySaver())
    res_dir = grafo_dir.invoke(
        {"analisis_id": "A-02a", "texto_usuario": TEXTO_CORTO},
        config={"configurable": {"thread_id": "t-02a"}},
    )
    assert res_dir["estrategia_ingesta"] == "directa"
    assert cont_dir["SalidaRF"] == 1

    texto_largo = " ".join(f"requisito{i}" for i in range(1500))
    cont_lot: dict[str, int] = {}
    grafo_lot = construir_grafo(_cliente_por_esquema(cont_lot), checkpointer=InMemorySaver())
    res_lot = grafo_lot.invoke(
        {"analisis_id": "A-02b", "texto_usuario": texto_largo},
        config={"configurable": {"thread_id": "t-02b"}},
    )
    assert res_lot["estrategia_ingesta"] == "lotes"
    assert cont_lot["SalidaRF"] > 1


def test_req_03_grafo_acumula_errores_paralelos_de_rf_y_rnf() -> None:
    def _fallar_ambos(esquema: type, _instrucciones: str) -> object:
        raise TimeoutError(f"fallo-{esquema.__name__}")

    grafo = construir_grafo(Mock(generar=Mock(side_effect=_fallar_ambos)), checkpointer=InMemorySaver())
    res = grafo.invoke(
        {"analisis_id": "A-03", "texto_usuario": TEXTO_CORTO},
        config={"configurable": {"thread_id": "t-03"}},
    )
    errores_texto = " | ".join(res["errores"])
    assert "requisitos_funcionales" in errores_texto
    assert "requisitos_no_funcionales" in errores_texto


def test_req_05_grafo_pausa_tras_cuatro_subagentes_y_regenera_cus_si_analista_lo_pide() -> None:
    contadores: dict[str, int] = {}
    grafo = construir_grafo(_cliente_por_esquema(contadores), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t-05"}}
    pausado = grafo.invoke({"analisis_id": "A-05", "texto_usuario": TEXTO_CORTO}, config=cfg)
    assert pausado["estado"] == "PENDIENTE_APROBACION"
    assert "__interrupt__" in pausado

    tras_regen = grafo.invoke(
        Command(resume={"accion": "regenerar_cus", "rf_editados": [RF_EDIT]}),
        config=cfg,
    )
    assert tras_regen["estado"] == "PENDIENTE_APROBACION"
    assert tras_regen["casos_uso"] == [CUS_2]
    assert contadores["SalidaRF"] == 1
    assert contadores["SalidaCasosUso"] == 2

    final = grafo.invoke(
        Command(
            resume={
                "accion": "aprobar",
                "respuestas_clarificacion": {"0": "Máximo 3 libros"},
                "comentarios_analista": "Validado",
            }
        ),
        config=cfg,
    )
    assert final["estado"] == "APROBADO"
    assert contadores["SalidaCasosUso"] == 2


def test_req_06_grafo_permite_editar_y_responder_preguntas_en_pendiente_aprobacion() -> None:
    grafo = construir_grafo(_cliente_por_esquema(), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t-06"}}
    pausado = grafo.invoke({"analisis_id": "A-06", "texto_usuario": TEXTO_CORTO}, config=cfg)
    assert pausado["estado"] == "PENDIENTE_APROBACION"

    final = grafo.invoke(
        Command(
            resume={
                "accion": "aprobar",
                "rf_editados": [RF_EDIT],
                "respuestas_clarificacion": {"0": "Máximo 3 libros"},
                "comentarios_analista": "Aprobado con límite definido",
            }
        ),
        config=cfg,
    )
    assert final["requisitos_funcionales"] == [RF_EDIT]
    assert final["respuestas_clarificacion"] == {"0": "Máximo 3 libros"}
    assert final["inconsistencias"][0].respuesta_analista == "Máximo 3 libros"
    assert final["comentarios_analista"] == "Aprobado con límite definido"


def test_req_07_bloquea_reporte_sin_aprobacion_y_sella_estado_aprobado() -> None:
    grafo = construir_grafo(_cliente_por_esquema(), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t-07"}}
    pausado = grafo.invoke({"analisis_id": "A-07", "texto_usuario": TEXTO_CORTO}, config=cfg)
    with pytest.raises(ValueError, match="aprobación"):
        consolidar_reporte(
            analisis_id=pausado["analisis_id"],
            estado=pausado["estado"],
            requisitos_funcionales=pausado["requisitos_funcionales"],
            requisitos_no_funcionales=pausado["requisitos_no_funcionales"],
            inconsistencias=pausado["inconsistencias"],
            casos_uso=pausado["casos_uso"],
            respuestas_clarificacion={},
            comentarios_analista="",
        )

    final = grafo.invoke(Command(resume={"accion": "aprobar"}), config=cfg)
    assert final["estado"] == "APROBADO"
    assert final["reporte_consolidado"] is not None
    assert final["reporte_consolidado"].estado == "APROBADO"


def test_req_08_detiene_en_fallido_tras_reintentos_y_reanuda_sin_reejecutar_completados() -> None:
    llamadas = {"rf": 0, "rnf": 0}
    fallar_rnf = {"activo": True}

    def _rnf_intermitente(esquema: type, _instrucciones: str) -> object:
        if esquema is SalidaRF:
            llamadas["rf"] += 1
            return SalidaRF(requisitos=[RF_1])
        if esquema is SalidaRNF:
            llamadas["rnf"] += 1
            if fallar_rnf["activo"]:
                raise TimeoutError("cuota excedida")
            return SalidaRNF(requisitos=[RNF_1])
        if esquema is SalidaInconsistencias:
            return SalidaInconsistencias(inconsistencias=[INC_1])
        return SalidaCasosUso(casos_uso=[CUS_1])

    grafo = construir_grafo(Mock(generar=Mock(side_effect=_rnf_intermitente)), checkpointer=InMemorySaver())
    cfg = {"configurable": {"thread_id": "t-08"}}

    fallido = grafo.invoke({"analisis_id": "A-08", "texto_usuario": TEXTO_CORTO}, config=cfg)
    assert fallido["estado"] == "FALLIDO"
    assert llamadas["rf"] == 1
    assert llamadas["rnf"] == 3
    assert len(fallido["requisitos_funcionales"]) == 1

    fallar_rnf["activo"] = False
    reanudado = grafo.invoke({"analisis_id": "A-08", "texto_usuario": TEXTO_CORTO}, config=cfg)
    assert reanudado["estado"] == "PENDIENTE_APROBACION"
    assert llamadas["rf"] == 1
    assert any(t.nodo == "nodo_rf" and t.estado == "COMPLETADO" for t in reanudado["trazas"])
