import json
from pathlib import Path
from typing import Literal
from docx import Document
from fpdf import FPDF
from src.schemas.contracts import ReporteConsolidado

FormatoExportacion = Literal["md", "json", "pdf", "docx"]


def _construir_secciones(
    reporte: ReporteConsolidado,
    nombre_proyecto: str,
    version: int,
) -> list[tuple[str, list[str]]]:
    secciones: list[tuple[str, list[str]]] = [
        (
            f"Especificación de Requisitos - {reporte.analisis_id}",
            [
                f"Proyecto: {nombre_proyecto or 'Sin proyecto'}",
                f"Versión: v{version}",
                f"Estado: {reporte.estado}",
                f"Modalidad de modelado: {reporte.modalidad_modelado}",
            ],
        ),
        (
            "Requisitos Funcionales (RF)",
            [
                f"{rf.id} - {rf.nombre}: {rf.descripcion} | Actores: {', '.join(rf.actores)} | Cita: \"{rf.referencia_texto}\""
                for rf in reporte.requisitos_funcionales
            ]
            or ["Sin requisitos funcionales registrados."],
        ),
        (
            "Requisitos No Funcionales (ISO/IEC 25010)",
            [
                f"{rnf.id} [{rnf.categoria_iso}]: {rnf.descripcion} | Métrica: {rnf.metrica_objetiva} ({rnf.valor_umbral})"
                for rnf in reporte.requisitos_no_funcionales
            ]
            or ["Sin requisitos no funcionales registrados."],
        ),
        (
            "Inconsistencias y Clarificaciones",
            [
                f"[{inc.severidad}] ({inc.tipo}) {inc.descripcion} | Pregunta: {inc.pregunta_clarificacion} | Respuesta: {inc.respuesta_analista or 'Sin respuesta'}"
                for inc in reporte.inconsistencias
            ]
            or ["Sin inconsistencias detectadas."],
        ),
    ]
    if reporte.casos_uso:
        secciones.append(
            (
                "Casos de Uso (CUS)",
                [
                    f"{cus.id} - {cus.nombre} (Actor: {cus.actor_principal}) | Flujo: {' '.join(cus.flujo_principal)}"
                    for cus in reporte.casos_uso
                ],
            )
        )
    if reporte.historias_usuario:
        secciones.append(
            (
                "Historias de Usuario (HU)",
                [
                    f"{hu.id} - {hu.titulo}: COMO {hu.como} QUIERO {hu.quiero} PARA QUE {hu.para_que} | Criterios: "
                    + "; ".join(f"DADO {c.dado} CUANDO {c.cuando} ENTONCES {c.entonces}" for c in hu.criterios_aceptacion)
                    for hu in reporte.historias_usuario
                ],
            )
        )
    secciones.append(
        (
            "Comentarios y Aprobación",
            [reporte.comentarios_analista or "Aprobado sin comentarios adicionales."],
        )
    )
    return secciones


def _latin1_seguro(texto: str) -> str:
    return texto.encode("latin-1", "replace").decode("latin-1")


def exportar_reporte(
    reporte: ReporteConsolidado,
    formato: FormatoExportacion,
    directorio_salida: Path,
    nombre_proyecto: str = "",
    version: int = 1,
) -> Path:
    """Exporta un reporte APROBADO a MD, JSON, PDF o DOCX (RF14 / RN10)."""
    if reporte.estado != "APROBADO":
        raise ValueError("Solo se pueden exportar reportes en estado APROBADO.")
    directorio_salida.mkdir(parents=True, exist_ok=True)
    ruta = directorio_salida / f"{reporte.analisis_id}_v{version}.{formato}"

    if formato == "json":
        payload = reporte.model_dump()
        payload["nombre_proyecto"] = nombre_proyecto
        payload["version"] = version
        ruta.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return ruta

    secciones = _construir_secciones(reporte, nombre_proyecto, version)

    if formato == "md":
        lineas: list[str] = []
        for idx, (titulo, items) in enumerate(secciones):
            prefijo = "#" if idx == 0 else "##"
            lineas.append(f"{prefijo} {titulo}")
            lineas.extend(f"- {item}" for item in items)
            lineas.append("")
        ruta.write_text("\n".join(lineas), encoding="utf-8")
        return ruta

    if formato == "docx":
        doc = Document()
        for idx, (titulo, items) in enumerate(secciones):
            doc.add_heading(titulo, level=1 if idx == 0 else 2)
            for item in items:
                doc.add_paragraph(item)
        doc.save(str(ruta))
        return ruta

    if formato == "pdf":
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        for idx, (titulo, items) in enumerate(secciones):
            pdf.set_font("Helvetica", "B", size=14 if idx == 0 else 12)
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 7, _latin1_seguro(titulo))
            pdf.set_font("Helvetica", size=10)
            for item in items:
                pdf.set_x(pdf.l_margin)
                pdf.multi_cell(0, 5, _latin1_seguro(f"- {item}"))
            pdf.ln(3)
        pdf.output(str(ruta))
        return ruta

    raise ValueError(f"Formato de exportación no soportado: {formato}")
