from unittest.mock import patch, MagicMock
from src.agents.rnf_agent import nodo_requisitos_no_funcionales
from src.schemas.rnf import RequisitoNoFuncional
from src.schemas.state import GraphState


def test_nodo_rnf_clasifica_iso_25010(mocker) -> None:
    """Prueba unitaria con mock: clasificacion RNF bajo ISO 25010."""
    mock_rnf = [
        RequisitoNoFuncional(
            id="RNF-01",
            categoria_iso="Seguridad",
            descripcion="El acceso requiere autenticacion multifactor.",
            metrica_objetiva="Tiempo de autenticacion",
            valor_umbral="< 2s",
        )
    ]
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_rnf

    with patch("src.agents.rnf_agent.LLMClient", return_value=mock_llm):
        estado = GraphState(texto_usuario="El sistema debe ser seguro y rapido.")
        resultado = nodo_requisitos_no_funcionales(estado)

    assert "requisitos_no_funcionales" in resultado
    assert len(resultado["requisitos_no_funcionales"]) == 1
    assert resultado["requisitos_no_funcionales"][0].categoria_iso == "Seguridad"