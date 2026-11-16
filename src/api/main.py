from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(
    title="Sistema Multiagente de Analisis de Requisitos",
    version="1.0.0",
    description="Orquestador LangGraph con subagentes RF, RNF, Inconsistencias y CUS",
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
