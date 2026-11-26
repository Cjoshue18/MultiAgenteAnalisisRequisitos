# Plan Técnico 005: API REST con FastAPI

**Spec de origen:** [spec.md](./spec.md) (Aprobada)  
**Constitución:** [constitution.md](../constitution.md)

---

## 1. Arquitectura y Diseño de Endpoints (`src/api/`)

### 1.1. Dependencias (`pyproject.toml`)
- `fastapi>=0.115.0`, `uvicorn>=0.30.0`, `python-multipart>=0.0.9`.

### 1.2. Modelos de Request/Response (`src/api/schemas.py`)
- `CrearProyectoRequest`: `nombre: str = Field(..., min_length=1)`, `descripcion: str = ""`.
- `IniciarAnalisisTextoRequest`: `proyecto_id: str`, `modalidad_modelado: ModalidadModelado`, `texto: str`.
- Respuestas tipadas reutilizando `ProyectoInfo` y `AnalisisRegistro` de `src/persistence/repository.py`.

### 1.3. Aplicación y Rutas (`src/api/app.py`)
Fábrica `crear_app(servicio: OrquestadorService | None = None) -> FastAPI` (permite inyectar un `OrquestadorService` con cliente mock en pruebas `TestClient`, o instanciar el servicio real desde `Settings`, `RepositorioSQLite` y `SqliteSaver` al ejecutar con `uvicorn src.api.app:app`):
- `GET /health` → `200` `{"status": "ok"}`
- `POST /api/proyectos` → `201` (`ProyectoInfo`)
- `GET /api/proyectos` → `200` (`list[ProyectoInfo]`)
- `GET /api/proyectos/{proyecto_id}` → `200` (`ProyectoInfo`) / `404`
- `POST /api/analisis` (JSON) → `201` (`AnalisisRegistro`) / `404` proyecto / `400` entrada o inyección
- `POST /api/analisis/archivo` (`Form(proyecto_id)`, `Form(modalidad_modelado)`, `archivo: UploadFile`) → guarda archivo temporal con extensión original, invoca `iniciar_analisis(..., ruta_archivo=...)` y limpia temporal en `finally:` → `201`
- `GET /api/analisis` (`?proyecto_id=`) → `200` (`list[AnalisisRegistro]`)
- `GET /api/analisis/{analisis_id}` → `200` (`AnalisisRegistro`) / `404`
- `POST /api/analisis/{analisis_id}/aprobar` (`DecisionRevision`) → `200` / `404` / `409` si `APROBADO` / `400` si cambio de modalidad
- `POST /api/analisis/{analisis_id}/versiones` → `201` / `404` / `409` si no está `APROBADO`
- `GET /api/analisis/{analisis_id}/exportar` (`?formato=md|json|pdf|docx`) → `200` `FileResponse` / `404` / `409` si no está `APROBADO` / `422` formato inválido

---

## 2. Plan de Commits Progresivos ($\le 300$ líneas por commit, 1 dominio)
1. **`docs(specs): agregar spec 005, plan y tareas tdd de api rest`** (`specs/005-api-rest/*`, ~180 líneas).
2. **`chore(deps): agregar fastapi, uvicorn y python-multipart`** (`pyproject.toml`, ~4 líneas).
3. **`feat(api): implementar endpoints rest en fastapi sobre OrquestadorService`** (`src/api/__init__.py`, `src/api/schemas.py`, `src/api/app.py`, ~180 líneas).
4. **`test(api): agregar pruebas tdd de endpoints fastapi con TestClient`** (`tests/unit/test_api_spec005.py`, ~180 líneas).
