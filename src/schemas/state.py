from typing import TypedDict
from src.schemas.contracts import RequisitoFuncional, RequisitoNoFuncional, Inconsistencia, CasoUso

class GraphState(TypedDict, total=False):
    texto_usuario: str
    requisitos_funcionales: list[RequisitoFuncional]
    requisitos_no_funcionales: list[RequisitoNoFuncional]
    inconsistencias: list[Inconsistencia]
    casos_uso: list[CasoUso]
    rf_aprobados: list[RequisitoFuncional]
    errores: list[str]
