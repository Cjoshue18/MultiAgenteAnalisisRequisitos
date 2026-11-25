from datetime import datetime, timezone
import json
from typing import Protocol, TypeVar
import uuid
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from src.persistence.models import AnalisisORM, Base, ProyectoORM
from src.schemas.contracts import (
    CasoUso,
    EstadoAnalisis,
    HistoriaUsuario,
    Inconsistencia,
    ModalidadModelado,
    ReporteConsolidado,
    RequisitoFuncional,
    RequisitoNoFuncional,
    TrazaEjecucion,
)

T = TypeVar("T", bound=BaseModel)


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dump_lista(items: list[BaseModel]) -> str:
    return json.dumps([i.model_dump() for i in items], ensure_ascii=False)


def _load_lista(raw: str, modelo: type[T]) -> list[T]:
    return [modelo.model_validate(item) for item in json.loads(raw or "[]")]


class ProyectoInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    proyecto_id: str
    nombre: str
    descripcion: str = ""
    fecha_creacion: str


class AnalisisRegistro(BaseModel):
    model_config = ConfigDict(frozen=True)

    analisis_id: str
    proyecto_id: str
    version: int = 1
    analisis_origen_id: str | None = None
    estado: EstadoAnalisis
    modalidad_modelado: ModalidadModelado
    texto_usuario: str = ""
    estrategia_ingesta: str = "directa"
    advertencias: list[str] = Field(default_factory=list)
    requisitos_funcionales: list[RequisitoFuncional] = Field(default_factory=list)
    requisitos_no_funcionales: list[RequisitoNoFuncional] = Field(default_factory=list)
    inconsistencias: list[Inconsistencia] = Field(default_factory=list)
    casos_uso: list[CasoUso] = Field(default_factory=list)
    historias_usuario: list[HistoriaUsuario] = Field(default_factory=list)
    respuestas_clarificacion: dict[str, str] = Field(default_factory=dict)
    comentarios_analista: str = ""
    trazas: list[TrazaEjecucion] = Field(default_factory=list)
    errores: list[str] = Field(default_factory=list)
    reporte_consolidado: ReporteConsolidado | None = None
    fecha_creacion: str = Field(default_factory=_ahora_iso)
    fecha_aprobacion: str | None = None


class RepositorioAnalisis(Protocol):
    def crear_proyecto(self, nombre: str, descripcion: str = "") -> ProyectoInfo: ...
    def obtener_proyecto(self, proyecto_id: str) -> ProyectoInfo: ...
    def listar_proyectos(self) -> list[ProyectoInfo]: ...
    def guardar_analisis(self, registro: AnalisisRegistro) -> AnalisisRegistro: ...
    def obtener_analisis(self, analisis_id: str) -> AnalisisRegistro: ...
    def listar_analisis(self, proyecto_id: str | None = None) -> list[AnalisisRegistro]: ...
    def crear_nueva_version(self, analisis_id: str) -> AnalisisRegistro: ...


def _orm_a_registro(row: AnalisisORM) -> AnalisisRegistro:
    reporte = ReporteConsolidado.model_validate_json(row.reporte_json) if row.reporte_json else None
    return AnalisisRegistro(
        analisis_id=row.analisis_id,
        proyecto_id=row.proyecto_id,
        version=row.version,
        analisis_origen_id=row.analisis_origen_id,
        estado=row.estado,  # type: ignore[arg-type]
        modalidad_modelado=row.modalidad_modelado,  # type: ignore[arg-type]
        texto_usuario=row.texto_usuario,
        estrategia_ingesta=row.estrategia_ingesta,
        advertencias=json.loads(row.advertencias_json or "[]"),
        requisitos_funcionales=_load_lista(row.rf_json, RequisitoFuncional),
        requisitos_no_funcionales=_load_lista(row.rnf_json, RequisitoNoFuncional),
        inconsistencias=_load_lista(row.inconsistencias_json, Inconsistencia),
        casos_uso=_load_lista(row.cus_json, CasoUso),
        historias_usuario=_load_lista(row.hu_json, HistoriaUsuario),
        respuestas_clarificacion=json.loads(row.respuestas_json or "{}"),
        comentarios_analista=row.comentarios_analista,
        trazas=_load_lista(row.trazas_json, TrazaEjecucion),
        errores=json.loads(row.errores_json or "[]"),
        reporte_consolidado=reporte,
        fecha_creacion=row.fecha_creacion,
        fecha_aprobacion=row.fecha_aprobacion,
    )


class RepositorioSQLite:
    """Adaptador relacional SQLite (SQLAlchemy) con inmutabilidad RN09."""

    def __init__(self, db_url: str = "sqlite:///analisis.db") -> None:
        self.engine = create_engine(db_url, future=True)
        Base.metadata.create_all(self.engine)
        self._Session = sessionmaker(bind=self.engine, expire_on_commit=False)

    def crear_proyecto(self, nombre: str, descripcion: str = "") -> ProyectoInfo:
        nombre_limpio = nombre.strip()
        if not nombre_limpio:
            raise ValueError("El nombre del proyecto no puede estar vacío.")
        proyecto = ProyectoORM(
            proyecto_id=f"PRY-{uuid.uuid4().hex[:8].upper()}",
            nombre=nombre_limpio,
            descripcion=descripcion.strip(),
            fecha_creacion=_ahora_iso(),
        )
        with self._Session() as session:
            session.add(proyecto)
            session.commit()
            return ProyectoInfo(
                proyecto_id=proyecto.proyecto_id,
                nombre=proyecto.nombre,
                descripcion=proyecto.descripcion,
                fecha_creacion=proyecto.fecha_creacion,
            )

    def obtener_proyecto(self, proyecto_id: str) -> ProyectoInfo:
        with self._Session() as session:
            row = session.get(ProyectoORM, proyecto_id)
            if row is None:
                raise ValueError(f"Proyecto no encontrado: {proyecto_id}")
            return ProyectoInfo(
                proyecto_id=row.proyecto_id,
                nombre=row.nombre,
                descripcion=row.descripcion,
                fecha_creacion=row.fecha_creacion,
            )

    def listar_proyectos(self) -> list[ProyectoInfo]:
        with self._Session() as session:
            rows = session.scalars(select(ProyectoORM).order_by(ProyectoORM.fecha_creacion.desc())).all()
            return [
                ProyectoInfo(
                    proyecto_id=r.proyecto_id,
                    nombre=r.nombre,
                    descripcion=r.descripcion,
                    fecha_creacion=r.fecha_creacion,
                )
                for r in rows
            ]

    def guardar_analisis(self, registro: AnalisisRegistro) -> AnalisisRegistro:
        with self._Session() as session:
            if session.get(ProyectoORM, registro.proyecto_id) is None:
                raise ValueError(f"Proyecto inexistente: {registro.proyecto_id}")
            existente = session.get(AnalisisORM, registro.analisis_id)
            if existente is not None and existente.estado == "APROBADO":
                raise ValueError(f"El análisis {registro.analisis_id} está APROBADO y es inmutable.")
            fecha_aprob = registro.fecha_aprobacion or (_ahora_iso() if registro.estado == "APROBADO" else None)
            row = existente or AnalisisORM(analisis_id=registro.analisis_id)
            row.proyecto_id = registro.proyecto_id
            row.version = registro.version
            row.analisis_origen_id = registro.analisis_origen_id
            row.estado = registro.estado
            row.modalidad_modelado = registro.modalidad_modelado
            row.texto_usuario = registro.texto_usuario
            row.estrategia_ingesta = registro.estrategia_ingesta
            row.advertencias_json = json.dumps(registro.advertencias, ensure_ascii=False)
            row.rf_json = _dump_lista(list(registro.requisitos_funcionales))
            row.rnf_json = _dump_lista(list(registro.requisitos_no_funcionales))
            row.inconsistencias_json = _dump_lista(list(registro.inconsistencias))
            row.cus_json = _dump_lista(list(registro.casos_uso))
            row.hu_json = _dump_lista(list(registro.historias_usuario))
            row.respuestas_json = json.dumps(registro.respuestas_clarificacion, ensure_ascii=False)
            row.comentarios_analista = registro.comentarios_analista
            row.trazas_json = _dump_lista(list(registro.trazas))
            row.errores_json = json.dumps(registro.errores, ensure_ascii=False)
            row.reporte_json = (
                registro.reporte_consolidado.model_dump_json() if registro.reporte_consolidado else None
            )
            row.fecha_creacion = registro.fecha_creacion
            row.fecha_aprobacion = fecha_aprob
            session.add(row)
            session.commit()
            return _orm_a_registro(row)

    def obtener_analisis(self, analisis_id: str) -> AnalisisRegistro:
        with self._Session() as session:
            row = session.get(AnalisisORM, analisis_id)
            if row is None:
                raise ValueError(f"Análisis no encontrado: {analisis_id}")
            return _orm_a_registro(row)

    def listar_analisis(self, proyecto_id: str | None = None) -> list[AnalisisRegistro]:
        with self._Session() as session:
            stmt = select(AnalisisORM)
            if proyecto_id is not None:
                stmt = stmt.where(AnalisisORM.proyecto_id == proyecto_id)
            rows = session.scalars(stmt.order_by(AnalisisORM.fecha_creacion.desc())).all()
            return [_orm_a_registro(r) for r in rows]

    def crear_nueva_version(self, analisis_id: str) -> AnalisisRegistro:
        origen = self.obtener_analisis(analisis_id)
        if origen.estado != "APROBADO":
            raise ValueError("Solo se puede crear una nueva versión desde un análisis APROBADO.")
        with self._Session() as session:
            max_ver = session.scalar(
                select(func.max(AnalisisORM.version)).where(AnalisisORM.proyecto_id == origen.proyecto_id)
            )
        siguiente = (max_ver or origen.version) + 1
        base_id = origen.analisis_origen_id or origen.analisis_id
        nuevo = origen.model_copy(
            update={
                "analisis_id": f"{base_id}-v{siguiente}",
                "version": siguiente,
                "analisis_origen_id": origen.analisis_id,
                "estado": "PENDIENTE_APROBACION",
                "reporte_consolidado": None,
                "fecha_creacion": _ahora_iso(),
                "fecha_aprobacion": None,
            }
        )
        return self.guardar_analisis(nuevo)
