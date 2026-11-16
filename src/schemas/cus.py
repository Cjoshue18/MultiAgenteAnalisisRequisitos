from pydantic import BaseModel, Field, ConfigDict
from typing import List


class CasoUso(BaseModel):
    """Caso de uso formal derivado de los requisitos funcionales.

    Contrato de salida del Subagente 4 (CUS).
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Identificador unico del caso de uso (e.g. CUS-01)")
    nombre: str = Field(..., description="Nombre del caso de uso")
    actor_principal: str = Field(..., description="Actor detonador del caso de uso")
    precondiciones: List[str] = Field(default_factory=list, description="Precondiciones requeridas")
    flujo_principal: List[str] = Field(default_factory=list, description="Pasos numerados del flujo principal")
    flujos_alternativos: List[str] = Field(default_factory=list, description="Flujos alternativos ante errores")
    postcondiciones: List[str] = Field(default_factory=list, description="Postcondiciones del sistema")
