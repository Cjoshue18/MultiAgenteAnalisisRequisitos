import logging
from fastapi import FastAPI
from src.api.routes import router

# Silenciar logs ruidosos de uvicorn.access para ciertos endpoints
class _NoiseFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return "/v1/models" not in msg


logging.getLogger("uvicorn.access").addFilter(_NoiseFilter())

app = FastAPI(
    title="Sistema Multiagente de Analisis de Requisitos",
    version="1.0.0",
    description="Orquestador LangGraph con subagentes RF, RNF, Inconsistencias y CUS",
)

app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
