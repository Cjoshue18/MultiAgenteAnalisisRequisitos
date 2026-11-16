from unittest.mock import patch, MagicMock
from src.agents.functional_agent import nodo_requisitos_funcionales
from src.schemas.functional import RequisitoFuncional
from src.schemas.state import GraphState


def test_nodo_rf_retorna_esquema_valido(mocker) -> None:
    """Prueba unitaria con mock: cero llamadas a API real de Gemini."""
    mock_rf = [
        RequisitoFuncional(
            id="RF-01",
            nombre="Iniciar Sesion",
            descripcion="El sistema debe permitir autenticar usuarios.",
            actores=["Usuario"],
            referencia_texto="El usuario puede iniciar sesion.",
        )
    ]

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_rf

    with patch("src.agents.functional_agent.LLMClient", return_value=mock_llm):
        estado_inicial = GraphState(texto_usuario="El usuario puede iniciar sesion.")
        resultado = nodo_requisitos_funcionales(estado_inicial)

    assert "requisitos_funcionales" in resultado
    assert len(resultado["requisitos_funcionales"]) == 1
    assert resultado["requisitos_funcionales"][0].id == "RF-01"
    assert "errores" not in resultado or len(resultado.get("errores", [])) == 0


def test_nodo_rf_maneja_error_sin_crash(mocker) -> None:
    """Prueba resiliencia: si el LLM falla, el nodo captura la excepcion."""
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.side_effect = Exception("API fallo")

    with patch("src.agents.functional_agent.LLMClient", return_value=mock_llm):
        estado_inicial = GraphState(texto_usuario="Texto de prueba suficiente para validar el nodo.")
        resultado = nodo_requisitos_funcionales(estado_inicial)

    assert "errores" in resultado
    assert len(resultado["errores"]) > 0