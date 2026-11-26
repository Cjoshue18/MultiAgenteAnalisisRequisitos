# Tasks 005: API REST con FastAPI

**Spec:** [spec.md](./spec.md) | **Plan:** [plan.md](./plan.md)  
**Regla TDD:** Escribir y verificar en rojo los tests `test_req_XX_*` antes de implementar `src/api/`.

---

## Fase 1 — Dependencias (`chore(deps)`)
- [x] Actualizar `repo/pyproject.toml` agregando `fastapi>=0.115.0`, `uvicorn>=0.30.0` y `python-multipart>=0.0.9`, e instalarlas en Python 3.12.

---

## Fase 2 — Pruebas TDD de la API (`test(api)`)
- [x] **Test TDD (`REQ-01`..`REQ-07`):** Crear `tests/unit/test_api_spec005.py` usando `TestClient` y `OrquestadorService` con mock LLM:
  - `test_req_01_proyectos_crear_listar_consultar_y_rechazar_vacio`
  - `test_req_02_iniciar_analisis_por_texto_y_archivo_y_errores_4xx`
  - `test_req_03_listar_historial_por_proyecto_y_detalle_404`
  - `test_req_04_aprobar_rechazar_cambio_modalidad_y_conflicto_409`
  - `test_req_05_crear_nueva_version_desde_aprobado`
  - `test_req_06_exportar_bloqueado_409_y_descarga_cuatro_formatos`
  - `test_req_07_health_y_openapi_disponibles`

---

## Fase 3 — Implementación FastAPI (`feat(api)`)
- [x] Crear `src/api/__init__.py`, `src/api/schemas.py` y `src/api/app.py` (`crear_app`, rutas `/health`, `/api/proyectos`, `/api/analisis`, `/api/analisis/archivo`, `/aprobar`, `/versiones`, `/exportar` y mapeo de errores `400`/`404`/`409`).
- [x] Ejecutar `pytest -v` y confirmar toda la suite en verde.
