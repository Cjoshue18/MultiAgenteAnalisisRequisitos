import json
from typing import Optional, Dict, Any, List
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Session, relationship
from src.persistence.database import Base, SessionLocal
from datetime import datetime


class AnalisisORM(Base):
    __tablename__ = "analisis"

    id = Column(Integer, primary_key=True, index=True)
    analisis_id = Column(String, unique=True, index=True, nullable=False)
    texto_entrada = Column(Text, nullable=False)
    estado = Column(String, default="EN_PROCESO")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    comentarios_analista = Column(Text, nullable=True)
    aprobado_humano = Column(Integer, default=0)

    requisitos = relationship("RequisitoORM", back_populates="analisis", cascade="all, delete-orphan")
    inconsistencias = relationship("InconsistenciaORM", back_populates="analisis", cascade="all, delete-orphan")
    casos_uso = relationship("CasoUsoORM", back_populates="analisis", cascade="all, delete-orphan")


class RequisitoORM(Base):
    __tablename__ = "requisitos"

    id = Column(Integer, primary_key=True, index=True)
    analisis_id_fk = Column(String, ForeignKey("analisis.analisis_id"))
    codigo = Column(String, nullable=False)
    tipo = Column(String, nullable=False)  # RF o RNF
    nombre = Column(String, nullable=False)
    descripcion = Column(Text, nullable=False)
    actores = Column(Text, nullable=True)
    categoria_iso = Column(String, nullable=True)
    metrica_objetiva = Column(Text, nullable=True)
    valor_umbral = Column(Text, nullable=True)
    referencia_texto = Column(Text, nullable=True)

    analisis = relationship("AnalisisORM", back_populates="requisitos")


class InconsistenciaORM(Base):
    __tablename__ = "inconsistencias"

    id = Column(Integer, primary_key=True, index=True)
    analisis_id_fk = Column(String, ForeignKey("analisis.analisis_id"))
    tipo = Column(String, nullable=False)
    severidad = Column(String, nullable=False)
    elementos_afectados = Column(String, nullable=True)
    descripcion_problema = Column(Text, nullable=True)
    pregunta_clarificacion = Column(Text, nullable=True)

    analisis = relationship("AnalisisORM", back_populates="inconsistencias")


class CasoUsoORM(Base):
    __tablename__ = "casos_uso"

    id = Column(Integer, primary_key=True, index=True)
    analisis_id_fk = Column(String, ForeignKey("analisis.analisis_id"))
    codigo = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    actor_principal = Column(String, nullable=True)
    precondiciones = Column(Text, nullable=True)
    flujo_principal = Column(Text, nullable=True)
    flujos_alternativos = Column(Text, nullable=True)
    postcondiciones = Column(Text, nullable=True)

    analisis = relationship("AnalisisORM", back_populates="casos_uso")


class AnalisisRepository:
    """Repositorio de persistencia desacoplada para analisis y requerimientos."""

    def __init__(self, db: Optional[Session] = None) -> None:
        self._db = db or SessionLocal()

    def crear_analisis(self, analisis_id: str, texto_entrada: str) -> AnalisisORM:
        db_obj = AnalisisORM(
            analisis_id=analisis_id,
            texto_entrada=texto_entrada,
            estado="EN_PROCESO",
        )
        self._db.add(db_obj)
        self._db.commit()
        self._db.refresh(db_obj)
        return db_obj

    def obtener_analisis(self, analisis_id: str) -> Optional[AnalisisORM]:
        return self._db.query(AnalisisORM).filter(AnalisisORM.analisis_id == analisis_id).first()

    def listar_analisis(self) -> List[AnalisisORM]:
        return self._db.query(AnalisisORM).order_by(AnalisisORM.fecha_creacion.desc()).all()

    def actualizar_estado(self, analisis_id: str, estado: str, comentarios: Optional[str] = None,
                          aprobado: bool = False) -> Optional[AnalisisORM]:
        obj = self.obtener_analisis(analisis_id)
        if not obj:
            return None
        obj.estado = estado
        if comentarios is not None:
            obj.comentarios_analista = comentarios
        obj.aprobado_humano = 1 if aprobado else 0
        self._db.commit()
        self._db.refresh(obj)
        return obj

    def guardar_requisito(self, analisis_id: str, datos: Dict[str, Any]) -> RequisitoORM:
        db_obj = RequisitoORM(
            analisis_id_fk=analisis_id,
            codigo=datos.get("id", ""),
            tipo=datos.get("tipo", "RF"),
            nombre=datos.get("nombre", ""),
            descripcion=datos.get("descripcion", ""),
            actores=json.dumps(datos.get("actores", [])),
            categoria_iso=datos.get("categoria_iso"),
            metrica_objetiva=datos.get("metrica_objetiva"),
            valor_umbral=datos.get("valor_umbral"),
            referencia_texto=datos.get("referencia_texto"),
        )
        self._db.add(db_obj)
        self._db.commit()
        self._db.refresh(db_obj)
        return db_obj

    def guardar_inconsistencia(self, analisis_id: str, datos: Dict[str, Any]) -> InconsistenciaORM:
        db_obj = InconsistenciaORM(
            analisis_id_fk=analisis_id,
            tipo=datos.get("tipo", ""),
            severidad=datos.get("severidad", ""),
            elementos_afectados=datos.get("elementos_afectados"),
            descripcion_problema=datos.get("descripcion_problema"),
            pregunta_clarificacion=datos.get("pregunta_clarificacion"),
        )
        self._db.add(db_obj)
        self._db.commit()
        self._db.refresh(db_obj)
        return db_obj

    def guardar_caso_uso(self, analisis_id: str, datos: Dict[str, Any]) -> CasoUsoORM:
        db_obj = CasoUsoORM(
            analisis_id_fk=analisis_id,
            codigo=datos.get("id", ""),
            nombre=datos.get("nombre", ""),
            actor_principal=datos.get("actor_principal"),
            precondiciones=json.dumps(datos.get("precondiciones", [])),
            flujo_principal=json.dumps(datos.get("flujo_principal", [])),
            flujos_alternativos=json.dumps(datos.get("flujos_alternativos", [])),
            postcondiciones=json.dumps(datos.get("postcondiciones", [])),
        )
        self._db.add(db_obj)
        self._db.commit()
        self._db.refresh(db_obj)
        return db_obj

    def close(self) -> None:
        self._db.close()
