from copy import deepcopy
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from src.agents.functional_agent import nodo_requisitos_funcionales
from src.agents.inconsistency_agent import nodo_inconsistencias
from src.agents.nonfunctional_agent import nodo_requisitos_no_funcionales
from src.agents.use_case_agent import nodo_casos_uso
from src.schemas.contracts import (
    CasoUso,
    Inconsistencia,
    RequisitoFuncional,
    RequisitoNoFuncional,
    SalidaCasosUso,
    SalidaInconsistencias,
    SalidaRF,
    SalidaRNF,
)

TEXTO = "El alumno debe consultar libros disponibles desde el catálogo de biblioteca."
RF = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="El alumno debe consultar libros disponibles",
)
RF_EDITADO = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo avanzado",
    descripcion="El sistema debe filtrar libros disponibles por facultad.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)
RNF = RequisitoNoFuncional(
    id="RNF-01",
    categoria_iso="Rendimiento",
    descripcion="Las consultas deben responder en menos de 2 segundos",
    metrica_objetiva="Tiempo en segundos",
    valor_umbral="2 s",
)
INC = Inconsistencia(
    tipo="vacío",
    severidad="Media",
    descripcion="No se especifica el límite de préstamos",
    pregunta_clarificacion="¿Cuántos libros puede prestar un alumno?",
)
CUS = CasoUso(
    id="CUS-01",
    nombre="Consultar catálogo",
    actor_principal="Alumno",
    precondiciones=["Acceder al catálogo"],
    flujo_principal=["1. El alumno ingresa la búsqueda", "2. El sistema muestra resultados"],
    flujos_alternativos=["Sin coincidencias: mostrar aviso"],
    postcondiciones=["Consulta mostrada"],
    rf_relacionados=["RF-01"],
)


def cliente_mock(salida: object) -> Mock:
    return Mock(generar=Mock(return_value=salida))


def test_rf_extrae_salida_estructurada_sin_mutar_estado() -> None:
    estado = {"texto_usuario": TEXTO}
    antes = deepcopy(estado)
    delta = nodo_requisitos_funcionales(estado, cliente_mock(SalidaRF(requisitos=[RF])))
    assert delta["requisitos_funcionales"] == [RF]
    assert estado == antes


def test_rnf_valida_categoria_y_metrica() -> None:
    delta = nodo_requisitos_no_funcionales({"texto_usuario": TEXTO}, cliente_mock(SalidaRNF(requisitos=[RNF])))
    assert delta["requisitos_no_funcionales"][0].categoria_iso == "Rendimiento"


def test_inconsistencias_usa_rf_y_rnf() -> None:
    cliente = cliente_mock(SalidaInconsistencias(inconsistencias=[INC]))
    estado = {"texto_usuario": TEXTO, "requisitos_funcionales": [RF], "requisitos_no_funcionales": [RNF]}
    delta = nodo_inconsistencias(estado, cliente)
    assert delta["inconsistencias"] == [INC]
    assert "RF-01" in cliente.generar.call_args.args[1]


def test_req_05_cus_requiere_al_menos_un_rf() -> None:
    cliente = cliente_mock(SalidaCasosUso(casos_uso=[CUS]))
    delta = nodo_casos_uso({"texto_usuario": TEXTO, "requisitos_funcionales": []}, cliente)
    assert "errores" in delta
    cliente.generar.assert_not_called()


def test_req_05_cus_genera_preliminar_sin_rf_aprobados_y_prioriza_rf_aprobados() -> None:
    delta_prelim = nodo_casos_uso(
        {"texto_usuario": TEXTO, "requisitos_funcionales": [RF]},
        cliente_mock(SalidaCasosUso(casos_uso=[CUS])),
    )
    assert delta_prelim["casos_uso"] == [CUS]

    cliente_regen = cliente_mock(SalidaCasosUso(casos_uso=[CUS]))
    delta_regen = nodo_casos_uso(
        {"requisitos_funcionales": [RF], "rf_aprobados": [RF_EDITADO]},
        cliente_regen,
    )
    assert delta_regen["casos_uso"] == [CUS]
    assert "Consultar catálogo avanzado" in cliente_regen.generar.call_args.args[1]


def test_entrada_vacia_no_invoca_llm() -> None:
    cliente = cliente_mock(SalidaRF(requisitos=[]))
    assert "errores" in nodo_requisitos_funcionales({"texto_usuario": " "}, cliente)
    cliente.generar.assert_not_called()


def test_req_01_comprobar_texto_maneja_none_sin_crashear() -> None:
    cliente = cliente_mock(SalidaRF(requisitos=[]))
    delta = nodo_requisitos_funcionales({"texto_usuario": None}, cliente)  # type: ignore[typeddict-item]
    assert "errores" in delta
    cliente.generar.assert_not_called()


def test_req_02_rf_y_rnf_consolidan_multiples_lotes_sin_duplicados() -> None:
    rf_lote2 = RequisitoFuncional(
        id="RF-01",
        nombre="Registrar préstamo",
        descripcion="El sistema debe registrar préstamos de libros.",
        actores=["Alumno"],
        referencia_texto="realizar préstamos",
    )
    cliente_rf = Mock()
    cliente_rf.generar.side_effect = [
        SalidaRF(requisitos=[RF]),
        SalidaRF(requisitos=[RF, rf_lote2]),
    ]
    delta_rf = nodo_requisitos_funcionales({"texto_usuario": TEXTO, "fragmentos": ["Lote 1", "Lote 2"]}, cliente_rf)
    assert cliente_rf.generar.call_count == 2
    assert [r.id for r in delta_rf["requisitos_funcionales"]] == ["RF-01", "RF-02"]

    rnf_lote2 = RequisitoNoFuncional(
        id="RNF-01",
        categoria_iso="Seguridad",
        descripcion="El acceso administrativo debe exigir MFA.",
        metrica_objetiva="Autenticación multifactor",
        valor_umbral="100%",
    )
    cliente_rnf = Mock()
    cliente_rnf.generar.side_effect = [
        SalidaRNF(requisitos=[RNF]),
        SalidaRNF(requisitos=[RNF, rnf_lote2]),
    ]
    delta_rnf = nodo_requisitos_no_funcionales({"texto_usuario": TEXTO, "fragmentos": ["Lote 1", "Lote 2"]}, cliente_rnf)
    assert cliente_rnf.generar.call_count == 2
    assert [r.id for r in delta_rnf["requisitos_no_funcionales"]] == ["RNF-01", "RNF-02"]


def test_req_04_inconsistencias_soporta_dicts_de_checkpoint() -> None:
    cliente = cliente_mock(SalidaInconsistencias(inconsistencias=[INC]))
    estado = {
        "texto_usuario": TEXTO,
        "requisitos_funcionales": [RF.model_dump()],
        "requisitos_no_funcionales": [RNF.model_dump()],
    }
    delta = nodo_inconsistencias(estado, cliente)  # type: ignore[arg-type]
    assert delta["inconsistencias"] == [INC]


def test_fallo_externo_es_registrado() -> None:
    cliente = Mock()
    cliente.generar.side_effect = TimeoutError("sin respuesta")
    delta = nodo_requisitos_funcionales({"texto_usuario": TEXTO}, cliente)
    assert "errores" in delta and "TimeoutError" in delta["errores"][0]


def test_req_08_reintenta_hasta_dos_veces_antes_de_registrar_fallo() -> None:
    cliente_ok = Mock()
    cliente_ok.generar.side_effect = [TimeoutError("1"), TimeoutError("2"), SalidaRF(requisitos=[RF])]
    delta_ok = nodo_requisitos_funcionales({"texto_usuario": TEXTO}, cliente_ok)
    assert cliente_ok.generar.call_count == 3
    assert delta_ok["requisitos_funcionales"] == [RF]

    cliente_fail = Mock()
    cliente_fail.generar.side_effect = TimeoutError("persistente")
    delta_fail = nodo_requisitos_funcionales({"texto_usuario": TEXTO}, cliente_fail)
    assert cliente_fail.generar.call_count == 3
    assert "errores" in delta_fail
    assert delta_fail["trazas"][-1].estado == "FALLIDO"


def test_salida_invalida_es_registrada() -> None:
    delta = nodo_requisitos_no_funcionales(
        {"texto_usuario": TEXTO},
        cliente_mock({"requisitos": [{"id": "RNF-01", "categoria_iso": "Inventada"}]}),
    )
    assert "errores" in delta


def test_codigo_invalido_rechazado() -> None:
    with pytest.raises(ValidationError):
        RequisitoFuncional(
            id="X",
            nombre="Consultar catálogo",
            descripcion="El sistema debe permitir consultar libros.",
            actores=["Alumno"],
            referencia_texto="El alumno debe consultar",
        )


def test_pasos_no_numerados_rechazados() -> None:
    with pytest.raises(ValidationError):
        CasoUso(
            id="CUS-01",
            nombre="Consultar catálogo",
            actor_principal="Alumno",
            precondiciones=[],
            flujo_principal=["Paso sin numerar"],
            flujos_alternativos=[],
            postcondiciones=[],
        )
