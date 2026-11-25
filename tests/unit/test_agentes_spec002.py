from unittest.mock import Mock
from src.agents.use_case_agent import nodo_modelado
from src.schemas.contracts import (
    CasoUso,
    CriterioAceptacion,
    HistoriaUsuario,
    RequisitoFuncional,
    SalidaCasosUso,
    SalidaHU,
)

RF_1 = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)
RF_APROB = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo filtrado",
    descripcion="El sistema debe permitir filtrar libros disponibles por facultad.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
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
    quiero="buscar libros disponibles en línea",
    para_que="saber qué libros puedo prestar",
    criterios_aceptacion=[
        CriterioAceptacion(
            dado="que existen libros registrados",
            cuando="busco por título",
            entonces="veo la disponibilidad en pantalla",
        )
    ],
    rf_relacionados=["RF-01"],
)


def _cliente_dual() -> Mock:
    def _generar(esquema: type, _instrucciones: str) -> object:
        if esquema is SalidaCasosUso:
            return SalidaCasosUso(casos_uso=[CUS_1])
        if esquema is SalidaHU:
            return SalidaHU(historias_usuario=[HU_1])
        raise ValueError(f"Esquema inesperado: {esquema}")

    return Mock(generar=Mock(side_effect=_generar))


def test_req_02_modelado_cus_genera_solo_cus_y_cero_hu() -> None:
    delta = nodo_modelado({"modalidad_modelado": "CUS", "requisitos_funcionales": [RF_1]}, _cliente_dual())
    assert delta["casos_uso"] == [CUS_1]
    assert delta["historias_usuario"] == []


def test_req_02_modelado_hu_genera_solo_hu_y_cero_cus() -> None:
    delta = nodo_modelado({"modalidad_modelado": "HU", "requisitos_funcionales": [RF_1]}, _cliente_dual())
    assert delta["historias_usuario"] == [HU_1]
    assert delta["casos_uso"] == []


def test_req_02_modelado_ambos_genera_cus_y_hu() -> None:
    delta = nodo_modelado({"modalidad_modelado": "AMBOS", "requisitos_funcionales": [RF_1]}, _cliente_dual())
    assert delta["casos_uso"] == [CUS_1]
    assert delta["historias_usuario"] == [HU_1]


def test_req_03_y_req_04_modelado_prioriza_rf_aprobados_al_regenerar() -> None:
    cliente = _cliente_dual()
    delta = nodo_modelado(
        {"modalidad_modelado": "HU", "requisitos_funcionales": [RF_1], "rf_aprobados": [RF_APROB]},
        cliente,
    )
    assert delta["historias_usuario"] == [HU_1]
    assert "Consultar catálogo filtrado" in cliente.generar.call_args.args[1]
