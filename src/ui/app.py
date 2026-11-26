"""Interfaz Streamlit para el flujo completo: proyecto, entrada, revisión, HITL y exportación.

Ejecutar: streamlit run src/ui/app.py
Requiere FastAPI corriendo en http://localhost:8000 (o API_BASE_URL).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any

# Streamlit ejecuta el archivo como script y puede cambiar el directorio de importación.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import streamlit as st

from src.services.api_client import ClienteAPI, ErrorAPI

st.set_page_config(page_title="Analizador de Requisitos · Grupo 6", page_icon="🧠", layout="wide")

ESTILOS = """
<style>
:root {color-scheme:dark}
.stApp {background:radial-gradient(circle at 78% 7%,#152b54 0%,#08162e 32%,#061025 74%);color:#e7eefc}
[data-testid="stSidebar"] {background:linear-gradient(170deg,#0e2144,#07142b);border-right:1px solid #29436a}
h1,h2,h3 {letter-spacing:-.025em;color:#eef6ff!important}
[data-testid="stMetric"] {background:#0d2445;border:1px solid #234a74;border-radius:16px;padding:16px}
.stButton>button[kind="primary"] {background:linear-gradient(110deg,#7047e9,#11a5ed);border:0;border-radius:11px;font-weight:700}
.stButton>button {border-radius:11px}
.stTabs [data-baseweb="tab-list"] {gap:12px}
.stTabs [data-baseweb="tab"] {border-radius:10px;padding:8px 16px;background:#102344}
.hero {padding:27px 30px;background:linear-gradient(105deg,#102e57,#101f42 65%,#2a1d58);border:1px solid #355c87;border-radius:20px;margin-bottom:20px}
.hero h1 {font-size:2.2rem;margin:0 0 7px}
.hero p {color:#bad0ef;margin:0}
.kicker {font-size:.85rem;color:#50daf3;font-weight:700;letter-spacing:.11em;text-transform:uppercase}
.info {padding:15px;border:1px solid #31517a;border-radius:13px;background:#102343;margin-bottom:10px}
.info strong {color:#75ddff}
</style>
"""
st.markdown(ESTILOS, unsafe_allow_html=True)


def api() -> ClienteAPI:
    return ClienteAPI(os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))


def ejecutar(funcion, *args, **kwargs):
    """Centraliza la gestión visual de errores del backend sin ocultar la causa."""
    try:
        return funcion(*args, **kwargs)
    except (ErrorAPI, ValueError) as exc:
        st.error(str(exc))
        return None


def tabla_editable(items: list[dict], titulo: str, clave: str, columnas: list[str], editable: bool = True) -> list[dict]:
    """Edita solo campos escalares, preservando los campos anidados del contrato."""
    st.subheader(f"{titulo} · {len(items)}")
    if not items:
        st.info("No hay elementos en esta categoría.")
        return []
    st.caption("Puedes corregir las descripciones antes de la aprobación humana." if editable else "Vista de solo lectura: análisis aprobado.")
    vista = [{c: item.get(c, "") for c in columnas} for item in items]
    editada = st.data_editor(vista, key=f"editor_{clave}", use_container_width=True,
                             hide_index=True, num_rows="fixed",
                             disabled=([c for c in columnas if c in {"id", "categoria_iso", "tipo", "severidad", "referencia_texto"}]
                                       if editable else columnas))
    salida: list[dict] = []
    for original, cambios in zip(items, editada):
        nuevo = dict(original)
        for campo, valor in cambios.items():
            if campo not in {"id", "categoria_iso", "tipo", "severidad", "referencia_texto"} and isinstance(valor, str):
                nuevo[campo] = valor
        salida.append(nuevo)
    return salida


def ver_documento(registro: dict) -> None:
    st.subheader("Texto original y trazabilidad")
    st.text_area("Solicitud recibida", value=registro.get("texto_usuario", ""), height=180,
                 disabled=True)
    for rf in registro.get("requisitos_funcionales", []):
        with st.expander(f"{rf['id']} · {rf.get('nombre', '')}"):
            st.write(rf.get("descripcion", ""))
            st.info("Cita: " + rf.get("referencia_texto", ""))
            st.caption("Actores: " + ", ".join(rf.get("actores", [])))


def vista_analisis(cliente: ClienteAPI, registro: dict) -> None:
    aid = registro["analisis_id"]
    estado = registro.get("estado", "")
    st.markdown(f"### Análisis `{aid}` · {estado.replace('_', ' ')}")
    a, b, c, d = st.columns(4)
    a.metric("Requisitos funcionales", len(registro.get("requisitos_funcionales", [])))
    b.metric("Requisitos no funcionales", len(registro.get("requisitos_no_funcionales", [])))
    c.metric("Inconsistencias", len(registro.get("inconsistencias", [])))
    d.metric("Modelos", len(registro.get("casos_uso", [])) + len(registro.get("historias_usuario", [])))
    if registro.get("errores"):
        st.error("\n".join(registro["errores"]))
    for aviso in registro.get("advertencias", []):
        st.caption("ℹ️ " + aviso)

    tab_rf, tab_rnf, tab_inc, tab_cus, tab_hu, tab_fuente, tab_traza = st.tabs([
        "🔷 Funcionales", "🛡️ No funcionales", "⚠️ Inconsistencias", "🧩 Casos de uso",
        "📝 Historias de usuario", "🔎 Trazabilidad", "📍 Auditoría",
    ])
    with tab_rf:
        rf_final = tabla_editable(registro.get("requisitos_funcionales", []), "Requisitos funcionales", aid + "_rf",
                                   ["id", "nombre", "descripcion", "referencia_texto"], editable=estado == "PENDIENTE_APROBACION")
        # Los actores se mantienen para no perder el contrato original.
    with tab_rnf:
        rnf_final = tabla_editable(registro.get("requisitos_no_funcionales", []), "Requisitos no funcionales", aid + "_rnf",
                                    ["id", "categoria_iso", "descripcion", "metrica_objetiva", "valor_umbral"], editable=estado == "PENDIENTE_APROBACION")
    with tab_inc:
        incs = registro.get("inconsistencias", [])
        respuestas: dict[str, str] = {}
        if not incs:
            st.success("No se registraron inconsistencias.")
        for i, inc in enumerate(incs):
            with st.container(border=True):
                st.markdown(f"**{inc.get('severidad')} · {inc.get('tipo')}** — {inc.get('descripcion', '')}")
                st.caption("Elementos: " + ", ".join(inc.get("elementos_afectados", [])))
                respuestas[str(i)] = st.text_input(inc.get("pregunta_clarificacion", "Pregunta"),
                                                  value=inc.get("respuesta_analista") or "",
                                                  key=f"preg_{aid}_{i}", disabled=estado != "PENDIENTE_APROBACION")
    with tab_cus:
        cus_final = tabla_editable(registro.get("casos_uso", []), "Casos de uso", aid + "_cus",
                                    ["id", "nombre", "actor_principal"], editable=estado == "PENDIENTE_APROBACION")
        for caso in cus_final:
            with st.expander(f"Flujo de {caso['id']}"):
                st.write("**Precondiciones:**", caso.get("precondiciones", []))
                st.write("**Flujo principal:**", caso.get("flujo_principal", []))
                st.write("**Alternativos:**", caso.get("flujos_alternativos", []))
                st.write("**Postcondiciones:**", caso.get("postcondiciones", []))
    with tab_hu:
        hu_final = tabla_editable(registro.get("historias_usuario", []), "Historias de usuario", aid + "_hu",
                                   ["id", "titulo", "como", "quiero", "para_que"], editable=estado == "PENDIENTE_APROBACION")
        for historia in hu_final:
            with st.expander(f"Criterios de {historia['id']}"):
                for crit in historia.get("criterios_aceptacion", []):
                    st.write(f"DADO {crit['dado']} / CUANDO {crit['cuando']} / ENTONCES {crit['entonces']}")
    with tab_fuente:
        ver_documento(registro)
    with tab_traza:
        for evento in registro.get("trazas", []):
            st.write(f"**{evento.get('nodo')}** · {evento.get('estado')} · {evento.get('detalle', '')}")
        st.caption(f"Versión: {registro.get('version', 1)} · Creado: {registro.get('fecha_creacion', '')}")

    st.divider()
    if estado == "APROBADO":
        st.success("Informe aprobado. Puedes descargarlo o crear una nueva versión.")
        col1, col2 = st.columns([1, 2])
        with col1:
            if st.button("➕ Crear nueva versión", use_container_width=True):
                nueva = ejecutar(cliente.crear_version, aid)
                if nueva:
                    st.session_state["analisis_id"] = nueva["analisis_id"]
                    st.rerun()
        with col2:
            formatos = {"md": "Markdown", "json": "JSON", "pdf": "PDF", "docx": "Word"}
            formato = st.selectbox("Formato de descarga", list(formatos), format_func=lambda x: formatos[x])
            if st.button("Preparar descarga", use_container_width=True):
                datos = ejecutar(cliente.exportar, aid, formato)
                if datos is not None:
                    st.session_state["descarga"] = (aid, formato, datos)
            descarga = st.session_state.get("descarga")
            if descarga and descarga[:2] == (aid, formato):
                st.download_button(f"⬇️ Descargar {formatos[formato]}", data=descarga[2],
                                   file_name=f"{aid}.{formato}", use_container_width=True)
    elif estado == "PENDIENTE_APROBACION":
        st.markdown("### ✍️ Revisión humana (Human-in-the-Loop)")
        st.caption("Los hallazgos son propuestas. El informe no se puede exportar hasta aprobarlo.")
        comentarios = st.text_area("Comentarios del analista", key=f"comentarios_{aid}",
                                   value=registro.get("comentarios_analista", ""))
        decision_base = {
            "modalidad_solicitada": registro.get("modalidad_modelado"),
            "rf_editados": rf_final,
            "rnf_editados": rnf_final,
            "casos_uso_editados": cus_final,
            "hu_editadas": hu_final,
            "respuestas_clarificacion": {k: v for k, v in respuestas.items() if v.strip()},
            "comentarios_analista": comentarios,
        }
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Aprobar análisis", type="primary", use_container_width=True):
                salida = ejecutar(cliente.revisar, aid, {"accion": "aprobar", **decision_base})
                if salida:
                    st.success("Análisis aprobado")
                    st.session_state.pop("descarga", None)
                    st.rerun()
        with col2:
            if st.button("🔄 Regenerar modelado CUS/HU", use_container_width=True):
                salida = ejecutar(cliente.revisar, aid, {"accion": "regenerar_cus", **decision_base})
                if salida:
                    st.rerun()
    elif estado == "FALLIDO":
        st.warning("El análisis falló. Revisa la auditoría y crea una nueva solicitud.")


def main() -> None:
    cliente = api()
    with st.sidebar:
        st.markdown("## 🧠 MultiAgente IA")
        st.caption("Grupo 6 · Arquitectura y Evolución de Software")
        st.divider()
        pagina = st.radio("Navegación", ["🏠 Panel general", "➕ Nuevo análisis", "🕘 Historial"],
                          label_visibility="collapsed")
        st.divider()
        try:
            cliente.estado()
            st.success("API conectada", icon="✅")
        except ErrorAPI:
            st.error("API sin conexión")
        st.caption("Python · FastAPI · LangGraph · Streamlit")

    st.markdown('<div class="hero"><div class="kicker">Ingeniería de requisitos · Grupo 6</div>'
                '<h1>Analizador inteligente de requisitos</h1>'
                '<p>Cuatro agentes especializados, trazabilidad verificable y aprobación humana.</p></div>',
                unsafe_allow_html=True)

    proyectos = ejecutar(cliente.proyectos)
    if proyectos is None:
        st.info("Inicia la API en otra terminal: `uvicorn src.api.app:app --reload`.")
        st.stop()

    with st.expander("📁 Crear proyecto", expanded=not bool(proyectos)):
        with st.form("form_proyecto", clear_on_submit=True):
            nombre = st.text_input("Nombre del proyecto", placeholder="Ej.: Biblioteca universitaria")
            descripcion = st.text_area("Descripción (opcional)", height=70)
            if st.form_submit_button("Crear proyecto", type="primary"):
                nuevo = ejecutar(cliente.crear_proyecto, nombre, descripcion)
                if nuevo:
                    st.session_state["proyecto_id"] = nuevo["proyecto_id"]
                    st.rerun()

    if not proyectos:
        st.warning("Primero crea un proyecto para comenzar.")
        st.stop()
    ids = {f"{p['nombre']} · {p['proyecto_id']}": p["proyecto_id"] for p in proyectos}
    etiquetas = list(ids)
    elegido = st.session_state.get("proyecto_id")
    indice = next((i for i, k in enumerate(etiquetas) if ids[k] == elegido), 0)
    clave = st.selectbox("Proyecto activo", etiquetas, index=indice)
    proyecto_id = ids[clave]
    st.session_state["proyecto_id"] = proyecto_id

    if pagina == "➕ Nuevo análisis":
        st.markdown("### 📄 Nueva solicitud")
        modalidad = st.radio("Modalidad de modelado (fija para este análisis)", ["CUS", "HU", "AMBOS"],
                             horizontal=True, help="CUS: casos de uso. HU: historias de usuario. AMBOS: genera ambos.")
        if modalidad == "AMBOS":
            st.info("Generar ambos modelos puede incrementar el tiempo de respuesta.")
        metodo = st.radio("Tipo de entrada", ["Escribir texto", "Cargar archivo"], horizontal=True)
        archivo = None
        texto = ""
        if metodo == "Escribir texto":
            texto = st.text_area("Descripción del sistema", height=210,
                                 placeholder="El usuario podrá consultar libros y registrar préstamos...")
            st.caption(f"{len(texto.strip())} caracteres · mínimo 20")
        else:
            archivo = st.file_uploader("Documento de requisitos", type=["txt", "md", "pdf"],
                                       help="Hasta 10 MB; PDF debe contener texto seleccionable.")
        if st.button("🚀 Iniciar análisis", type="primary", use_container_width=True):
            if metodo == "Escribir texto":
                if len(texto.strip()) < 20:
                    st.warning("Ingresa al menos 20 caracteres significativos.")
                    st.stop()
                operacion = lambda: cliente.iniciar_texto(proyecto_id, modalidad, texto)
            else:
                if archivo is None:
                    st.warning("Selecciona un archivo.")
                    st.stop()
                operacion = lambda: cliente.iniciar_archivo(proyecto_id, modalidad, archivo.name, archivo.getvalue())
            with st.spinner("Los cuatro subagentes están procesando la solicitud..."):
                nuevo = ejecutar(operacion)
            if nuevo:
                st.session_state["analisis_id"] = nuevo["analisis_id"]
                st.rerun()

    historial = ejecutar(cliente.analisis, proyecto_id)
    if historial is None:
        st.stop()
    if pagina == "🕘 Historial":
        st.subheader("Análisis anteriores")
        if historial:
            st.dataframe([{"Código": x["analisis_id"], "Estado": x["estado"],
                           "Modalidad": x["modalidad_modelado"], "Versión": x["version"],
                           "Fecha": x["fecha_creacion"]} for x in historial],
                         use_container_width=True, hide_index=True)
        else:
            st.info("Aún no hay análisis en este proyecto.")
    if pagina == "🏠 Panel general":
        a, b, c = st.columns(3)
        a.metric("Análisis realizados", len(historial))
        b.metric("Pendientes de revisión", sum(x["estado"] == "PENDIENTE_APROBACION" for x in historial))
        c.metric("Reportes aprobados", sum(x["estado"] == "APROBADO" for x in historial))
        st.markdown("### 🔁 Flujo multiagente")
        st.markdown('<div class="info">🧠 <strong>Orquestador</strong> → '
                    '🔷 <strong>RF + RNF en paralelo</strong> → ⚠️ <strong>Inconsistencias</strong> → '
                    '🧩 <strong>CUS / HU</strong> → ✅ <strong>Revisión humana</strong> → Reporte</div>',
                    unsafe_allow_html=True)

    if historial:
        opciones = {f"{x['analisis_id']} · {x['estado']} · v{x['version']}": x["analisis_id"] for x in historial}
        claves = list(opciones)
        actual = st.session_state.get("analisis_id")
        indice = next((i for i, k in enumerate(claves) if opciones[k] == actual), 0)
        seleccionado = st.selectbox("Abrir análisis", claves, index=indice)
        st.session_state["analisis_id"] = opciones[seleccionado]
        registro = ejecutar(cliente.obtener_analisis, opciones[seleccionado])
        if registro:
            vista_analisis(cliente, registro)


if __name__ == "__main__":
    main()
