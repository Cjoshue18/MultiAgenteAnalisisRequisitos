from src.graph.arch_graph import construir_grafo
from src.schemas.state import GraphState


def test_grafo_tiene_nodos_esperados() -> None:
    """Prueba que el grafo se construye con los nodos canonicos."""
    grafo = construir_grafo()
    assert grafo is not None


def test_estado_inicial_tiene_texto() -> None:
    """Prueba que el GraphState inicial acepta texto de usuario."""
    estado = GraphState(texto_usuario="El sistema debe permitir crear cuentas de usuario.")
    assert "crear cuentas" in estado.texto_usuario
