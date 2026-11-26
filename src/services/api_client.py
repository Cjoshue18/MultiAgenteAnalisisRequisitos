"""Cliente HTTP mínimo para la interfaz Streamlit (sin dependencia de requests).

Los métodos aceptan y devuelven estructuras JSON; los errores HTTP se traducen
al mensaje legible que devuelve FastAPI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import uuid


class ErrorAPI(RuntimeError):
    """Error de comunicación o respuesta de la API."""


class ClienteAPI:
    def __init__(self, url_base: str = "http://127.0.0.1:8000", timeout: int = 120) -> None:
        self.url_base = url_base.rstrip("/")
        self.timeout = timeout

    def _enviar(self, ruta: str, metodo: str = "GET", datos: Any = None,
                tipo_contenido: str = "application/json") -> Any:
        contenido = None
        if datos is not None:
            contenido = (json.dumps(datos, ensure_ascii=False).encode("utf-8")
                         if tipo_contenido == "application/json" else datos)
        headers = {"Accept": "application/json"}
        if contenido is not None:
            headers["Content-Type"] = tipo_contenido
        solicitud = Request(self.url_base + ruta, data=contenido,
                            headers=headers, method=metodo)
        try:
            with urlopen(solicitud, timeout=self.timeout) as respuesta:
                datos_respuesta = respuesta.read()
                return json.loads(datos_respuesta) if datos_respuesta else None
        except HTTPError as exc:
            cuerpo = exc.read().decode("utf-8", errors="replace")
            try:
                detalle = json.loads(cuerpo).get("detail", cuerpo)
            except ValueError:
                detalle = cuerpo
            if isinstance(detalle, list):
                detalle = "; ".join(str(p.get("msg", p)) if isinstance(p, dict) else str(p)
                                    for p in detalle)
            raise ErrorAPI(f"Error HTTP {exc.code}: {detalle}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ErrorAPI(f"No se pudo conectar con FastAPI ({self.url_base}): {exc}") from exc

    def estado(self) -> dict[str, str]:
        return self._enviar("/health")

    def proyectos(self) -> list[dict]:
        return self._enviar("/api/proyectos")

    def crear_proyecto(self, nombre: str, descripcion: str = "") -> dict:
        return self._enviar("/api/proyectos", "POST", {"nombre": nombre, "descripcion": descripcion})

    def analisis(self, proyecto_id: str | None = None) -> list[dict]:
        params = "?" + urlencode({"proyecto_id": proyecto_id}) if proyecto_id else ""
        return self._enviar("/api/analisis" + params)

    def obtener_analisis(self, analisis_id: str) -> dict:
        return self._enviar(f"/api/analisis/{analisis_id}")

    def iniciar_texto(self, proyecto_id: str, modalidad: str, texto: str) -> dict:
        return self._enviar("/api/analisis", "POST", {
            "proyecto_id": proyecto_id, "modalidad_modelado": modalidad, "texto": texto,
        })

    def iniciar_archivo(self, proyecto_id: str, modalidad: str, nombre: str, contenido: bytes) -> dict:
        """Carga multipart; el servidor valida extensión, tamaño y contenido."""
        if Path(nombre).suffix.lower() not in {".txt", ".md", ".pdf"}:
            raise ErrorAPI("Solo se admiten archivos .txt, .md o .pdf")
        if len(contenido) > 10 * 1024 * 1024:
            raise ErrorAPI("El archivo supera el máximo de 10 MB")
        separador = "----multiagente-" + uuid.uuid4().hex
        fragmentos: list[bytes] = []
        for clave, valor in (("proyecto_id", proyecto_id), ("modalidad_modelado", modalidad)):
            fragmentos.append((f"--{separador}\r\nContent-Disposition: form-data; name=\"{clave}\""
                               f"\r\n\r\n{valor}\r\n").encode("utf-8"))
        # Solo se utiliza el nombre base y se escapan comillas y barras para evitar cabeceras inválidas.
        nombre_seguro = Path(nombre.replace("\\", "/")).name.replace('"', "_").replace("\r", "_").replace("\n", "_")
        mime = "application/pdf" if nombre_seguro.lower().endswith(".pdf") else "text/plain"
        fragmentos.append((f"--{separador}\r\nContent-Disposition: form-data; name=\"archivo\"; "
                           f"filename=\"{nombre_seguro}\"\r\nContent-Type: {mime}\r\n\r\n").encode("utf-8"))
        fragmentos.append(contenido)
        fragmentos.append(f"\r\n--{separador}--\r\n".encode("utf-8"))
        return self._enviar("/api/analisis/archivo", "POST", b"".join(fragmentos),
                            f"multipart/form-data; boundary={separador}")

    def revisar(self, analisis_id: str, decision: dict) -> dict:
        return self._enviar(f"/api/analisis/{analisis_id}/aprobar", "POST", decision)

    def crear_version(self, analisis_id: str) -> dict:
        return self._enviar(f"/api/analisis/{analisis_id}/versiones", "POST", {})

    def exportar(self, analisis_id: str, formato: str) -> bytes:
        if formato not in {"json", "md", "pdf", "docx"}:
            raise ValueError("Formato no compatible")
        req = Request(self.url_base + f"/api/analisis/{analisis_id}/exportar?" + urlencode({"formato": formato}))
        try:
            with urlopen(req, timeout=self.timeout) as respuesta:
                return respuesta.read()
        except HTTPError as exc:
            try:
                detalle = json.loads(exc.read()).get("detail", "Error al exportar")
            except (ValueError, AttributeError):
                detalle = "Error al exportar"
            raise ErrorAPI(f"Error HTTP {exc.code}: {detalle}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ErrorAPI(f"No se pudo descargar el reporte: {exc}") from exc
