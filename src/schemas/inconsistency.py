from pydantic import BaseModel, Field, ConfigDict


class Inconsistencia(BaseModel):
    """Hallazgo semantico detectado por el Subagente 3.

    Contrato de salida del Subagente 3 (Inconsistencias y Ambigüedades).
    """

    model_config = ConfigDict(frozen=True)

    tipo: str = Field(..., description="ambigüedad, contradicción o vacío")
    severidad: str = Field(..., description="Alta, Media o Baja")
    elementos_afectados: str = Field(..., description="Requisitos o elementos afectados")
    descripcion_problema: str = Field(..., description="Descripcion del problema detectado")
    pregunta_clarificacion: str = Field(..., description="Pregunta dirigida al analista para resolver la incertidumbre")
