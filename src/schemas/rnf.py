from pydantic import BaseModel, Field, ConfigDict


class RequisitoNoFuncional(BaseModel):
    """Requisito no funcional clasificado bajo ISO/IEC 25010.

    Contrato de salida del Subagente 2 (RNF).
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Identificador unico del requisito (e.g. RNF-01)")
    categoria_iso: str = Field(..., description="Una de las 8 categorias de ISO/IEC 25010")
    descripcion: str = Field(..., description="Descripcion del atributo de calidad")
    metrica_objetiva: str = Field(..., description="Metrica cuantificable y verificable")
    valor_umbral: str = Field(..., description="Valor umbral o criterio de aceptacion")
