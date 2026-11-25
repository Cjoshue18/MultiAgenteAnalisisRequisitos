import time
from unittest.mock import Mock
import pytest
from src.agents.functional_agent import nodo_requisitos_funcionales
from src.core.config import Settings
from src.schemas.contracts import RequisitoFuncional, SalidaRF
from src.services.llm_client import ClienteConFallback, ClienteLangChain, crear_cliente_llm

TEXTO = "El alumno debe consultar libros disponibles en el catálogo de la biblioteca."
RF = RequisitoFuncional(
    id="RF-01",
    nombre="Consultar catálogo",
    descripcion="El sistema debe permitir consultar libros disponibles.",
    actores=["Alumno"],
    referencia_texto="consultar libros disponibles",
)


def test_req_02_fabrica_alterna_proveedor_segun_configuracion(mocker, monkeypatch: pytest.MonkeyPatch) -> None:
    mock_gem = mocker.patch("src.services.llm_client.ChatGoogleGenerativeAI", return_value=Mock())
    mock_groq = mocker.patch("src.services.llm_client.ChatGroq", return_value=Mock())
    mock_nv = mocker.patch("src.services.llm_client.ChatOpenAI", return_value=Mock())

    cfg_groq = Settings(
        _env_file=None,
        llm_provider="groq",
        gemini_api_key="g-key",
        groq_api_key="q-key",
        nvidia_api_key="n-key",
    )
    cliente_groq = crear_cliente_llm(cfg_groq)
    assert isinstance(cliente_groq, ClienteLangChain)
    mock_groq.assert_called_once()
    mock_gem.assert_not_called()

    cfg_nv = Settings(_env_file=None, llm_provider="nvidia", nvidia_api_key="n-key")
    cliente_nv = crear_cliente_llm(cfg_nv)
    assert isinstance(cliente_nv, ClienteLangChain)
    mock_nv.assert_called_once()
    assert "nvidia" in str(mock_nv.call_args.kwargs.get("base_url", "")).lower()


def test_req_03_fallback_conmuta_de_primario_a_respaldo_ante_429_o_timeout() -> None:
    primario = Mock(generar=Mock(side_effect=RuntimeError("HTTP 429 quota exceeded")))
    respaldo = Mock(generar=Mock(return_value=SalidaRF(requisitos=[RF])))
    cliente = ClienteConFallback([("gemini", primario), ("groq", respaldo)])

    salida = cliente.generar(SalidaRF, "Extrae RF", timeout_s=15.0)
    assert salida.requisitos == [RF]
    assert len(cliente.eventos_fallback) == 1
    assert "gemini" in cliente.eventos_fallback[0] and "groq" in cliente.eventos_fallback[0]


def test_req_03_fallback_propaga_errores_de_todos_los_proveedores_si_todos_fallan() -> None:
    primario = Mock(generar=Mock(side_effect=TimeoutError("timeout gemini")))
    respaldo = Mock(generar=Mock(side_effect=RuntimeError("HTTP 503 groq")))
    cliente = ClienteConFallback([("gemini", primario), ("groq", respaldo)])

    with pytest.raises(RuntimeError) as exc_info:
        cliente.generar(SalidaRF, "Extrae RF")
    msg = str(exc_info.value)
    assert "gemini" in msg and "groq" in msg


def test_req_04_agentes_aplican_timeout_15s_en_directa_y_30s_en_lotes() -> None:
    registrados: list[float | None] = []

    class ClienteConTimeout:
        def generar(self, esquema: type, instrucciones: str, timeout_s: float | None = None) -> object:
            registrados.append(timeout_s)
            return SalidaRF(requisitos=[RF])

    nodo_requisitos_funcionales({"texto_usuario": TEXTO, "fragmentos": [TEXTO]}, ClienteConTimeout())
    nodo_requisitos_funcionales({"texto_usuario": TEXTO, "fragmentos": ["Lote 1", "Lote 2"]}, ClienteConTimeout())
    assert registrados == [15.0, 30.0, 30.0]


def test_req_04_cliente_aborta_llamada_que_supera_timeout_configurado() -> None:
    class RunnableLento:
        def invoke(self, _instrucciones: str) -> object:
            time.sleep(0.25)
            return SalidaRF(requisitos=[RF])

    modelo_lento = Mock(with_structured_output=Mock(return_value=RunnableLento()))
    cliente = ClienteLangChain(modelo_lento)
    with pytest.raises(TimeoutError, match="excedió"):
        cliente.generar(SalidaRF, "Extrae RF", timeout_s=0.05)
