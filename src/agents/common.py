import logging
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from typing import Any, TypeVar
from pydantic import BaseModel
from src.schemas.contracts import TrazaEjecucion
from src.schemas.state import GraphState
from src.services.llm_client import ClienteEstructurado

logger = logging.getLogger(__name__)
MAX_REINTENTOS = 2
T = TypeVar("T", bound=BaseModel)


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def comprobar_texto(state: GraphState) -> str:
    texto = (state.get("texto_usuario") or "").strip()
    if len(texto) < 20:
        raise ValueError("La descripción debe contener al menos 20 caracteres")
    return texto


def serializar_elementos(elementos: Sequence[BaseModel | dict[str, Any]]) -> list[dict[str, Any]]:
    """Convierte modelos Pydantic o diccionarios de checkpoint a dict plano."""
    return [e.model_dump() if isinstance(e, BaseModel) else dict(e) for e in elementos]


def _ejecutar_con_reintentos(
    cliente: ClienteEstructurado,
    esquema: type[T],
    instrucciones: str,
    nodo: str,
    max_reintentos: int = MAX_REINTENTOS,
) -> tuple[T | None, list[TrazaEjecucion], Exception | None]:
    trazas: list[TrazaEjecucion] = []
    ultimo_error: Exception | None = None
    for intento in range(max_reintentos + 1):
        inicio = _ahora_iso()
        try:
            resultado = cliente.generar(esquema, instrucciones)
            salida = esquema.model_validate(resultado)
            trazas.append(
                TrazaEjecucion(nodo=nodo, estado="COMPLETADO", inicio_iso=inicio, fin_iso=_ahora_iso(), detalle="OK")
            )
            return salida, trazas, None
        except Exception as exc:
            ultimo_error = exc
            estado_traza = "REINTENTO" if intento < max_reintentos else "FALLIDO"
            logger.warning("Fallo intento %d en %s: %s", intento + 1, nodo, exc)
            trazas.append(
                TrazaEjecucion(
                    nodo=nodo,
                    estado=estado_traza,
                    inicio_iso=inicio,
                    fin_iso=_ahora_iso(),
                    detalle=f"{type(exc).__name__}: {exc}",
                )
            )
    return None, trazas, ultimo_error


def ejecutar_agente(
    cliente: ClienteEstructurado,
    esquema: type[T],
    instrucciones: str,
    clave: str,
    atributo: str,
    nodo: str | None = None,
) -> dict[str, object]:
    nombre_nodo = nodo or clave
    salida, trazas, exc = _ejecutar_con_reintentos(cliente, esquema, instrucciones, nombre_nodo)
    if exc is not None or salida is None:
        return {"errores": [f"{clave}: {type(exc).__name__}: {exc}"], "trazas": trazas}
    return {clave: getattr(salida, atributo), "trazas": trazas}


def extraer_por_lotes(
    state: GraphState,
    cliente: ClienteEstructurado,
    esquema: type[T],
    atributo: str,
    clave: str,
    prefijo: str,
    constructor_instrucciones: Callable[[str], str],
    clave_dedup: Callable[[Any], tuple[str, ...]],
    nodo: str,
) -> dict[str, object]:
    """Ejecuta extracción en pasada directa o por lotes consolidando sin duplicados."""
    try:
        texto = comprobar_texto(state)
    except ValueError as exc:
        return {"errores": [str(exc)]}

    fragmentos = state.get("fragmentos") or [texto]
    if len(fragmentos) == 1:
        return ejecutar_agente(cliente, esquema, constructor_instrucciones(fragmentos[0]), clave, atributo, nodo=nodo)

    acumulados: list[Any] = []
    vistas: set[tuple[str, ...]] = set()
    trazas_totales: list[TrazaEjecucion] = []
    for lote in fragmentos:
        salida, trazas, exc = _ejecutar_con_reintentos(cliente, esquema, constructor_instrucciones(lote), nodo)
        trazas_totales.extend(trazas)
        if exc is not None or salida is None:
            return {"errores": [f"{clave}: {type(exc).__name__}: {exc}"], "trazas": trazas_totales}
        for item in getattr(salida, atributo):
            huella = clave_dedup(item)
            if huella not in vistas:
                vistas.add(huella)
                acumulados.append(item.model_copy(update={"id": f"{prefijo}-{len(acumulados) + 1:02d}"}))
    return {clave: acumulados, "trazas": trazas_totales}
