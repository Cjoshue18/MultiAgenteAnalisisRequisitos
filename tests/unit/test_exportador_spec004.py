import json
from pathlib import Path
from docx import Document
from pypdf import PdfReader
import pytest
from src.schemas.contracts import (
    CasoUso,
    CriterioAceptacion,
    HistoriaUsuario,
    Inconsistencia,
    ReporteConsolidado,
    RequisitoFuncional,
    RequisitoNoFuncional,
)
from src.services.exportador import exportar_reporte


def _reporte_aprobado() -> ReporteConsolidado:
    return ReporteConsolidado(
        analisis_id="ANA-EXP-01",
        estado="APROBADO",
        modalidad_modelado="AMBOS",
        requisitos_funcionales=[
            RequisitoFuncional(
                id="RF-01",
                nombre="Consultar catálogo",
                descripcion="El sistema debe permitir consultar libros disponibles.",
                actores=["Alumno"],
                referencia_texto="consultar libros disponibles",
            )
        ],
        requisitos_no_funcionales=[
            RequisitoNoFuncional(
                id="RNF-01",
                categoria_iso="Rendimiento",
                descripcion="Responder en menos de 2 segundos.",
                metrica_objetiva="Latencia",
                valor_umbral="2 s",
            )
        ],
        inconsistencias=[
            Inconsistencia(
                tipo="vacío",
                severidad="Alta",
                descripcion="No se indica el máximo de libros por préstamo.",
                pregunta_clarificacion="¿Cuántos libros puede prestar un alumno?",
                respuesta_analista="Hasta 3 libros simultáneos.",
            )
        ],
        casos_uso=[
            CasoUso(
                id="CUS-01",
                nombre="Consultar catálogo",
                actor_principal="Alumno",
                precondiciones=["Estar autenticado"],
                flujo_principal=["1. Buscar libro", "2. Mostrar resultados"],
                flujos_alternativos=[],
                postcondiciones=["Resultados mostrados"],
                rf_relacionados=["RF-01"],
            )
        ],
        historias_usuario=[
            HistoriaUsuario(
                id="HU-01",
                titulo="Consulta de catálogo",
                como="Alumno",
                quiero="buscar libros disponibles",
                para_que="solicitar un préstamo",
                criterios_aceptacion=[
                    CriterioAceptacion(
                        dado="que hay libros registrados",
                        cuando="busco por título",
                        entonces="veo disponibilidad",
                    )
                ],
                rf_relacionados=["RF-01"],
            )
        ],
        respuestas_clarificacion={"0": "Hasta 3 libros simultáneos."},
        comentarios_analista="Aprobado por analista.",
    )


def test_req_05_rechaza_exportacion_si_reporte_no_esta_aprobado(tmp_path: Path) -> None:
    reporte_falso = _reporte_aprobado().model_copy(update={"estado": "PENDIENTE_APROBACION"})
    with pytest.raises(ValueError, match="APROBADO"):
        exportar_reporte(reporte_falso, "md", tmp_path)


def test_req_06_exporta_markdown_y_json_con_trazabilidad_completa(tmp_path: Path) -> None:
    reporte = _reporte_aprobado()
    ruta_md = exportar_reporte(reporte, "md", tmp_path, nombre_proyecto="Biblioteca", version=1)
    ruta_json = exportar_reporte(reporte, "json", tmp_path, nombre_proyecto="Biblioteca", version=1)

    md_texto = ruta_md.read_text(encoding="utf-8")
    assert "ANA-EXP-01" in md_texto
    assert "RF-01" in md_texto and "consultar libros disponibles" in md_texto
    assert "RNF-01" in md_texto
    assert "Hasta 3 libros simultáneos." in md_texto
    assert "CUS-01" in md_texto and "HU-01" in md_texto

    data = json.loads(ruta_json.read_text(encoding="utf-8"))
    assert data["analisis_id"] == "ANA-EXP-01"
    assert data["nombre_proyecto"] == "Biblioteca"
    assert data["version"] == 1
    assert data["modalidad_modelado"] == "AMBOS"


def test_req_06_exporta_pdf_y_docx_validos_no_vacios(tmp_path: Path) -> None:
    reporte = _reporte_aprobado()
    ruta_pdf = exportar_reporte(reporte, "pdf", tmp_path, nombre_proyecto="Biblioteca", version=1)
    ruta_docx = exportar_reporte(reporte, "docx", tmp_path, nombre_proyecto="Biblioteca", version=1)

    assert ruta_pdf.exists() and ruta_pdf.stat().st_size > 200
    lector_pdf = PdfReader(str(ruta_pdf))
    assert len(lector_pdf.pages) >= 1
    assert "ANA-EXP-01" in (lector_pdf.pages[0].extract_text() or "")

    assert ruta_docx.exists() and ruta_docx.stat().st_size > 500
    doc = Document(str(ruta_docx))
    texto_doc = "\n".join(p.text for p in doc.paragraphs)
    assert "ANA-EXP-01" in texto_doc and "RF-01" in texto_doc
