# Plan Técnico 003: Adaptadores LLM (Gemini, Groq, NVIDIA), Fallback y Seguridad

**Spec de origen:** [spec.md](./spec.md) (Aprobada)  
**Constitución:** [constitution.md](../constitution.md)

---

## 1. Arquitectura y Decisiones Técnicas

### 1.1. Configuración Externa (`src/core/config.py` y `.env.example`)
- **`pyproject.toml`:** añadir `pydantic-settings>=2.0.0`, `langchain-google-genai>=2.0.0`, `langchain-groq>=0.2.0`, `langchain-openai>=0.2.0` (para NVIDIA NIM vía endpoint compatible OpenAI).
- **`repo/.env.example`:** plantilla sin secretos:
  - `LLM_PROVIDER=auto` (`auto` | `gemini` | `groq` | `nvidia`)
  - `GEMINI_API_KEY=` / `GEMINI_MODEL=gemini-2.0-flash`
  - `GROQ_API_KEY=` / `GROQ_MODEL=llama-3.3-70b-versatile`
  - `NVIDIA_API_KEY=` / `NVIDIA_MODEL=meta/llama-3.1-70b-instruct`
  - `LLM_TIMEOUT_DIRECTA_S=15`
  - `LLM_TIMEOUT_LOTES_S=30`
- **`src/core/config.py`:** `Settings(BaseSettings)` leyendo `.env` y variables de entorno, sin imprimir ni exponer claves en `__repr__` o excepciones (`SecretStr` o enmascarado).

### 1.2. Seguridad Anti-Inyección (`src/services/seguridad.py` + `ingesta.py`)
- **`validar_seguridad_entrada(texto: str) -> str`:**
  - Normaliza texto (minúsculas, sin tildes) y evalúa patrones de *Prompt Injection* (ej. anulación de instrucciones previas, extracción de `system prompt`, suplantación de rol de sistema/desarrollador).
  - Si detecta coincidencia, **rechaza toda la solicitud** lanzando `ValueError("Solicitud rechazada por posible inyección de instrucciones")`.
- **`delimitar_documento(texto: str) -> str`:** envuelve el documento válido entre delimitadores explícitos `<documento_usuario>...</documento_usuario>`.
- Integrar `validar_seguridad_entrada` dentro de `preparar_ingesta` (`src/services/ingesta.py`) para que `nodo_ingesta` bloquee la solicitud antes de despachar `RF || RNF`.

### 1.3. Adaptadores LLM, Fallback y Timeouts (`src/services/llm_client.py` + `agents/`)
- **Puerto `ClienteEstructurado`:** mantiene compatibilidad con `generar(esquema, instrucciones)` y soporta opcionalmente `timeout_s: float | None = None`.
- **`ClienteLangChain`:** inyecta timeout por llamada si está configurado (o en el runnable/modelo) y envuelve `with_structured_output(esquema)`.
- **`ClienteConFallback`:** recibe una secuencia ordenada de proveedores `(nombre, cliente)`. Si el proveedor actual falla por cuota (`429`), indisponibilidad (`503`), conexión o `TimeoutError`, registra el evento de conmutación en `eventos_fallback` y pasa al siguiente; si todos fallan, lanza `RuntimeError` resumiendo todos los fallos.
- **`crear_cliente_llm(settings: Settings) -> ClienteEstructurado`:** fábrica hexagonal:
  - En modo `auto`: construye la cadena con los proveedores que tengan API key configurada en el orden `gemini` → `groq` → `nvidia` (rechaza con `ValueError` si no hay ninguna key).
  - En modo específico (`gemini` | `groq` | `nvidia`): exige la API key de ese proveedor o lanza `ValueError` indicando exactamente cuál falta.
- **Timeouts por estrategia en `src/agents/`:**
  - `src/agents/common.py` calcula `timeout_s = 30.0` si `len(fragmentos) > 1` (o `estrategia_ingesta == "lotes"`), y `15.0` si es estrategia directa, pasándolo de forma segura solo si el cliente acepta `timeout_s` (para mantener compatibilidad con mocks simples).

---

## 2. Plan de Commits Progresivos ($\le 300$ líneas por commit, 1 dominio)
1. **`chore(deps): agregar pydantic-settings, proveedores llm y .env.example`** (`pyproject.toml`, `.env.example`, ~35 líneas).
2. **`feat(config): cargar configuracion externa y credenciales sin secretos`** (`src/core/config.py`, `tests/unit/test_config_spec003.py`, ~95 líneas).
3. **`feat(security): rechazar inyeccion de prompts y delimitar entradas`** (`src/services/seguridad.py`, `src/services/ingesta.py`, `tests/unit/test_seguridad_spec003.py`, ~120 líneas).
4. **`feat(llm): implementar adaptadores, fallback y timeouts por estrategia`** (`src/services/llm_client.py`, `src/agents/common.py`, `src/agents/functional_agent.py`, `src/agents/nonfunctional_agent.py`, `tests/unit/test_llm_spec003.py`, ~220 líneas).

---

## 3. Verificación
- Suite completa `pytest -v` con mocks (cero llamadas de red en `tests/unit/`).
- Opcional al finalizar: script/comando de *smoke test* manual usando `repo/.env` con tus API keys gratuitas (Gemini, Groq, NVIDIA).
