import pytest
from src.schemas.state import GraphState


@pytest.fixture
def estado_valido() -> GraphState:
    return GraphState(
        texto_usuario="El sistema debe permitir al usuario iniciar sesion con correo y contrasena."
    )


@pytest.fixture
def estado_vacio() -> GraphState:
    return GraphState(texto_usuario="")
