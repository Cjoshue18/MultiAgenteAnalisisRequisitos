from typing import Any, Type, TypeVar, get_origin, get_args
from pydantic import BaseModel
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
        self._model = "gemini-3.8-flash"

    def _resolver_esquema(self, modelo_pydantic: Type[T]) -> Type[BaseModel]:
        """Si el tipo es una lista, crea un modelo contenedor para structured output."""
        origen = get_origin(modelo_pydantic)
        if origen is list:
            item_type = get_args(modelo_pydantic)[0]

            class ModeloContenedor(BaseModel):
                items: list[item_type]

            ModeloContenedor.__name__ = f"Lista{item_type.__name__}"
            return ModeloContenedor  # type: ignore
        return modelo_pydantic  # type: ignore

    def with_structured_output(
        self, modelo_pydantic: Type[T]
    ) -> Any:
        """Devuelve una instancia configurada para salida estructurada.

        Wrapper que expone una interfaz compatible con LangGraph para forzar
        respuestas tipadas mediante Pydantic.
        """
        schema_model = self._resolver_esquema(modelo_pydantic)
        es_lista = get_origin(modelo_pydantic) is list

        class StructuredLLM:
            def __init__(self, client: "LLMClient", model_type: Type[T]) -> None:
                self._google_client = client._client  # cliente de Google Gemini
                self._model_name = client._model      # nombre del modelo
                self._model_type = model_type
                self._es_lista = es_lista

            def invoke(self, prompt: str) -> Any:
                try:
                    response = self._google_client.models.generate_content(
                        model=self._model_name,
                        contents=prompt,
                        config={
                            "response_mime_type": "application/json",
                            "response_schema": schema_model,
                        },
                    )
                    parsed = response.parsed
                    if parsed is None:
                        # Fallback: intentar parsear texto como JSON del schema
                        import json
                        texto = response.text or "[]"
                        datos = json.loads(texto)
                        if self._es_lista:
                            if isinstance(datos, list):
                                return [self._model_type(**item) for item in datos]
                            return [self._model_type(**datos)]
                        return [self._model_type(**datos)]

                    if self._es_lista:
                        return list(parsed.items) if hasattr(parsed, "items") else []
                    return parsed if isinstance(parsed, list) else [parsed]
                except Exception as exc:
                    logger.error("Error en llamada a LLM: %s", str(exc))
                    raise

        return StructuredLLM(self, modelo_pydantic)