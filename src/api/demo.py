"""Servidor de demostración local SIN credenciales de IA.

Se usa exclusivamente para mostrar el flujo completo en una exposición:
uvicorn src.api.demo:app --reload
Las respuestas son de ejemplo y NO deben presentarse como inferencias de IA.
"""
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver
from src.api.app import crear_app
from src.persistence.repository import RepositorioSQLite
from src.schemas.contracts import (
    CasoUso, CriterioAceptacion, HistoriaUsuario, Inconsistencia,
    RequisitoFuncional, RequisitoNoFuncional, SalidaCasosUso, SalidaHU,
    SalidaInconsistencias, SalidaRF, SalidaRNF,
)
from src.services.orchestrator import OrquestadorService


class ClienteDemostracion:
    """Datos de prueba para visualizar la solución sin hacer llamadas a proveedores."""

    def generar(self, esquema: type, instrucciones: str):
        texto_cita = "El usuario podrá consultar el catálogo y solicitar préstamos."
        # Estos valores son demostrativos, no análisis real del documento.
        if esquema is SalidaRF:
            return SalidaRF(requisitos=[RequisitoFuncional(
                id="RF-01", nombre="Consultar catálogo",
                descripcion="El sistema debe permitir consultar los libros del catálogo.",
                actores=["Usuario"], referencia_texto=texto_cita,
            )])
        if esquema is SalidaRNF:
            return SalidaRNF(requisitos=[RequisitoNoFuncional(
                id="RNF-01", categoria_iso="Rendimiento",
                descripcion="El sistema debe responder las consultas de catálogo oportunamente.",
                metrica_objetiva="Tiempo de respuesta en segundos",
                valor_umbral="2 s (valor ilustrativo, pendiente de validación)",
            )])
        if esquema is SalidaInconsistencias:
            return SalidaInconsistencias(inconsistencias=[Inconsistencia(
                tipo="vacío", severidad="Media",
                descripcion="No se indica la cantidad máxima de préstamos simultáneos.",
                pregunta_clarificacion="¿Cuántos préstamos puede tener un usuario a la vez?",
            )])
        if esquema is SalidaCasosUso:
            return SalidaCasosUso(casos_uso=[CasoUso(
                id="CUS-01", nombre="Consultar catálogo", actor_principal="Usuario",
                precondiciones=["El catálogo está disponible"],
                flujo_principal=["1. El usuario abre el catálogo", "2. El sistema muestra los libros"],
                flujos_alternativos=["No hay libros disponibles"],
                postcondiciones=["El usuario visualiza el catálogo"], rf_relacionados=["RF-01"],
            )])
        if esquema is SalidaHU:
            return SalidaHU(historias_usuario=[HistoriaUsuario(
                id="HU-01", titulo="Consulta del catálogo", como="Usuario",
                quiero="consultar los libros disponibles", para_que="elegir un préstamo adecuado",
                criterios_aceptacion=[CriterioAceptacion(
                    dado="que el catálogo está disponible", cuando="consulto los libros",
                    entonces="veo los libros registrados")], rf_relacionados=["RF-01"],
            )])
        raise ValueError(f"Contrato desconocido en modo demostración: {esquema}")


SERVICIO = OrquestadorService(
    ClienteDemostracion(), RepositorioSQLite("sqlite:///demo_analisis.db"),
    InMemorySaver(), Path("demo_reportes"),
)
app = crear_app(SERVICIO)
