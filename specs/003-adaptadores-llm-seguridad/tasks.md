# Tasks 003: Adaptadores LLM, Fallback y Seguridad de Entrada

**Spec:** [spec.md](./spec.md) | **Plan:** [plan.md](./plan.md)  
**Regla TDD:** En cada fase, escribir y verificar en rojo los tests `test_req_XX_*` antes de implementar el código productivo.

---

## Fase 1 — Dependencias y Plantilla de Entorno (`chore(deps)`)
- [x] Actualizar `repo/pyproject.toml` agregando `pydantic-settings`, `langchain-google-genai`, `langchain-groq` y `langchain-openai`.
- [x] Crear `repo/.env.example` documentando `LLM_PROVIDER`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `NVIDIA_API_KEY`, `LLM_TIMEOUT_DIRECTA_S=15` y `LLM_TIMEOUT_LOTES_S=30`.

---

## Fase 2 — Configuración Externa Segura (`feat(config)`)
- [x] **Test TDD (`REQ-01`, `REQ-04`):** Crear `tests/unit/test_config_spec003.py` con:
  - `test_req_01_settings_carga_valores_desde_env_y_oculta_secretos`
  - `test_req_01_rechaza_inicializacion_sin_credenciales_para_proveedor_elegido`
  - `test_req_04_settings_define_timeouts_15_directa_y_30_lotes`
- [x] **Implementación:** Crear `src/core/config.py` (`Settings` con `SecretStr` y `obtener_settings`).
- [x] Ejecutar `pytest -v` y confirmar Fase 2 en verde.

---

## Fase 3 — Protección Anti-Inyección (`feat(security)`)
- [x] **Test TDD (`REQ-05`):** Crear `tests/unit/test_seguridad_spec003.py` con:
  - `test_req_05_rechaza_solicitud_con_prompt_injection_sin_llamar_llm`
  - `test_req_05_acepta_texto_legitimo_y_delimita_como_datos_pasivos`
  - `test_req_05_grafo_detiene_en_fallido_si_detecta_inyeccion`
- [x] **Implementación:** Crear `src/services/seguridad.py` (`validar_seguridad_entrada`, `delimitar_documento`) e integrar en `src/services/ingesta.py` (`preparar_ingesta`).
- [x] Ejecutar `pytest -v` y confirmar Fase 3 en verde.

---

## Fase 4 — Adaptadores LLM, Fallback y Timeouts (`feat(llm)`)
- [x] **Test TDD (`REQ-02`, `REQ-03`, `REQ-04`):** Crear `tests/unit/test_llm_spec003.py` con:
  - `test_req_02_fabrica_alterna_proveedor_segun_configuracion`
  - `test_req_03_fallback_conmuta_de_primario_a_respaldo_ante_429_o_timeout`
  - `test_req_03_fallback_propaga_errores_de_todos_los_proveedores_si_todos_fallan`
  - `test_req_04_agentes_aplican_timeout_15s_en_directa_y_30s_en_lotes`
  - `test_req_04_cliente_aborta_llamada_que_supera_timeout_configurado`
- [x] **Implementación:**
  - Actualizar `src/services/llm_client.py` (`ClienteLangChain` con timeout, `ClienteConFallback`, `crear_cliente_llm` para Gemini/Groq/NVIDIA).
  - Actualizar `src/agents/common.py`, `functional_agent.py` y `nonfunctional_agent.py` para enviar `timeout_s` según estrategia (`15s` directa / `30s` lotes) y delimitación pasiva.
- [x] Ejecutar `pytest -v` y confirmar toda la suite en verde (cero llamadas de red en `tests/unit/`).
