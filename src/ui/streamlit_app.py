import streamlit as st
import requests
from typing import Dict, Any

API_BASE = "http://localhost:8000/api"


def main() -> None:
    st.set_page_config(page_title="Analisis de Requisitos - Multiagente", layout="wide")
    st.title("Sistema Multiagente de Analisis de Requisitos")
    st.markdown("Grupo 6  |  Arquitectura y Evolucion de Software (2026-2)")

    menu = st.sidebar.radio("Navegacion", ["Nuevo Analisis", "Historial", "Detalle de Analisis"])

    if menu == "Nuevo Analisis":
        st.subheader("Ingresar solicitud de analisis")
        texto = st.text_area(
            "Descripcion de requisitos (lenguaje natural)",
            height=250,
            placeholder="Ej: Necesito un sistema para una biblioteca universitaria donde los alumnos puedan consultar libros...",
        )
        if st.button("Analizar", type="primary"):
            if len(texto.strip()) < 20:
                st.error("El texto debe tener al menos 20 caracteres.")
            else:
                with st.spinner("Ejecutando pipeline multiagente..."):
                    try:
                        resp = requests.post(f"{API_BASE}/analisis", json={"texto": texto}, timeout=120)
                        if resp.status_code == 202:
                            data = resp.json()
                            st.success(f"Analisis iniciado: {data['analisis_id']} - Estado: {data['estado']}")
                            st.session_state["ultimo_id"] = data["analisis_id"]
                        else:
                            st.error(f"Error: {resp.text}")
                    except Exception as exc:
                        st.error(f"No se pudo conectar con la API: {exc}")

    elif menu == "Historial":
        st.subheader("Historial de analisis")
        try:
            resp = requests.get(f"{API_BASE}/analisis", timeout=30)
            if resp.status_code == 200:
                for item in resp.json():
                    with st.expander(f"{item['analisis_id']} - {item['estado']}"):
                        st.write(f"Fecha: {item['fecha_creacion']}")
                        st.write(f"Aprobado: {'Si' if item['aprobado_humano'] else 'No'}")
            else:
                st.error("No se pudo cargar el historial")
        except Exception as exc:
            st.error(f"Error conectando con la API: {exc}")

    elif menu == "Detalle de Analisis":
        st.subheader("Detalle y aprobacion (Human-in-the-Loop)")
        analisis_id = st.text_input("ID del analisis", value=st.session_state.get("ultimo_id", ""))
        if st.button("Cargar"):
            try:
                resp = requests.get(f"{API_BASE}/analisis/{analisis_id}", timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    st.write(f"**Estado:** {data['estado']}")
                    st.write(f"**Texto original:** {data['texto_entrada'][:200]}...")

                    st.markdown("### Requisitos Funcionales")
                    for r in data["requisitos"]:
                        if r["tipo"] == "RF":
                            st.markdown(f"- **{r['codigo']}**: {r['descripcion']}  (Actores: {', '.join(r['actores'])})")

                    st.markdown("### Requisitos No Funcionales (ISO 25010)")
                    for r in data["requisitos"]:
                        if r["tipo"] == "RNF":
                            st.markdown(f"- **{r['codigo']}** [{r['categoria_iso']}]: {r['descripcion']}  Metrica: {r['metrica_objetiva']}")

                    st.markdown("### Inconsistencias")
                    for inc in data["inconsistencias"]:
                        st.markdown(f"- [{inc['severidad']}] {inc['descripcion_problema']}")
                        st.markdown(f"  *Pregunta:* {inc['pregunta_clarificacion']}")

                    st.markdown("### Casos de Uso")
                    for c in data["casos_de_uso"]:
                        st.markdown(f"- **{c['codigo']}**: {c['nombre']} (Actor: {c['actor_principal']})")

                    comentarios = st.text_area("Comentarios del analista", key="comentarios")
                    if st.button("Aprobar Analisis"):
                        aprobar_resp = requests.post(
                            f"{API_BASE}/analisis/{analisis_id}/aprobar",
                            json={"comentarios": comentarios},
                            timeout=30,
                        )
                        if aprobar_resp.status_code == 200:
                            st.success("Analisis aprobado formalmente")
                        else:
                            st.error("Error al aprobar")
                else:
                    st.error("Analisis no encontrado")
            except Exception as exc:
                st.error(f"Error: {exc}")


if __name__ == "__main__":
    main()
