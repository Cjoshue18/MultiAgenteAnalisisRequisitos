from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
import inspect
import logging
from typing import Protocol, TypeVar
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from src.core.config import Settings

logger = logging.getLogger(__name__)
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
T = TypeVar("T", bound=BaseModel)


class ClienteEstructurado(Protocol):
    def generar(self, esquema: type[T], instrucciones: str) -> T:
        """Devolver instancia validada por Pydantic sin exponer proveedor externo."""
        ...


def invocar_cliente_estructurado(
    cliente: object,
    esquema: type[T],
    instrucciones: str,
    timeout_s: float | None = None,
) -> T:
    """Invoca generar() pasando timeout_s solo si el adaptador lo declara explícitamente."""
    generar_fn = getattr(cliente, "generar")
    try:
        params = inspect.signature(generar_fn).parameters
    except (TypeError, ValueError):
        params = {}
    if timeout_s is not None and "timeout_s" in params:
        return generar_fn(esquema, instrucciones, timeout_s=timeout_s)
    return generar_fn(esquema, instrucciones)


class ClienteLangChain:
    """Adaptador para LLM con with_structured_output y control de timeout por llamada."""

    def __init__(self, modelo: object) -> None:
        self.modelo = modelo

    def generar(self, esquema: type[T], instrucciones: str, timeout_s: float | None = None) -> T:
        runnable = self.modelo.with_structured_output(esquema)  # type: ignore[attr-defined]
        if timeout_s is None:
            salida = runnable.invoke(instrucciones)
            return esquema.model_validate(salida)

        executor = ThreadPoolExecutor(max_workers=1)
        futuro = executor.submit(runnable.invoke, instrucciones)
        try:
            salida = futuro.result(timeout=timeout_s)
        except FutureTimeoutError as exc:
            futuro.cancel()
            executor.shutdown(wait=False, cancel_futures=True)
            raise TimeoutError(f"La llamada al proveedor excedió el límite de {timeout_s}s") from exc
        executor.shutdown(wait=False)
        return esquema.model_validate(salida)


class ClienteConFallback:
    """Decorador hexagonal que conmuta automáticamente entre proveedores ante fallos."""

    def __init__(self, proveedores: Sequence[tuple[str, ClienteEstructurado]]) -> None:
        if not proveedores:
            raise ValueError("Se requiere al menos un proveedor para ClienteConFallback.")
        self.proveedores = list(proveedores)
        self.eventos_fallback: list[str] = []

    def generar(self, esquema: type[T], instrucciones: str, timeout_s: float | None = None) -> T:
        errores: list[str] = []
        fallidos: list[str] = []
        for idx, (nombre, cliente) in enumerate(self.proveedores):
            try:
                resultado = invocar_cliente_estructurado(cliente, esquema, instrucciones, timeout_s=timeout_s)
                salida = esquema.model_validate(resultado)
                if idx > 0 and fallidos:
                    evento = f"Fallback de {', '.join(fallidos)} hacia {nombre}"
                    self.eventos_fallback.append(evento)
                    logger.warning(evento)
                return salida
            except Exception as exc:
                fallidos.append(nombre)
                errores.append(f"{nombre}: {type(exc).__name__}: {exc}")
                logger.warning("Proveedor %s falló: %s", nombre, exc)
        raise RuntimeError("Fallaron todos los proveedores LLM: " + " | ".join(errores))


def _construir_adaptador(nombre: str, settings: Settings) -> ClienteLangChain:
    timeout_defecto = float(settings.llm_timeout_lotes_s)
    if nombre == "gemini":
        clave = settings.obtener_secreto("gemini")
        return ClienteLangChain(
            ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=clave, timeout=timeout_defecto)
        )
    if nombre == "groq":
        clave = settings.obtener_secreto("groq")
        return ClienteLangChain(
            ChatGroq(model=settings.groq_model, api_key=clave, timeout=timeout_defecto)
        )
    if nombre == "nvidia":
        clave = settings.obtener_secreto("nvidia")
        return ClienteLangChain(
            ChatOpenAI(
                model=settings.nvidia_model,
                api_key=clave,
                base_url=NVIDIA_BASE_URL,
                timeout=timeout_defecto,
            )
        )
    raise ValueError(f"Proveedor LLM no soportado: {nombre}")


def crear_cliente_llm(settings: Settings) -> ClienteEstructurado:
    """Fábrica hexagonal: construye proveedor único o cadena con Fallback según Settings."""
    settings.validar_credenciales()
    if settings.llm_provider != "auto":
        return _construir_adaptador(settings.llm_provider, settings)

    cadena: list[tuple[str, ClienteEstructurado]] = [
        (nombre, _construir_adaptador(nombre, settings))
        for nombre in ("gemini", "groq", "nvidia")
        if settings.obtener_secreto(nombre)  # type: ignore[arg-type]
    ]
    if len(cadena) == 1:
        return cadena[0][1]
    return ClienteConFallback(cadena)
