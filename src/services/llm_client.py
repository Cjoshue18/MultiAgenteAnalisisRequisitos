from typing import Any, Type, TypeVar
from src.core.settings import settings
from src.core.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class LLMClient:
    """Cliente de Google Gemini con soporte para Structured Output.

    Obtiene la clave de API desde variables de entorno (.env) y nunca la
    escribe en el codigo fuente.
    """

    def __init__(self) -> None:
        api_key = settings.gemini_api_key
        if not api_key:
            raise ValueError("GEMINI_API_KEY no configurada en variables de entorno")
        # Importo perezoso para no fallar si el paquete no esta disponible en tests
        from google import genai  # type: ignore

        self._client = genai.Client(api_key=api_key)
        self._model = "gemini-1.5-flash"

    def with_structured_output(
        self, modelo_pydantic: Type[T]
    ) -> Any:
        """Devuelve una instancia configurada para salida estructurada.

        Wrapper que expone una interfaz compatible con LangGraph para forzar
        respuestas tipadas mediante Pydantic.
        """
        class StructuredLLM:
            def __init__(self, client: "LLMClient", model_type: Type[T]) -> None:
                self._client = client
                self._model_type = model_type

            def invoke(self, prompt: str) -> Any:
                try:
                    response = self._client._client.models.generate_content(
                        model=self._client._model,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": self._model_type,
                        },
                    )
                    parsed = response.parsed
                    if parsed is None:
                        # Fallback: intentar parsear texto como JSON del schema
                        import json
                        texto = response.text or "[]"
                        datos = json.loads(texto)
                        if isinstance(datos, list):
                            return [self._model_type(**item) for item in datos]
                        return [self._model_type(**datos)]
                    return parsed
                except Exception as exc:
                    logger.error("Error en llamada a LLM: %s", str(exc))
                    raise

        return StructuredLLM(self, modelo_pydantic)