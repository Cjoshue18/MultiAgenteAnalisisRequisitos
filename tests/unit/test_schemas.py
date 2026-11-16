from src.schemas.functional import RequisitoFuncional
from src.schemas.rnf import RequisitoNoFuncional
from src.schemas.cus import CasoUso
from src.schemas.inconsistency import Inconsistencia
from src.schemas.state import GraphState


def test_requisito_funcional_es_valido() -> None:
    rf = RequisitoFuncional(
        id="RF-01",
        nombre="Iniciar sesion",
        descripcion="El sistema debe permitir autenticar usuarios.",
        actores=["Usuario"],
        referencia_texto="El usuario puede iniciar sesión.",
    )
    assert rf.id == "RF-01"
    assert rf.actores == ["Usuario"]
    assert "autenticar" in rf.descripcion


def test_requisito_no_funcional_tiene_categoria_iso() -> None:
    rnf = RequisitoNoFuncional(
        id="RNF-01",
        categoria_iso="Seguridad",
        descripcion="El acceso requiere MFA.",
        metrica_objetiva="Tiempo de autenticacion",
        valor_umbral="< 2s",
    )
    assert rnf.categoria_iso == "Seguridad"


def test_caso_uso_tiene_flujo_principal() -> None:
    cus = CasoUso(
        id="CUS-01",
        nombre="Iniciar sesion",
        actor_principal="Usuario",
        precondiciones=["Usuario registrado"],
        flujo_principal=["1. Ingresar credenciales", "2. Validar", "3. Conceder acceso"],
        flujos_alternativos=["2a. Error de credenciales"],
        postcondiciones=["Sesion iniciada"],
    )
    assert len(cus.flujo_principal) == 3


def test_inconsistencia_tiene_severidad_valida() -> None:
    inc = Inconsistencia(
        tipo="ambigüedad",
        severidad="Media",
        elementos_afectados="RF-01",
        descripcion_problema="Termino vago",
        pregunta_clarificacion="¿Cual es el umbral?",
    )
    assert inc.severidad in ("Alta", "Media", "Baja")


def test_graph_state_inicial_vacio() -> None:
    estado = GraphState(texto_usuario="Prueba de texto suficiente para validar.")
    assert estado.texto_usuario == "Prueba de texto suficiente para validar."
    assert estado.requisitos_funcionales == []
    assert estado.errores == []
