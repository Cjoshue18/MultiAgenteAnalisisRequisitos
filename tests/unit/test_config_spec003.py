from pathlib import Path
import pytest
from src.core.config import Settings


def _limpiar_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "LLM_PROVIDER",
        "GEMINI_API_KEY",
        "GROQ_API_KEY",
        "NVIDIA_API_KEY",
        "LLM_TIMEOUT_DIRECTA_S",
        "LLM_TIMEOUT_LOTES_S",
    ):
        monkeypatch.delenv(var, raising=False)


def test_req_01_settings_carga_valores_desde_env_y_oculta_secretos(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _limpiar_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "LLM_PROVIDER=groq\nGEMINI_API_KEY=secret-gem-123\nGROQ_API_KEY=secret-groq-456\n",
        encoding="utf-8",
    )
    cfg = Settings(_env_file=env_file)
    assert cfg.llm_provider == "groq"
    assert cfg.gemini_api_key is not None
    assert cfg.gemini_api_key.get_secret_value() == "secret-gem-123"
    assert "secret-gem-123" not in repr(cfg)
    assert "secret-groq-456" not in str(cfg)


def test_req_01_rechaza_inicializacion_sin_credenciales_para_proveedor_elegido(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _limpiar_env(monkeypatch)
    cfg_groq = Settings(_env_file=None, llm_provider="groq", groq_api_key=None)
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        cfg_groq.validar_credenciales()

    cfg_auto = Settings(_env_file=None, llm_provider="auto", gemini_api_key=None, groq_api_key=None, nvidia_api_key=None)
    with pytest.raises(ValueError, match="API key"):
        cfg_auto.validar_credenciales()


def test_req_04_settings_define_timeouts_15_directa_y_30_lotes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _limpiar_env(monkeypatch)
    cfg = Settings(_env_file=None)
    assert cfg.llm_timeout_directa_s == 15
    assert cfg.llm_timeout_lotes_s == 30
