from typing import Literal
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ProveedorLLM = Literal["auto", "gemini", "groq", "nvidia"]

_CLAVE_POR_PROVEEDOR = {
    "gemini": ("gemini_api_key", "GEMINI_API_KEY"),
    "groq": ("groq_api_key", "GROQ_API_KEY"),
    "nvidia": ("nvidia_api_key", "NVIDIA_API_KEY"),
}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_provider: ProveedorLLM = "auto"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3-flash-preview"
    groq_api_key: SecretStr | None = None
    groq_model: str = "openai/gpt-oss-120b"
    nvidia_api_key: SecretStr | None = None
    nvidia_model: str = "nvidia/nemotron-3.5-bolt-e4b"
    llm_timeout_directa_s: int = 15
    llm_timeout_lotes_s: int = 30

    def obtener_secreto(self, proveedor: Literal["gemini", "groq", "nvidia"]) -> str | None:
        attr, _ = _CLAVE_POR_PROVEEDOR[proveedor]
        secreto: SecretStr | None = getattr(self, attr)
        if secreto is None:
            return None
        valor = secreto.get_secret_value().strip()
        return valor or None

    def validar_credenciales(self) -> None:
        if self.llm_provider == "auto":
            if not any(self.obtener_secreto(p) for p in ("gemini", "groq", "nvidia")):
                raise ValueError(
                    "Se requiere al menos una API key configurada (GEMINI_API_KEY, GROQ_API_KEY o NVIDIA_API_KEY)."
                )
            return
        if not self.obtener_secreto(self.llm_provider):
            _, nombre_env = _CLAVE_POR_PROVEEDOR[self.llm_provider]
            raise ValueError(f"Falta {nombre_env} en la configuración externa.")


def obtener_settings() -> Settings:
    return Settings()
