from unittest.mock import patch, MagicMock
from src.agents.cus_agent import nodo_casos_de_uso
from src.schemas.cus import CasoUso
from src.schemas.state import GraphState
from src.schemas.functional import RequisitoFuncional


def test_nodo_cus_genera_casos_de_uso(mocker) -> None:
    """Prueba unitaria con mock: generacion de casos de uso formales."""
    mock_cus = [
        CasoUso(
            id="CUS-01",
            nombre="Iniciar sesion",
            actor_principal="Usuario",
            precondiciones=["Usuario registrado"],
            flujo_principal=["1. Ingresar credenciales", "2. Validar", "3. Conceder acceso"],
            flujos_alternativos=["2a. Credenciales invalidas"],
            postcondiciones=["Sesion iniciada"],
        )
    ]
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_cus

    with patch("src.agents.cus_agent.LLMClient", return_value=mock_llm):
        estado = GraphState(
            texto_usuario="Texto de prueba para casos de uso.",
            requisitos_funcionales=[
                RequisitoFuncional(
                    id="RF-01",
                    nombre="Autenticarse",
                    descripcion="El sistema debe permitir autenticarse.",
                    actores=["Usuario"],
                    referencia_texto="El usuario puede iniciar sesion.",
                )
            ]
        )
        resultado = nodo_casos_de_uso(estado)

    assert "casos_de_uso" in resultado
    assert len(resultado["casos_de_uso"]) == 1
    assert resultado["casos_de_uso"][0].id == "CUS-01"