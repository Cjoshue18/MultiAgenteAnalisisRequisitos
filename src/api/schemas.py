from pydantic import BaseModel, Field, field_validator
from src.schemas.contracts import ModalidadModelado


class CrearProyectoRequest(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto")
    descripcion: str = Field(default="", description="Descripción opcional")

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio:
            raise ValueError("El nombre del proyecto no puede estar vacío.")
        return limpio


class IniciarAnalisisTextoRequest(BaseModel):
    proyecto_id: str = Field(..., min_length=1, description="Identificador del proyecto")
    modalidad_modelado: ModalidadModelado = Field(..., description="CUS, HU o AMBOS")
    texto: str = Field(..., description="Descripción textual de requisitos")
