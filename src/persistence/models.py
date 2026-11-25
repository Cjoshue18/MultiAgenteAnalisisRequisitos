from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ProyectoORM(Base):
    __tablename__ = "proyectos"

    proyecto_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, default="", nullable=False)
    fecha_creacion: Mapped[str] = mapped_column(String(64), nullable=False)


class AnalisisORM(Base):
    __tablename__ = "analisis"

    analisis_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    proyecto_id: Mapped[str] = mapped_column(String(64), ForeignKey("proyectos.proyecto_id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    analisis_origen_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    estado: Mapped[str] = mapped_column(String(32), nullable=False)
    modalidad_modelado: Mapped[str] = mapped_column(String(16), nullable=False)
    texto_usuario: Mapped[str] = mapped_column(Text, default="", nullable=False)
    estrategia_ingesta: Mapped[str] = mapped_column(String(16), default="directa", nullable=False)
    advertencias_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    rf_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    rnf_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    inconsistencias_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    cus_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    hu_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    respuestas_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    comentarios_analista: Mapped[str] = mapped_column(Text, default="", nullable=False)
    trazas_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    errores_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    reporte_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    fecha_creacion: Mapped[str] = mapped_column(String(64), nullable=False)
    fecha_aprobacion: Mapped[str | None] = mapped_column(String(64), nullable=True)
