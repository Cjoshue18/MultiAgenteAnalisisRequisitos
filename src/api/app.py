from pathlib import Path
import sqlite3
import tempfile
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from langgraph.checkpoint.sqlite import SqliteSaver
from src.api.schemas import CrearProyectoRequest, IniciarAnalisisTextoRequest
from src.core.config import Settings
from src.persistence.repository import AnalisisRegistro, ProyectoInfo, RepositorioSQLite
from src.schemas.contracts import DecisionRevision, ModalidadModelado
from src.services.exportador import FormatoExportacion
from src.services.llm_client import crear_cliente_llm
from src.services.orchestrator import OrquestadorService

_MEDIA_TYPES: dict[FormatoExportacion, str] = {
    "md": "text/markdown; charset=utf-8",
    "json": "application/json",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _http_desde_value_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    msg_low = msg.lower()
    if "no encontrado" in msg_low or "inexistente" in msg_low:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
    if "inmutable" in msg_low or "aprobado" in msg_low:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


def _crear_servicio_por_defecto() -> OrquestadorService:
    settings = Settings()
    cliente = crear_cliente_llm(settings)
    repo = RepositorioSQLite("sqlite:///analisis.db")
    conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return OrquestadorService(cliente, repo, saver, Path("reportes"))


def crear_app(servicio: OrquestadorService | None = None) -> FastAPI:
    """Construye la aplicación FastAPI desacoplada vía OrquestadorService."""
    fastapi_app = FastAPI(
        title="MultiAgente Análisis de Requisitos API",
        version="0.1.0",
        description="API REST para proyectos, análisis multiagente (CUS/HU/AMBOS), HITL y exportación.",
    )
    estado_srv: dict[str, OrquestadorService | None] = {"instancia": servicio}

    def obtener_servicio() -> OrquestadorService:
        if estado_srv["instancia"] is None:
            estado_srv["instancia"] = _crear_servicio_por_defecto()
        return estado_srv["instancia"]

    @fastapi_app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @fastapi_app.post("/api/proyectos", response_model=ProyectoInfo, status_code=status.HTTP_201_CREATED)
    def crear_proyecto(
        body: CrearProyectoRequest,
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> ProyectoInfo:
        try:
            return srv.crear_proyecto(body.nombre, body.descripcion)
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc

    @fastapi_app.get("/api/proyectos", response_model=list[ProyectoInfo])
    def listar_proyectos(srv: OrquestadorService = Depends(obtener_servicio)) -> list[ProyectoInfo]:
        return srv.listar_proyectos()

    @fastapi_app.get("/api/proyectos/{proyecto_id}", response_model=ProyectoInfo)
    def obtener_proyecto(
        proyecto_id: str,
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> ProyectoInfo:
        try:
            return srv.repositorio.obtener_proyecto(proyecto_id)
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc

    @fastapi_app.post("/api/analisis", response_model=AnalisisRegistro, status_code=status.HTTP_201_CREATED)
    def iniciar_analisis_texto(
        body: IniciarAnalisisTextoRequest,
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> AnalisisRegistro:
        try:
            registro = srv.iniciar_analisis(body.proyecto_id, body.modalidad_modelado, texto=body.texto)
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc
        if registro.estado == "FALLIDO" and not registro.requisitos_funcionales:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(registro.errores))
        return registro

    @fastapi_app.post("/api/analisis/archivo", response_model=AnalisisRegistro, status_code=status.HTTP_201_CREATED)
    def iniciar_analisis_archivo(
        proyecto_id: str = Form(...),
        modalidad_modelado: ModalidadModelado = Form(...),
        archivo: UploadFile = File(...),
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> AnalisisRegistro:
        sufijo = Path(archivo.filename or "entrada.txt").suffix or ".txt"
        with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
            tmp.write(archivo.file.read())
            ruta_tmp = Path(tmp.name)
        try:
            registro = srv.iniciar_analisis(proyecto_id, modalidad_modelado, ruta_archivo=ruta_tmp)
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc
        finally:
            ruta_tmp.unlink(missing_ok=True)
        if registro.estado == "FALLIDO" and not registro.requisitos_funcionales:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="; ".join(registro.errores))
        return registro

    @fastapi_app.get("/api/analisis", response_model=list[AnalisisRegistro])
    def listar_analisis(
        proyecto_id: str | None = Query(default=None),
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> list[AnalisisRegistro]:
        return srv.listar_analisis(proyecto_id=proyecto_id)

    @fastapi_app.get("/api/analisis/{analisis_id}", response_model=AnalisisRegistro)
    def obtener_analisis(
        analisis_id: str,
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> AnalisisRegistro:
        try:
            return srv.obtener_analisis(analisis_id)
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc

    @fastapi_app.post("/api/analisis/{analisis_id}/aprobar", response_model=AnalisisRegistro)
    def revisar_o_aprobar(
        analisis_id: str,
        decision: DecisionRevision,
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> AnalisisRegistro:
        try:
            return srv.enviar_revision(analisis_id, decision)
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc

    @fastapi_app.post(
        "/api/analisis/{analisis_id}/versiones",
        response_model=AnalisisRegistro,
        status_code=status.HTTP_201_CREATED,
    )
    def crear_nueva_version(
        analisis_id: str,
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> AnalisisRegistro:
        try:
            return srv.crear_nueva_version(analisis_id)
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc

    @fastapi_app.get("/api/analisis/{analisis_id}/exportar")
    def exportar_analisis(
        analisis_id: str,
        formato: FormatoExportacion = Query(default="md"),
        srv: OrquestadorService = Depends(obtener_servicio),
    ) -> FileResponse:
        try:
            rutas = srv.exportar_analisis(analisis_id, [formato])
        except ValueError as exc:
            raise _http_desde_value_error(exc) from exc
        ruta = rutas[formato]
        return FileResponse(path=str(ruta), media_type=_MEDIA_TYPES[formato], filename=ruta.name)

    return fastapi_app


app = crear_app()
