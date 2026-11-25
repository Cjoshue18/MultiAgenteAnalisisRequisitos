from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

CategoriaISO = Literal["Rendimiento", "Seguridad", "Fiabilidad", "Usabilidad", "Compatibilidad", "Mantenibilidad", "Escalabilidad", "Portabilidad"]

class ContratoBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

class RequisitoFuncional(ContratoBase):
    id: str = Field(..., pattern=r"^RF-\d{2,}$", description="Código correlativo RF-01")
    nombre: str = Field(..., min_length=3, description="Título del requisito")
    descripcion: str = Field(..., min_length=10, description="Funcionalidad única verificable")
    actores: list[str] = Field(..., min_length=1, description="Actores involucrados")
    referencia_texto: str = Field(..., min_length=3, description="Cita exacta del documento original")

class RequisitoNoFuncional(ContratoBase):
    id: str = Field(..., pattern=r"^RNF-\d{2,}$", description="Código correlativo RNF-01")
    categoria_iso: CategoriaISO = Field(..., description="Atributo ISO/IEC 25010 establecido para el proyecto")
    descripcion: str = Field(..., min_length=10, description="Restricción de calidad")
    metrica_objetiva: str = Field(..., min_length=3, description="Nombre y unidad de medida")
    valor_umbral: str = Field(..., min_length=1, description="Valor objetivo; si es propuesto debe indicarse")

class Inconsistencia(ContratoBase):
    tipo: Literal["ambigüedad", "contradicción", "vacío"] = Field(..., description="Tipo de hallazgo")
    severidad: Literal["Alta", "Media", "Baja"] = Field(..., description="Prioridad del problema")
    descripcion: str = Field(..., min_length=8, description="Descripción de la evidencia del problema")
    pregunta_clarificacion: str = Field(..., min_length=5, description="Pregunta concreta al analista")
    elementos_afectados: list[str] = Field(default_factory=list, description="Identificadores relacionados")

class CasoUso(ContratoBase):
    id: str = Field(..., pattern=r"^CUS-\d{2,}$", description="Código correlativo CUS-01")
    nombre: str = Field(..., min_length=3, description="Nombre en infinitivo")
    actor_principal: str = Field(..., min_length=2, description="Actor que dispara el caso")
    precondiciones: list[str] = Field(..., description="Condiciones previas")
    flujo_principal: list[str] = Field(..., min_length=1, description="Pasos numerados del flujo feliz")
    flujos_alternativos: list[str] = Field(..., description="Excepciones y alternativas")
    postcondiciones: list[str] = Field(..., description="Estado resultante")
    rf_relacionados: list[str] = Field(default_factory=list, description="RF que originan el caso")

    @field_validator("flujo_principal")
    @classmethod
    def verificar_pasos(cls, pasos: list[str]) -> list[str]:
        for i, paso in enumerate(pasos, 1):
            if not paso.startswith(f"{i}."):
                raise ValueError("El flujo principal requiere pasos correlativos: 1., 2., ...")
        return pasos

class SalidaRF(ContratoBase):
    requisitos: list[RequisitoFuncional] = Field(..., description="Requisitos funcionales encontrados")
class SalidaRNF(ContratoBase):
    requisitos: list[RequisitoNoFuncional] = Field(..., description="Requisitos no funcionales encontrados")
class SalidaInconsistencias(ContratoBase):
    inconsistencias: list[Inconsistencia] = Field(..., description="Hallazgos que requieren revisión")
class SalidaCasosUso(ContratoBase):
    casos_uso: list[CasoUso] = Field(..., description="Casos de uso preliminares")
