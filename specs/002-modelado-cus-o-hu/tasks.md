# Tasks 002: Selección Previa y Modelado en CUS, HU o Ambos

**Spec:** [spec.md](./spec.md) | **Plan:** [plan.md](./plan.md)  
**Regla TDD:** En cada fase, escribir y verificar en rojo los tests `test_req_XX_*` antes de implementar el código productivo.

---

## Fase 1 — Contratos `HU`, `AMBOS` y Modalidad Fija (`fix(schemas)`)
- [x] **Test TDD (`REQ-04`, `REQ-05`, `REQ-06`):** Crear `tests/unit/test_schemas_spec002.py` con:
  - `test_req_04_historia_usuario_valida_narrativa_y_criterios_dado_cuando_entonces`
  - `test_req_04_rechaza_hu_sin_criterios_o_narrativa_incompleta`
  - `test_req_05_validar_decision_revision_rechaza_cambio_de_modalidad`
  - `test_req_06_consolidar_reporte_preserva_modalidad_e_historias_aprobadas`
- [x] **Implementación:** Actualizar `src/schemas/contracts.py` (`ModalidadModelado`, `CriterioAceptacion`, `HistoriaUsuario`, `SalidaHU`, `DecisionRevision`, `ReporteConsolidado`, `consolidar_reporte`, `validar_decision_revision`) y `src/schemas/state.py` (`modalidad_modelado`, `historias_usuario`, `advertencias`).
- [x] Ejecutar `pytest -v` y confirmar Fase 1 en verde.

---

## Fase 2 — Validación Previa y Advertencias (`feat(ingesta)`)
- [x] **Test TDD (`REQ-01`):** Crear `tests/unit/test_ingesta_spec002.py` con:
  - `test_req_01_rechaza_modalidad_nula_o_invalida`
  - `test_req_01_cus_y_hu_emiten_advertencia_de_modalidad_fija`
  - `test_req_01_ambos_emite_advertencia_fija_y_mayor_demora`
- [x] **Implementación:** Agregar `validar_modalidad_modelado` en `src/services/ingesta.py`.
- [x] Ejecutar `pytest -v` y confirmar Fase 2 en verde.

---

## Fase 3 — Subagente 4 Configurable `CUS` / `HU` / `AMBOS` (`feat(agents)`)
- [x] **Test TDD (`REQ-02`, `REQ-03`, `REQ-04`):** Crear `tests/unit/test_agentes_spec002.py` con:
  - `test_req_02_modelado_cus_genera_solo_cus_y_cero_hu`
  - `test_req_02_modelado_hu_genera_solo_hu_y_cero_cus`
  - `test_req_02_modelado_ambos_genera_cus_y_hu`
  - `test_req_03_y_req_04_modelado_prioriza_rf_aprobados_al_regenerar`
- [x] **Implementación:** Agregar `nodo_historias_usuario` y `nodo_modelado` en `src/agents/use_case_agent.py`.
- [x] Ejecutar `pytest -v` y confirmar Fase 3 en verde.

---

## Fase 4 — Orquestación LangGraph y Bloqueo en HITL (`feat(graph)`)
- [x] **Test TDD (`REQ-01`, `REQ-02`, `REQ-05`, `REQ-06`):**
  - Actualizar llamadas base en `tests/unit/test_graph_spec001.py` para incluir `"modalidad_modelado": "CUS"` (alineado a `REQ-01` de Spec 002).
  - Crear `tests/unit/test_graph_spec002.py` con:
    - `test_req_01_grafo_rechaza_envio_sin_modalidad_y_guarda_advertencias_en_ambos`
    - `test_req_02_grafo_genera_exclusivamente_hu_cuando_se_elige_hu`
    - `test_req_02_grafo_genera_cus_y_hu_cuando_se_elige_ambos`
    - `test_req_05_grafo_rechaza_cambio_modalidad_en_hitl_y_regenera_en_modalidad_original`
    - `test_req_06_grafo_e2e_sqlite_consolida_reporte_inmutable_con_modalidad_ambos`
- [x] **Implementación:** Actualizar `src/graph/workflow.py` (`nodo_ingesta` validando modalidad + `advertencias`, `nodo_modelado`, `nodo_revision_humana` con `validar_decision_revision` y `hu_editadas`, `nodo_consolidador` preservando `modalidad_modelado` y `historias_usuario`).
- [x] Ejecutar `pytest -v` y verificar toda la suite (Spec 001 + Spec 002) en verde.
