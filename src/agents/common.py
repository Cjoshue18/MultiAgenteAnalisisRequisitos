import logging
from pydantic import BaseModel
from src.schemas.state import GraphState
from src.services.llm_client import ClienteEstructurado

logger = logging.getLogger(__name__)

def ejecutar_agente(state: GraphState, cliente: ClienteEstructurado, esquema: type[BaseModel],
                    instrucciones: str, clave: str, atributo: str) -> dict[str, object]:
    try:
        resultado = cliente.generar(esquema, instrucciones)
        salida = esquema.model_validate(resultado)
        return {clave: getattr(salida, atributo)}
    except Exception as exc:
        logger.warning("Falló el agente %s: %s", clave, exc)
        return {"errores": [f"{clave}: {type(exc).__name__}: {exc}"]}

def comprobar_texto(state: GraphState) -> str:
    texto = state.get("texto_usuario", "").strip()
    if len(texto) < 20:
        raise ValueError("La descripción debe contener al menos 20 caracteres")
    return texto
