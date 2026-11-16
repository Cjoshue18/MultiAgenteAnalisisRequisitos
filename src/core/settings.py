from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Configuracion de la aplicacion leída desde variables de entorno (.env).

    Las credenciales de API NUNCA se escriben en el codigo fuente.
    """

    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None

    database_url: str = "sqlite:///./analisis.db"

    app_env: str = "development"
    log_level: str = "DEBUG"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
