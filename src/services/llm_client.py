from typing import Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class ClienteEstructurado(Protocol):
    def generar(self, esquema: type[T], instrucciones: str) -> T:
        """Devolver instancia validada por Pydantic sin exponer proveedor externo."""
        ...

class ClienteLangChain:
    """Adaptador opcional para LLM con método with_structured_output."""
    def __init__(self, modelo: object) -> None:
        self.modelo = modelo

    def generar(self, esquema: type[T], instrucciones: str) -> T:
        # El proveedor se inyecta; nunca se crea conexión en importación.
        salida = self.modelo.with_structured_output(esquema).invoke(instrucciones)  # type: ignore[attr-defined]
        return esquema.model_validate(salida)
