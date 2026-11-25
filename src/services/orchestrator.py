from pathlib import Path
from typing import Any
import uuid
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.types import Command
from src.agents.use_case_agent import nodo_modelado
from src.graph.workflow import _aplicar_respuestas_inconsistencias, construir_grafo
from src.persistence.repository import AnalisisRegistro, ProyectoInfo, RepositorioAnalisis
from src.schemas.contracts import (
    DecisionRevision,
    ModalidadModelado,
    consolidar_reporte,
    validar_decision_revision,
)
from src.services.exportador import FormatoExportacion, exportar_reporte
from src.services.llm_client import ClienteEstructurado


class OrquestadorService:
    """Patrón Fachada: unifica proyectos, grafo LangGraph, persistencia SQLite y exportación."""

    def __init__(
        self,
        cliente: ClienteEstructurado,
        repositorio: RepositorioAnalisis,
        checkpointer: BaseCheckpointSaver,
        directorio_reportes: Path = Path("reportes"),
    ) -> None:
        self.cliente = cliente
        self.repositorio = repositorio
        self.checkpointer = checkpointer
        self.directorio_reportes = directorio_reportes
        self._grafo = construir_grafo(cliente, checkpointer=checkpointer)

    def crear_proyecto(self, nombre: str, descripcion: str = "") -> ProyectoInfo:
        return self.repositorio.crear_proyecto(nombre, descripcion)

    def listar_proyectos(self) -> list[ProyectoInfo]:
        return self.repositorio.listar_proyectos()

    def iniciar_analisis(
        self,
        proyecto_id: str,
        modalidad_modelado: ModalidadModelado,
        texto: str | None = None,
        ruta_archivo: str | Path | None = None,
    ) -> AnalisisRegistro:
        self.repositorio.obtener_proyecto(proyecto_id)
        analisis_id = f"ANA-{uuid.uuid4().hex[:8].upper()}"
        entrada: dict[str, Any] = {
            "analisis_id": analisis_id,
            "modalidad_modelado": modalidad_modelado,
        }
        if texto is not None:
            entrada["texto_usuario"] = texto
        if ruta_archivo is not None:
            entrada["ruta_archivo"] = str(ruta_archivo)

        estado_final = self._grafo.invoke(entrada, config={"configurable": {"thread_id": analisis_id}})
        registro = self._mapear_estado(estado_final, analisis_id, proyecto_id, version=1)
        return self.repositorio.guardar_analisis(registro)

    def obtener_analisis(self, analisis_id: str) -> AnalisisRegistro:
        return self.repositorio.obtener_analisis(analisis_id)

    def listar_analisis(self, proyecto_id: str | None = None) -> list[AnalisisRegistro]:
        return self.repositorio.listar_analisis(proyecto_id=proyecto_id)

    def enviar_revision(self, analisis_id: str, decision: DecisionRevision) -> AnalisisRegistro:
        actual = self.repositorio.obtener_analisis(analisis_id)
        if actual.estado == "APROBADO":
            raise ValueError(f"El análisis {analisis_id} está APROBADO y es inmutable.")
        validar_decision_revision(actual.modalidad_modelado, decision)

        cfg = {"configurable": {"thread_id": analisis_id}}
        snapshot = self._grafo.get_state(cfg)
        if snapshot.next:
            estado_final = self._grafo.invoke(Command(resume=decision.model_dump()), config=cfg)
            registro = self._mapear_estado(
                estado_final,
                analisis_id,
                actual.proyecto_id,
                version=actual.version,
                base=actual,
            )
            return self.repositorio.guardar_analisis(registro)

        registro = self._aplicar_revision_sin_checkpoint(actual, decision)
        return self.repositorio.guardar_analisis(registro)

    def crear_nueva_version(self, analisis_id: str) -> AnalisisRegistro:
        return self.repositorio.crear_nueva_version(analisis_id)

    def exportar_analisis(
        self,
        analisis_id: str,
        formatos: list[FormatoExportacion],
    ) -> dict[str, Path]:
        actual = self.repositorio.obtener_analisis(analisis_id)
        if actual.estado != "APROBADO" or actual.reporte_consolidado is None:
            raise ValueError("Solo se pueden exportar análisis en estado APROBADO.")
        proyecto = self.repositorio.obtener_proyecto(actual.proyecto_id)
        return {
            fmt: exportar_reporte(
                actual.reporte_consolidado,
                fmt,
                self.directorio_reportes,
                nombre_proyecto=proyecto.nombre,
                version=actual.version,
            )
            for fmt in formatos
        }

    def _aplicar_revision_sin_checkpoint(
        self,
        actual: AnalisisRegistro,
        decision: DecisionRevision,
    ) -> AnalisisRegistro:
        rf = decision.rf_editados if decision.rf_editados is not None else actual.requisitos_funcionales
        rnf = decision.rnf_editados if decision.rnf_editados is not None else actual.requisitos_no_funcionales
        cus = decision.casos_uso_editados if decision.casos_uso_editados is not None else actual.casos_uso
        hu = decision.hu_editadas if decision.hu_editadas is not None else actual.historias_usuario
        inc = _aplicar_respuestas_inconsistencias(actual.inconsistencias, decision.respuestas_clarificacion)

        if decision.accion == "regenerar_cus":
            res = nodo_modelado(
                {"modalidad_modelado": actual.modalidad_modelado, "rf_aprobados": rf, "requisitos_funcionales": rf},
                self.cliente,
            )
            return actual.model_copy(
                update={
                    "requisitos_funcionales": rf,
                    "requisitos_no_funcionales": rnf,
                    "inconsistencias": inc,
                    "casos_uso": res.get("casos_uso", cus),
                    "historias_usuario": res.get("historias_usuario", hu),
                    "respuestas_clarificacion": decision.respuestas_clarificacion,
                    "comentarios_analista": decision.comentarios_analista,
                }
            )

        reporte = consolidar_reporte(
            analisis_id=actual.analisis_id,
            estado="APROBADO",
            modalidad_modelado=actual.modalidad_modelado,
            requisitos_funcionales=rf,
            requisitos_no_funcionales=rnf,
            inconsistencias=inc,
            casos_uso=cus,
            historias_usuario=hu,
            respuestas_clarificacion=decision.respuestas_clarificacion,
            comentarios_analista=decision.comentarios_analista,
        )
        return actual.model_copy(
            update={
                "estado": "APROBADO",
                "requisitos_funcionales": rf,
                "requisitos_no_funcionales": rnf,
                "inconsistencias": inc,
                "casos_uso": cus,
                "historias_usuario": hu,
                "respuestas_clarificacion": decision.respuestas_clarificacion,
                "comentarios_analista": decision.comentarios_analista,
                "reporte_consolidado": reporte,
            }
        )

    def _mapear_estado(
        self,
        estado: dict[str, Any],
        analisis_id: str,
        proyecto_id: str,
        version: int,
        base: AnalisisRegistro | None = None,
    ) -> AnalisisRegistro:
        datos: dict[str, Any] = {
            "analisis_id": analisis_id,
            "proyecto_id": proyecto_id,
            "version": version,
            "analisis_origen_id": base.analisis_origen_id if base else None,
            "estado": estado.get("estado", "FALLIDO"),
            "modalidad_modelado": estado.get("modalidad_modelado", base.modalidad_modelado if base else "CUS"),
            "texto_usuario": estado.get("texto_usuario", base.texto_usuario if base else ""),
            "estrategia_ingesta": estado.get("estrategia_ingesta", "directa"),
            "advertencias": estado.get("advertencias", []),
            "requisitos_funcionales": estado.get("requisitos_funcionales", []),
            "requisitos_no_funcionales": estado.get("requisitos_no_funcionales", []),
            "inconsistencias": estado.get("inconsistencias", []),
            "casos_uso": estado.get("casos_uso", []),
            "historias_usuario": estado.get("historias_usuario", []),
            "respuestas_clarificacion": estado.get("respuestas_clarificacion", {}),
            "comentarios_analista": estado.get("comentarios_analista", ""),
            "trazas": estado.get("trazas", []),
            "errores": estado.get("errores", []),
            "reporte_consolidado": estado.get("reporte_consolidado"),
        }
        if base is not None:
            datos["fecha_creacion"] = base.fecha_creacion
        return AnalisisRegistro(**datos)
