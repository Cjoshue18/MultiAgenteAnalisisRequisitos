# AGENTS.md - Sistema Multiagente de Análisis de Requisitos

Guía operativa para agentes de IA en este repositorio.

---

## 1. Propósito del Sistema

Sistema multiagente inteligente que recibe especificaciones textuales o historias de usuario en lenguaje natural y genera un análisis formal de requisitos:
- **Requisitos Funcionales (RF):** Atómicos, con actores y citas del texto original.
- **Requisitos No Funcionales (RNF):** Atributos de calidad clasificados bajo **ISO/IEC 25010** con métricas objetivas cuantificables.
- **Inconsistencias y Ambigüedades:** Detección de vacíos, contradicciones y formulación de preguntas de clarificación.
- **Casos de Uso (CUS):** Especificación formal derivada de los RF aprobados (actores, precondiciones, flujo principal, alternativos y postcondiciones).

---

## 2. Metodología: SDD + TDD

El desarrollo del proyecto es **Specification-Driven Development (SDD)** guiado por contratos y **Test-Driven Development (TDD)** con mocks.

```
 [ 1. ESPECIFICACIÓN ]           [ 2. PRUEBA UNITARIA ]        [ 3. IMPLEMENTACIÓN ]
  Modelos Pydantic en     ──►     Test unitario con      ──►    Nodo en LangGraph con
  schemas (contratos)             mocks/fixtures JSON           salida estructurada
```

### Reglas Clave:
1. **Spec First:** Definir primero los modelos Pydantic del contrato y las claves del `GraphState` antes de escribir cualquier lógica o prompt.
2. **TDD con Mocks (Cero llamadas de red en tests):** Las pruebas unitarias **nunca** llaman a APIs reales de LLM. Se prueban transiciones de estado, validación de esquemas y fallbacks usando `unittest.mock` / `pytest-mock` y datos estáticos.
3. **Structured Outputs:** Todo subagente debe forzar salidas estructuradas (`with_structured_output`) ligadas a su modelo Pydantic.

---

## 3. Stack Tecnológico

- **Lenguaje:** Python 3.11+ (tipado estricto con `typing` y Pydantic v2)
- **Orquestación Multiagente:** LangGraph (`StateGraph`, paralelismo y checkpoints)
- **Modelos LLM:** Google Gemini API / Groq (Llama 3)
- **Backend API:** FastAPI
- **Persistencia:** SQLite (SQLModel / SQLAlchemy)
- **Frontend:** Streamlit
- **Testing:** pytest (pytest-mock, pytest-asyncio)

---

## 4. Topología y Pipeline de Agentes

El flujo en el `StateGraph` de LangGraph sigue esta secuencia obligatoria:

```
                     ┌────────────────────────┐
                     │   Agente Orquestador   │
                     │  (Supervisor / State)  │
                     └───────────┬────────────┘
                                 │
                     ┌───────────┴───────────┐
                     │ (Fork Concurrente)    │
                     ▼                       ▼
            ┌─────────────────┐     ┌─────────────────┐
            │   Subagente 1   │     │   Subagente 2   │
            │ Requisitos Func.│     │ Requisitos No F.│
            │     (RF-xx)     │     │ (ISO/IEC 25010) │
            └────────┬────────┘     └────────┬────────┘
                     │                       │
                     └───────────┬───────────┘
                                 │ (Join / Sincronización)
                                 ▼
                     ┌─────────────────────────┐
                     │       Subagente 3       │
                     │    Inconsistencias y    │
                     │      Ambigüedades       │
                     └───────────┬─────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │       Subagente 4       │
                     │   Casos de Uso (CUS-xx) │
                     │  (Basado en RF limpios) │
                     └───────────┬─────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────┐
                     │  Consolidación Final y  │
                     │  Revisión (Streamlit)   │
                     └─────────────────────────┘
```

### Responsabilidades por Nodo:
1. **Orquestador:** Valida la entrada, inicializa `GraphState`, coordina bifurcaciones/uniones y ensambla el reporte final.
2. **Subagente 1 (RF):** Extrae requerimientos funcionales atómicos (`RF-xx`), actores y reglas.
3. **Subagente 2 (RNF):** Extrae y categoriza bajo ISO/IEC 25010 asignando métricas objetivas (`RNF-xx`).
4. **Subagente 3 (Inconsistencias):** Cruza entrada vs RF y RNF; detecta contradicciones, ambigüedades y genera preguntas al usuario.
5. **Subagente 4 (Casos de Uso):** Genera casos de uso (`CUS-xx`) estructurados con flujo principal y alternativo a partir de los RF ya depurados.

---

## 5. Convención Obligatoria de Commits

Todo commit en este repositorio debe seguir estrictamente el siguiente formato:

```text
prefijo(contexto): descripcion
```

- **`prefijo` (en inglés):** Tipo de cambio realizado (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`).
  - `feat`: Nueva funcionalidad, subagente o capacidad.
  - `fix`: Corrección de un error o bug.
  - `docs`: Cambios o adiciones en documentación.
  - `test`: Creación o actualización de pruebas unitarias o fixtures.
  - `refactor`: Refactorización de código sin alterar su comportamiento.
  - `chore`: Tareas de mantenimiento, dependencias o configuración.
- **`contexto` (en inglés/código):** Módulo o componente modificado (e.g., `orchestrator`, `rf-agent`, `rnf-agent`, `inconsistency-agent`, `use-case-agent`, `schemas`, `graph`, `api`, `ui`).
- **`descripcion` (OBLIGATORIAMENTE en español):** Es la **única parte del commit que debe ir en español**. Resumen corto en minúsculas y modo imperativo describiendo claramente qué se hizo.

### Ejemplos Válidos:
- `feat(rf-agent): implementar salida estructurada con esquema pydantic`
- `test(inconsistency-agent): agregar pruebas unitarias con fixtures estaticas de mocks`
- `docs(specs): agregar propuesta maestra y documentacion de semana 13`
- `fix(schemas): forzar validacion de categorias iso 25010 en modelo rnf`
- `refactor(graph): desacoplar transiciones de estado de la logica del agente`
