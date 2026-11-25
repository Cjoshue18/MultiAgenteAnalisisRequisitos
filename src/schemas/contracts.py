from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

CategoriaISO = Literal[
    "Rendimiento",
    "Seguridad",
    "Fiabilidad",
    "Usabilidad",
    "Compatibilidad",
    "Mantenibilidad",
    "Escalabilidad",
    "Portabilidad",
]
EstadoAnalisis = Literal["EN_PROCESO", "PENDIENTE_APROBACION", "APROBADO", "FALLIDO"]
TextoNoVacio = Annotated[str, Field(min_length=1)]


class ContratoBase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class RequisitoFuncional(ContratoBase):
    id: str = Field(..., pattern=r"^RF-\d{2,}$", description="Código correlativo RF-01")
    nombre: str = Field(..., min_length=3, description="Título del requisito")
    descripcion: str = Field(..., min_length=10, description="Funcionalidad única verificable")
    actores: list[TextoNoVacio] = Field(..., min_length=1, description="Actores involucrados")
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
    respuesta_analista: str | None = Field(default=None, description="Respuesta ingresada en revisión humana")


class CasoUso(ContratoBase):
    id: str = Field(..., pattern=r"^CUS-\d{2,}$", description="Código correlativo CUS-01")
    nombre: str = Field(..., min_length=3, description="Nombre en infinitivo")
    actor_principal: str = Field(..., min_length=2, description="Actor que dispara el caso")
    precondiciones: list[TextoNoVacio] = Field(..., description="Condiciones previas")
    flujo_principal: list[str] = Field(..., min_length=1, description="Pasos numerados del flujo feliz")
    flujos_alternativos: list[TextoNoVacio] = Field(..., description="Excepciones y alternativas")
    postcondiciones: list[TextoNoVacio] = Field(..., description="Estado resultante")
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


class TrazaEjecucion(ContratoBase):
    nodo: str = Field(..., min_length=1, description="Nombre del nodo ejecutado")
    estado: Literal["COMPLETADO", "REINTENTO", "FALLIDO"] = Field(..., description="Resultado del nodo")
    inicio_iso: str = Field(..., min_length=1, description="Marca de tiempo inicial ISO-8601")
    fin_iso: str = Field(..., min_length=1, description="Marca de tiempo final ISO-8601")
    detalle: str = Field(default="", description="Resumen o mensaje del resultado")


class DecisionRevision(ContratoBase):
    accion: Literal["aprobar", "regenerar_cus"] = Field(..., description="Acción explícita del analista en HITL")
    rf_editados: list[RequisitoFuncional] | None = Field(default=None, description="RF editados o confirmados")
    rnf_editados: list[RequisitoNoFuncional] | None = Field(default=None, description="RNF editados o confirmados")
    casos_uso_editados: list[CasoUso] | None = Field(default=None, description="Casos de uso editados")
    respuestas_clarificacion: dict[str, str] = Field(default_factory=dict, description="Respuestas por hallazgo")
    comentarios_analista: str = Field(default="", description="Observaciones finales del analista")


class ReporteConsolidado(ContratoBase):
    analisis_id: str = Field(..., min_length=1, description="Identificador único del análisis")
    estado: Literal["APROBADO"] = Field(..., description="Solo se consolida en estado aprobado")
    requisitos_funcionales: list[RequisitoFuncional] = Field(default_factory=list)
    requisitos_no_funcionales: list[RequisitoNoFuncional] = Field(default_factory=list)
    inconsistencias: list[Inconsistencia] = Field(default_factory=list)
    casos_uso: list[CasoUso] = Field(default_factory=list)
    respuestas_clarificacion: dict[str, str] = Field(default_factory=dict)
    comentarios_analista: str = Field(default="")


def consolidar_reporte(
    *,
    analisis_id: str,
    estado: str,
    requisitos_funcionales: list[RequisitoFuncional],
    requisitos_no_funcionales: list[RequisitoNoFuncional],
    inconsistencias: list[Inconsistencia],
    casos_uso: list[CasoUso],
    respuestas_clarificacion: dict[str, str],
    comentarios_analista: str,
) -> ReporteConsolidado:
    """Construye el reporte final inmutable únicamente si existe aprobación humana."""
    if estado != "APROBADO":
        raise ValueError("El análisis requiere aprobación humana explícita para consolidar el reporte")
    return ReporteConsolidado(
        analisis_id=analisis_id,
        estado="APROBADO",
        requisitos_funcionales=requisitos_funcionales,
        requisitos_no_funcionales=requisitos_no_funcionales,
        inconsistencias=inconsistencias,
        casos_uso=casos_uso,
        respuestas_clarificacion=respuestas_clarificacion,
        comentarios_analista=comentarios_analista,
    )
