# Tasks 004: Proyectos, Persistencia SQLite, Exportación y Fachada

**Spec:** [spec.md](./spec.md) | **Plan:** [plan.md](./plan.md)  
**Regla TDD:** En cada fase, escribir y verificar en rojo los tests `test_req_XX_*` antes de implementar el código productivo.

---

## Fase 1 — Dependencias (`chore(deps)`)
- [x] Actualizar `repo/pyproject.toml` agregando `sqlalchemy>=2.0.0`, `python-docx>=1.1.0` y `fpdf2>=2.7.0`, e instalarlas en Python 3.12.

---

## Fase 2 — Persistencia SQLite e Inmutabilidad (`feat(persistence)`)
- [x] **Test TDD (`REQ-01`, `REQ-03`, `REQ-04`):** Crear `tests/unit/test_persistence_spec004.py` con:
  - `test_req_01_crea_lista_proyectos_y_asocia_multiples_analisis`
  - `test_req_03_persiste_y_recupera_analisis_entre_instancias_sqlite`
  - `test_req_04_rechaza_sobrescritura_de_analisis_aprobado`
  - `test_req_04_crea_nueva_version_correlativa_manteniendo_original_aprobada`
- [x] **Implementación:** Crear `src/persistence/__init__.py`, `src/persistence/models.py` y `src/persistence/repository.py`.
- [x] Ejecutar `pytest -v` y confirmar Fase 2 en verde.

---

## Fase 3 — Exportación Multiformato (`feat(export)`)
- [x] **Test TDD (`REQ-05`, `REQ-06`):** Crear `tests/unit/test_exportador_spec004.py` con:
  - `test_req_05_rechaza_exportacion_si_reporte_no_esta_aprobado`
  - `test_req_06_exporta_markdown_y_json_con_trazabilidad_completa`
  - `test_req_06_exporta_pdf_y_docx_validos_no_vacios`
- [x] **Implementación:** Crear `src/services/exportador.py`.
- [x] Ejecutar `pytest -v` y confirmar Fase 3 en verde.

---

## Fase 4 — Fachada `OrquestadorService` y E2E (`feat(facade)`)
- [x] **Test TDD (`REQ-01`..`REQ-06`):** Crear `tests/unit/test_orchestrator_spec004.py` con:
  - `test_req_01_fachada_rechaza_proyecto_inexistente_y_soporta_multiples_corridas`
  - `test_req_02_fachada_ejecuta_ciclo_completo_y_consulta_historial`
  - `test_req_04_fachada_bloquea_revision_sobre_aprobado_y_permite_nueva_version`
  - `test_req_05_fachada_bloquea_exportacion_sin_aprobacion`
  - `test_req_06_fachada_e2e_sqlite_exporta_los_cuatro_formatos`
- [x] **Implementación:** Crear `src/services/orchestrator.py`.
- [x] Ejecutar `pytest -v` y confirmar toda la suite en verde.
