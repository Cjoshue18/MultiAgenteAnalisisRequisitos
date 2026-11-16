# Sistema Multiagente de Analisis de Requisitos de Software

Implementacion de una solucion de software basada en una arquitectura multiagente de inteligencia artificial para el curso Arquitectura y Evolucion de Software (2026-2) - Grupo 6.

## Estructura del proyecto

```
src/
  core/           # Configuracion, logging y settings
  schemas/        # Modelos Pydantic v2 (contratos SDD)
  agents/         # Subagentes especializados (RF, RNF, Inconsistencias, CUS)
  graph/          # Grafo de estados LangGraph (StateGraph)
  services/       # Clientes LLM y servicios externos
  api/            # Endpoints REST FastAPI
  ui/             # Interfaz Streamlit (Human-in-the-Loop)
  persistence/    # Capa de datos SQLite + SQLAlchemy
tests/
  unit/           # Pruebas unitarias con mocks (TDD)
  fixtures/       # Datos estaticos para tests
```

## Reglas de desarrollo

- **SDD (Specification-Driven Development):** Definir primero los modelos Pydantic y el `GraphState` antes de escribir logica o prompts.
- **TDD (Test-Driven Development):** Pruebas unitarias con `unittest.mock` / `pytest-mock`. Cero llamadas a APIs reales de LLM en `tests/unit/`.
- **Structured Outputs:** Todo subagente fuerza salidas estructuradas con `with_structured_output(ModeloPydantic)`.
- **Tipado estricto:** Python 3.11+ con `list[str]`, `str | None`, etc.
- **Seguridad:** Nunca hardcodear API keys; usar `pydantic-settings` + `.env`.

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -e .
cp .env.example .env   # editar con tu GEMINI_API_KEY
```

## Ejecucion

API (FastAPI + Uvicorn):
```bash
uvicorn src.api.main:app --reload
```

Frontend (Streamlit):
```bash
streamlit run src/ui/streamlit_app.py
```

## Pruebas

```bash
pytest tests/unit/
```
