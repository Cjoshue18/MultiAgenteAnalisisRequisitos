from pydantic import BaseModel, Field, ConfigDict
from typing import List


class RequisitoFuncional(BaseModel):
    """Requisito funcional atomico extraido del texto original.

    Contrato de salida del Subagente 1 (RF).
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Identificador unico del requisito (e.g. RF-01)")
    nombre: str = Field(..., description="Titulo representativo del requisito")
    descripcion: str = Field(..., description="Redaccion atomica: 'El sistema debe...'")
    actores: List[str] = Field(default_factory=list, description="Lista de actores involucrados")
    referencia_texto: str = Field(..., description="Cita textual de la entrada que sustenta el requisito")
