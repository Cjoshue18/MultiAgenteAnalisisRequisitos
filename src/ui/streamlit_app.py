# -*- coding: utf-8 -*-
import streamlit as st
import requests
from typing import Dict, Any, List

API_BASE = "http://localhost:8000/api"


def main() -> None:
    st.set_page_config(
        page_title="Sistema Multiagente de Analisis de Requisitos",
        page_icon=":material/assignment:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Estilo adicional mínimo
    st.markdown(
        """
        <style>
        .metric-card {
            background: var(--secondary-background-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # ===================== SIDEBAR =====================
    with st.sidebar:
        st.title("Menu")
        st.divider()

        pagina = st.radio(
            "Navegacion",
            [
                ("Nuevo analisis", ":material/assignment:"),
                ("Historial", ":material/history:"),
                ("Detalle de analisis", ":material/description:"),
            ],
            format_func=lambda x: f"{x[1]} {x[0]}",
            label_visibility="collapsed",
        )
        st.divider()
        st.caption("Grupo 6  |  Arquitectura y Evolucion de Software (2026-2)")
        st.caption("Sistema Multiagente de Analisis de Requisitos")

    pagina_seleccionada = pagina[0]

    # ===================== PAGINA PRINCIPAL =====================
    st.title("Sistema Multiagente de Analisis de Requisitos")
    st.caption("Grupo 6  |  Arquitectura y Evolucion de Software (2026-2)")
    st.divider()

    # ---------------------------------------------------- NUEVO ANALISIS
    if pagina_seleccionada == "Nuevo analisis":
        st.subheader("Ingresar solicitud de analisis")

        texto = st.text_area(
            "Descripcion de requisitos (lenguaje natural)",
            height=260,
            placeholder="Ej: Necesito un sistema para una biblioteca universitaria donde los alumnos puedan consultar libros disponibles, realizar prestamos y recibir notificaciones cuando tengan que devolverlos.",
        )

        col_btn, col_spacer = st.columns([1, 4])
        with col_btn:
            analizar = st.button("Analizar", type="primary", width="stretch")

        if analizar:
            if len(texto.strip()) < 20:
                st.error("El texto debe tener al menos 20 caracteres.")
            else:
                with st.spinner("Ejecutando pipeline multiagente..."):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/analisis",
                            json={"texto": texto},
                            timeout=120,
                        )
                        if resp.status_code == 202:
                            data = resp.json()
                            st.success(
                                f"Analisis iniciado: **{data['analisis_id']}**  \nEstado: {data['estado']}"
                            )
                            st.session_state["ultimo_id"] = data["analisis_id"]
                            st.badge("Listo", icon=":material/check:", color="green")
                        else:
                            st.error(f"Error: {resp.text}")
                    except Exception as exc:
                        st.error(f"No se pudo conectar con la API: {exc}")

    # ---------------------------------------------------- HISTORIAL
    elif pagina_seleccionada == "Historial":
        st.subheader("Historial de analisis")

        try:
            resp = requests.get(f"{API_BASE}/analisis", timeout=30)
            if resp.status_code == 200:
                items = resp.json()
                if not items:
                    st.info("No hay analisis registrados todavia.")
                else:
                    for item in items:
                        with st.container(border=True):
                            col1, col2, col3 = st.columns([2, 2, 1])
                            with col1:
                                st.markdown(f"**{item['analisis_id']}**")
                                st.caption(f"Fecha: {item['fecha_creacion']}")
                            with col2:
                                estado = item["estado"]
                                color = "green" if estado == "APROBADO" else "orange" if estado == "CON_ERRORES" else "blue"
                                st.badge(estado.replace("_", " ").title(), icon=":material/check_circle:" if estado == "APROBADO" else ":material/schedule:", color=color)
                            with col3:
                                aprobado = "Si" if item["aprobado_humano"] else "No"
                                st.markdown(f"**Aprobado:** {aprobado}")
            else:
                st.error("No se pudo cargar el historial.")
        except Exception as exc:
            st.error(f"Error conectando con la API: {exc}")

    # ---------------------------------------------------- DETALLE
    elif pagina_seleccionada == "Detalle de analisis":
        st.subheader("Detalle y aprobacion (Human-in-the-Loop)")

        analisis_id = st.text_input(
            "ID del analisis",
            value=st.session_state.get("ultimo_id", ""),
            placeholder="Ej: ANAL-00001",
        )

        if st.button("Cargar analisis", type="primary"):
            try:
                resp = requests.get(f"{API_BASE}/analisis/{analisis_id}", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state["ultimo_id"] = analisis_id

                    # Encabezado del detalle
                    col_id, col_estado = st.columns([2, 1])
                    with col_id:
                        st.markdown(f"**ID:** `{analisis_id}`")
                    with col_estado:
                        estado = data["estado"]
                        color = "green" if estado == "APROBADO" else "orange" if estado == "CON_ERRORES" else "blue"
                        st.badge(estado.replace("_", " ").title(), icon=":material/check_circle:" if estado == "APROBADO" else ":material/schedule:", color=color)

                    st.divider()

                    # Texto original
                    with st.expander("Texto original", expanded=False):
                        st.write(data["texto_entrada"])

                    # Tabs para los resultados
                    tab_rf, tab_rnf, tab_inc, tab_cus = st.tabs(
                        ["Requisitos funcionales", "Requisitos no funcionales", "Inconsistencias", "Casos de uso"]
                    )

                    # --- RF
                    with tab_rf:
                        rfs = [r for r in data["requisitos"] if r["tipo"] == "RF"]
                        if rfs:
                            for r in rfs:
                                with st.container(border=True):
                                    c1, c2 = st.columns([3, 1])
                                    with c1:
                                        st.markdown(f"**{r['codigo']}**  —  {r['nombre']}")
                                        st.caption(f"Cita: {r['referencia_texto']}")
                                    with c2:
                                        st.markdown(f"**Actores:** {', '.join(r['actores'])}")
                                    st.write(r["descripcion"])
                        else:
                            st.info("No hay requisitos funcionales.")

                    # --- RNF
                    with tab_rnf:
                        rnfs = [r for r in data["requisitos"] if r["tipo"] == "RNF"]
                        if rnfs:
                            for r in rnfs:
                                with st.container(border=True):
                                    c1, c2 = st.columns([3, 1])
                                    with c1:
                                        st.markdown(f"**{r['codigo']}**  —  {r['nombre']}")
                                        st.caption(f"Categoria ISO: {r['categoria_iso']}")
                                    with c2:
                                        st.markdown(f"**Metrica:** {r['metrica_objetiva']}")
                                        st.caption(f"Umbral: {r['valor_umbral']}")
                                    st.write(r["descripcion"])
                        else:
                            st.info("No hay requisitos no funcionales.")

                    # --- Inconsistencias
                    with tab_inc:
                        incs = data["inconsistencias"]
                        if incs:
                            for inc in incs:
                                sev_color = "red" if inc["severidad"] == "Alta" else "orange" if inc["severidad"] == "Media" else "blue"
                                with st.container(border=True):
                                    st.markdown(
                                        f"**{inc['tipo'].capitalize()}**  —  "
                                        f":{sev_color}-badge[{inc['severidad']}]"
                                    )
                                    st.write(inc["descripcion_problema"])
                                    st.caption(f"Pregunta: {inc['pregunta_clarificacion']}")
                        else:
                            st.info("No se detectaron inconsistencias.")

                    # --- CUS
                    with tab_cus:
                        cus_list = data["casos_de_uso"]
                        if cus_list:
                            for c in cus_list:
                                with st.container(border=True):
                                    st.markdown(f"**{c['codigo']}**  —  {c['nombre']}")
                                    st.caption(f"Actor: {c['actor_principal']}")
                                    with st.expander("Ver flujo principal"):
                                        for paso in c["flujo_principal"]:
                                            st.write(f"• {paso}")
                                    if c["flujos_alternativos"]:
                                        with st.expander("Ver flujos alternativos"):
                                            for alt in c["flujos_alternativos"]:
                                                st.write(f"• {alt}")
                                    if c["postcondiciones"]:
                                        with st.expander("Ver postcondiciones"):
                                            for post in c["postcondiciones"]:
                                                st.write(f"• {post}")
                        else:
                            st.info("No hay casos de uso generados.")

                    st.divider()

                    # Aprobacion humana
                    st.subheader("Aprobacion del analista")
                    comentarios = st.text_area(
                        "Comentarios del analista",
                        height=120,
                        placeholder="Ingrese observaciones o comentarios antes de aprobar...",
                    )
                    col_aprobar, col_spacer = st.columns([1, 4])
                    with col_aprobar:
                        if st.button("Aprobar analisis", type="primary", width="stretch"):
                            try:
                                aprobar_resp = requests.post(
                                    f"{API_BASE}/analisis/{analisis_id}/aprobar",
                                    json={"comentarios": comentarios},
                                    timeout=30,
                                )
                                if aprobar_resp.status_code == 200:
                                    st.success("Analisis aprobado formalmente")
                                    st.badge("Aprobado", icon=":material/check_circle:", color="green")
                                else:
                                    st.error("Error al aprobar")
                            except Exception as exc:
                                st.error(f"Error: {exc}")
                else:
                    st.error("Analisis no encontrado.")
            except Exception as exc:
                st.error(f"Error: {exc}")


if __name__ == "__main__":
    main()