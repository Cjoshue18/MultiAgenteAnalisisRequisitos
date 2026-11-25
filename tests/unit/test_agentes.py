from copy import deepcopy
from unittest.mock import Mock
import pytest
from pydantic import ValidationError
from src.agents.functional_agent import nodo_requisitos_funcionales
from src.agents.nonfunctional_agent import nodo_requisitos_no_funcionales
from src.agents.inconsistency_agent import nodo_inconsistencias
from src.agents.use_case_agent import nodo_casos_uso
from src.schemas.contracts import (RequisitoFuncional, RequisitoNoFuncional, SalidaRF,
                                   SalidaRNF, SalidaInconsistencias, SalidaCasosUso,
                                   Inconsistencia, CasoUso)

TEXTO = "El alumno debe consultar libros disponibles desde el catálogo de biblioteca."
RF = RequisitoFuncional(id="RF-01", nombre="Consultar catálogo", descripcion="El sistema debe permitir consultar libros disponibles.", actores=["Alumno"], referencia_texto="El alumno debe consultar libros disponibles")
RNF = RequisitoNoFuncional(id="RNF-01", categoria_iso="Rendimiento", descripcion="Las consultas deben responder en menos de 2 segundos", metrica_objetiva="Tiempo en segundos", valor_umbral="2 s")
INC = Inconsistencia(tipo="vacío", severidad="Media", descripcion="No se especifica el límite de préstamos", pregunta_clarificacion="¿Cuántos libros puede prestar un alumno?")
CUS = CasoUso(id="CUS-01", nombre="Consultar catálogo", actor_principal="Alumno", precondiciones=["Acceder al catálogo"], flujo_principal=["1. El alumno ingresa la búsqueda", "2. El sistema muestra resultados"], flujos_alternativos=["Sin coincidencias: mostrar aviso"], postcondiciones=["Consulta mostrada"], rf_relacionados=["RF-01"])

def cliente_mock(salida: object) -> Mock:
    return Mock(generar=Mock(return_value=salida))

def test_rf_extrae_salida_estructurada_sin_mutar_estado() -> None:
    estado = {"texto_usuario": TEXTO}
    antes = deepcopy(estado)
    delta = nodo_requisitos_funcionales(estado, cliente_mock(SalidaRF(requisitos=[RF])))
    assert delta == {"requisitos_funcionales": [RF]}
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

def test_cus_requiere_aprobacion() -> None:
    cliente = cliente_mock(SalidaCasosUso(casos_uso=[CUS]))
    delta = nodo_casos_uso({"texto_usuario": TEXTO, "requisitos_funcionales": [RF]}, cliente)
    assert "errores" in delta
    cliente.generar.assert_not_called()

def test_cus_con_rf_aprobados() -> None:
    delta = nodo_casos_uso({"rf_aprobados": [RF]}, cliente_mock(SalidaCasosUso(casos_uso=[CUS])))
    assert delta["casos_uso"] == [CUS]

def test_entrada_vacia_no_invoca_llm() -> None:
    cliente = cliente_mock(SalidaRF(requisitos=[]))
    assert "errores" in nodo_requisitos_funcionales({"texto_usuario": " "}, cliente)
    cliente.generar.assert_not_called()

def test_fallo_externo_es_registrado() -> None:
    cliente = Mock()
    cliente.generar.side_effect = TimeoutError("sin respuesta")
    delta = nodo_requisitos_funcionales({"texto_usuario": TEXTO}, cliente)
    assert "errores" in delta and "TimeoutError" in delta["errores"][0]

def test_salida_invalida_es_registrada() -> None:
    delta = nodo_requisitos_no_funcionales({"texto_usuario": TEXTO}, cliente_mock({"requisitos": [{"id": "RNF-01", "categoria_iso": "Inventada"}]}))
    assert "errores" in delta

def test_codigo_invalido_rechazado() -> None:
    with pytest.raises(ValidationError):
        RequisitoFuncional(id="X", nombre="Consultar catálogo", descripcion="El sistema debe permitir consultar libros.", actores=["Alumno"], referencia_texto="El alumno debe consultar")

def test_pasos_no_numerados_rechazados() -> None:
    with pytest.raises(ValidationError):
        CasoUso(id="CUS-01", nombre="Consultar catálogo", actor_principal="Alumno", precondiciones=[], flujo_principal=["Paso sin numerar"], flujos_alternativos=[], postcondiciones=[])
