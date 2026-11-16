from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.graph.arch_graph import ejecutar_analisis
from src.persistence.database import SessionLocal, get_db
from src.persistence.repository import AnalisisRepository
from src.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class AnalisisEntrada(BaseModel):
    texto: str


class AnalisisRespuesta(BaseModel):
    analisis_id: str
    estado: str


class AprobacionEntrada(BaseModel):
    comentarios: Optional[str] = None


@router.post("/analisis", response_model=AnalisisRespuesta, status_code=202)
def iniciar_analisis(entrada: AnalisisEntrada, db: Session = Depends(get_db)) -> Any:
    """Recibe la descripcion textual y lanza el pipeline multiagente."""
    if not entrada.texto or len(entrada.texto.strip()) < 20:
        raise HTTPException(status_code=400, detail="Texto insuficiente (minimo 20 caracteres)")

    repo = AnalisisRepository(db)
    analisis = repo.crear_analisis(
        analisis_id=f"ANAL-{abs(hash(entrada.texto)) % 100000:05d}",
        texto_entrada=entrada.texto,
    )

    try:
        estado = ejecutar_analisis(entrada.texto)
        errores = estado.get("errores", [])

        # Persistir RF
        for rf in estado.get("requisitos_funcionales", []):
            repo.guardar_requisito(analisis.analisis_id, {
                "tipo": "RF",
                "id": rf.id,
                "nombre": rf.nombre,
                "descripcion": rf.descripcion,
                "actores": rf.actores,
                "referencia_texto": rf.referencia_texto,
            })

        # Persistir RNF
        for rnf in estado.get("requisitos_no_funcionales", []):
            repo.guardar_requisito(analisis.analisis_id, {
                "tipo": "RNF",
                "id": rnf.id,
                "nombre": rnf.categoria_iso,
                "descripcion": rnf.descripcion,
                "categoria_iso": rnf.categoria_iso,
                "metrica_objetiva": rnf.metrica_objetiva,
                "valor_umbral": rnf.valor_umbral,
                "referencia_texto": "",
            })

        # Persistir inconsistencias
        for inc in estado.get("inconsistencias", []):
            repo.guardar_inconsistencia(analisis.analisis_id, {
                "tipo": inc.tipo,
                "severidad": inc.severidad,
                "elementos_afectados": inc.elementos_afectados,
                "descripcion_problema": inc.descripcion_problema,
                "pregunta_clarificacion": inc.pregunta_clarificacion,
            })

        # Persistir CUS
        for cus in estado.get("casos_de_uso", []):
            repo.guardar_caso_uso(analisis.analisis_id, {
                "id": cus.id,
                "nombre": cus.nombre,
                "actor_principal": cus.actor_principal,
                "precondiciones": cus.precondiciones,
                "flujo_principal": cus.flujo_principal,
                "flujos_alternativos": cus.flujos_alternativos,
                "postcondiciones": cus.postcondiciones,
            })

        estado_final = "APROBADO" if not errores else "CON_ERRORES"
        repo.actualizar_estado(analisis.analisis_id, estado_final)

        return {"analisis_id": analisis.analisis_id, "estado": estado_final}
    except Exception as exc:
        logger.error("Error en endpoint /analisis: %s", str(exc))
        repo.actualizar_estado(analisis.analisis_id, "ERROR")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/analisis/{analisis_id}")
def consultar_analisis(analisis_id: str, db: Session = Depends(get_db)) -> Any:
    """Devuelve el estado y resultados de un analisis."""
    repo = AnalisisRepository(db)
    obj = repo.obtener_analisis(analisis_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Analisis no encontrado")

    return {
        "analisis_id": obj.analisis_id,
        "estado": obj.estado,
        "texto_entrada": obj.texto_entrada,
        "comentarios_analista": obj.comentarios_analista,
        "aprobado_humano": bool(obj.aprobado_humano),
        "requisitos": [
            {
                "codigo": r.codigo,
                "tipo": r.tipo,
                "nombre": r.nombre,
                "descripcion": r.descripcion,
                "actores": r.actores,
                "categoria_iso": r.categoria_iso,
                "metrica_objetiva": r.metrica_objetiva,
                "valor_umbral": r.valor_umbral,
                "referencia_texto": r.referencia_texto,
            }
            for r in obj.requisitos
        ],
        "inconsistencias": [
            {
                "tipo": i.tipo,
                "severidad": i.severidad,
                "elementos_afectados": i.elementos_afectados,
                "descripcion_problema": i.descripcion_problema,
                "pregunta_clarificacion": i.pregunta_clarificacion,
            }
            for i in obj.inconsistencias
        ],
        "casos_de_uso": [
            {
                "codigo": c.codigo,
                "nombre": c.nombre,
                "actor_principal": c.actor_principal,
                "precondiciones": c.precondiciones,
                "flujo_principal": c.flujo_principal,
                "flujos_alternativos": c.flujos_alternativos,
                "postcondiciones": c.postcondiciones,
            }
            for c in obj.casos_uso
        ],
    }


@router.post("/analisis/{analisis_id}/aprobar")
def aprobar_analisis(analisis_id: str, entrada: AprobacionEntrada, db: Session = Depends(get_db)) -> Any:
    """Registra la aprobacion humana y sella el reporte."""
    repo = AnalisisRepository(db)
    obj = repo.actualizar_estado(
        analisis_id,
        estado="APROBADO",
        comentarios=entrada.comentarios,
        aprobado=True,
    )
    if not obj:
        raise HTTPException(status_code=404, detail="Analisis no encontrado")
    return {"analisis_id": obj.analisis_id, "estado": obj.estado, "aprobado": True}


@router.get("/analisis")
def listar_analisis(db: Session = Depends(get_db)) -> Any:
    """Retorna el historial de analisis registrados."""
    repo = AnalisisRepository(db)
    items = repo.listar_analisis()
    return [
        {
            "analisis_id": a.analisis_id,
            "estado": a.estado,
            "fecha_creacion": a.fecha_creacion.isoformat() if a.fecha_creacion else None,
            "aprobado_humano": bool(a.aprobado_humano),
        }
        for a in items
    ]
