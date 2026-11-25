# Tasks 001: Ingesta Dual, Orquestación Multiagente y Revisión Humana (HITL)

**Spec:** [spec.md](./spec.md) | **Plan:** [plan.md](./plan.md)  
**Regla TDD:** En cada fase, escribir y ejecutar en rojo los tests `test_req_XX_*` antes de implementar el código productivo.

---

## Fase 1 — Empaquetado y Configuración (`chore(deps)`)
- [x] Crear `repo/pyproject.toml` con dependencias (`pydantic>=2.0`, `langgraph`, `langgraph-checkpoint-sqlite`, `pypdf`, `pytest`, `pytest-mock`) y `pythonpath = ["."]`.
- [x] Verificar que `pytest -v` descubre y pasa los 10 tests existentes en `tests/unit/test_agentes.py`.

---

## Fase 2 — Contratos SDD y Reducers (`fix(schemas)`)
- [x] **Test TDD (`REQ-03`, `REQ-06`, `REQ-07`, `REQ-08`):** Crear `tests/unit/test_schemas_spec001.py` con:
  - `test_req_03_graph_state_acumula_errores_con_reducer`
  - `test_req_06_inconsistencia_acepta_respuesta_analista_y_decision_revision`
  - `test_req_07_reporte_consolidado_rechaza_estado_no_aprobado`
  - `test_req_08_traza_ejecucion_registra_estado_y_timestamps`
  - Tests de rechazo de strings vacíos en `RequisitoFuncional.actores` y `CasoUso.precondiciones`.
- [x] **Implementación:** Actualizar `src/schemas/contracts.py` (`TextoNoVacio`, `Inconsistencia.respuesta_analista`, `TrazaEjecucion`, `DecisionRevision`, `ReporteConsolidado`, `consolidar_reporte`) y `src/schemas/state.py` (`errores` y `trazas` con `operator.add`, `estado`, `estrategia_ingesta`, `fragmentos`, `respuestas_clarificacion`, `comentarios_analista`, `reporte_consolidado`).
- [x] Ejecutar `pytest -v` y confirmar todos los tests de Fase 2 en verde.

---

## Fase 3 — Ingesta Dual y Límites (`feat(ingesta)`)
- [x] **Test TDD (`REQ-01`, `REQ-02`):** Crear `tests/unit/test_ingesta_spec001.py` cubriendo los escenarios de `spec.md`:
  - `test_req_01_rechaza_entrada_nula_vacia_o_menor_20_caracteres`
  - `test_req_01_rechaza_extension_invalida_exceso_10mb_o_10000_palabras`
  - `test_req_01_extrae_texto_desde_txt_md_y_pdf_mock`
  - `test_req_02_selecciona_estrategia_directa_menor_1000_palabras`
  - `test_req_02_selecciona_estrategia_lotes_con_solapamiento_entre_1000_y_10000_palabras`
- [x] **Implementación:** Crear `src/services/ingesta.py` con validación (`RN01`, `RN02`), lectores `.txt`/`.md`/`.pdf` y patrón Strategy (`EstrategiaDirecta`, `EstrategiaSegmentacion`).
- [x] Ejecutar `pytest -v` y confirmar todos los tests de Fase 3 en verde.

---

## Fase 4 — Resiliencia, Lotes y Compatibilidad en Agentes (`fix(agents)`)
- [x] **Test TDD (`REQ-02`, `REQ-04`, `REQ-05`, `REQ-08`):** Actualizar `tests/unit/test_agentes.py` agregando:
  - `test_req_01_comprobar_texto_maneja_none_sin_crashear`
  - `test_req_02_rf_y_rnf_consolidan_multiples_lotes_sin_duplicados`
  - `test_req_04_inconsistencias_soporta_dicts_de_checkpoint`
  - `test_req_05_cus_genera_preliminar_sin_rf_aprobados_y_prioriza_rf_aprobados`
  - `test_req_08_reintenta_hasta_dos_veces_antes_de_registrar_fallo`
- [x] **Implementación:**
  - Encapsular `configurar_logging` en `src/core/logger.py`.
  - Actualizar `src/agents/common.py` (manejo de `None`, `serializar_elementos`, política de 2 reintentos y retorno de `TrazaEjecucion`).
  - Actualizar `functional_agent.py` y `nonfunctional_agent.py` para iterar sobre `fragmentos` y deduplicar/renumerar salidas.
  - Actualizar `use_case_agent.py` para usar `rf_aprobados or requisitos_funcionales`.
- [x] Ejecutar `pytest -v` y confirmar todos los tests de Fase 4 en verde.

---

## Fase 5 — Grafo LangGraph, Checkpoints y HITL (`feat(graph)`)
- [x] **Test TDD (`REQ-01`..`REQ-08`):** Crear `tests/unit/test_graph_spec001.py` usando cliente mock y checkpointer en memoria:
  - `test_req_01_grafo_rechaza_entrada_invalida_sin_ejecutar_extractores`
  - `test_req_02_grafo_procesa_camino_directo_y_camino_por_lotes`
  - `test_req_03_grafo_acumula_errores_paralelos_de_rf_y_rnf`
  - `test_req_05_grafo_pausa_tras_cuatro_subagentes_y_regenera_cus_si_analista_lo_pide`
  - `test_req_06_grafo_permite_editar_y_responder_preguntas_en_pendiente_aprobacion`
  - `test_req_07_bloquea_reporte_sin_aprobacion_y_sella_estado_aprobado`
  - `test_req_08_detiene_en_fallido_tras_reintentos_y_reanuda_sin_reejecutar_completados`
- [x] **Implementación:** Crear `src/graph/__init__.py` y `src/graph/workflow.py` (`construir_grafo` con `StateGraph`, Fork/Join, router de fallos, `interrupt()` HITL, ciclo explícito `regenerar_cus`, consolidador final y trazas).
- [x] Ejecutar `pytest -v` y verificar suite completa en verde y `git diff --stat` dentro del límite ($\le 300$ líneas por commit).
