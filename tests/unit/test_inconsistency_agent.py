from unittest.mock import patch, MagicMock
from src.agents.inconsistency_agent import nodo_inconsistencias
from src.schemas.inconsistency import Inconsistencia
from src.schemas.state import GraphState


def test_nodo_inconsistencias_detecta_hallazgos(mocker) -> None:
    """Prueba unitaria con mock: deteccion de inconsistencias."""
    mock_inc = [
        Inconsistencia(
            tipo="ambigüedad",
            severidad="Media",
            elementos_afectados="RF-01",
            descripcion_problema="Termino vago: rapido",
            pregunta_clarificacion="¿Cual es el umbral de tiempo?",
        )
    ]
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value.invoke.return_value = mock_inc

    with patch("src.agents.inconsistency_agent.LLMClient", return_value=mock_llm):
        estado = GraphState(
            texto_usuario="El sistema debe responder rapido.",
            requisitos_funcionales=[],
            requisitos_no_funcionales=[],
        )
        resultado = nodo_inconsistencias(estado)

    assert "inconsistencias" in resultado
    assert len(resultado["inconsistencias"]) == 1
    assert resultado["inconsistencias"][0].severidad == "Media"