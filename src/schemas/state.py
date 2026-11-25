import operator
from typing import Annotated, Literal, TypedDict
from src.schemas.contracts import (
    CasoUso,
    EstadoAnalisis,
    Inconsistencia,
    ReporteConsolidado,
    RequisitoFuncional,
    RequisitoNoFuncional,
    TrazaEjecucion,
)


class GraphState(TypedDict, total=False):
    analisis_id: str
    estado: EstadoAnalisis
    texto_usuario: str
    ruta_archivo: str | None
    tamano_bytes: int
    estrategia_ingesta: Literal["directa", "lotes"]
    fragmentos: list[str]
    requisitos_funcionales: list[RequisitoFuncional]
    requisitos_no_funcionales: list[RequisitoNoFuncional]
    inconsistencias: list[Inconsistencia]
    casos_uso: list[CasoUso]
    rf_aprobados: list[RequisitoFuncional]
    respuestas_clarificacion: dict[str, str]
    comentarios_analista: str
    reporte_consolidado: ReporteConsolidado | None
    errores: Annotated[list[str], operator.add]
    trazas: Annotated[list[TrazaEjecucion], operator.add]
