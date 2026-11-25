from typing import List, Optional, Any, Dict, Annotated
import operator
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from src.schemas.functional import RequisitoFuncional
from src.schemas.rnf import RequisitoNoFuncional
from src.schemas.cus import CasoUso
from src.schemas.inconsistency import Inconsistencia


class GraphState(BaseModel):
    """Estado compartido tipado que fluye por el grafo LangGraph.

    Cada nodo lee el estado actual y retorna un diccionario con las claves
    actualizadas. Nunca muta el objeto directamente.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Entrada
    texto_usuario: str = Field(..., description="Texto de requisitos ingresado por el analista")
    analisis_id: Optional[str] = Field(None, description="Identificador unico del analisis")

    # Salidas de subagentes
    requisitos_funcionales: List[RequisitoFuncional] = Field(default_factory=list)
    requisitos_no_funcionales: List[RequisitoNoFuncional] = Field(default_factory=list)
    inconsistencias: List[Inconsistencia] = Field(default_factory=list)
    casos_de_uso: List[CasoUso] = Field(default_factory=list)

    # Control de flujo y errores
    errores: Annotated[list[str], operator.add] = Field(default_factory=list)
    etapa_actual: str = Field(default="inicio")
    aprobado_humano: bool = Field(default=False)
    comentarios_analista: Optional[str] = Field(None)

    # Metadatos
    fecha_creacion: Optional[datetime] = None
    tiempo_respuesta_segundos: Optional[float] = None
