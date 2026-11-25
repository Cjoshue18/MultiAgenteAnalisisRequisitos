---
description: Reglas de flujo SDD estilo Spec Kit (Constitution, Spec agnóstica, Plan técnico y Tasks TDD)
globs: specs/**/*.md
---

# Flujo SDD estilo Spec Kit

Estas reglas gobiernan toda especificación y planificación dentro de `specs/`.

## Directivas Obligatorias

1. **Estructura por Funcionalidad:**
   - Las reglas globales del proyecto residen en `specs/constitution.md`.
   - Cada capacidad vive en `specs/<NNN-nombre-corto>/` con tres artefactos en orden estricto:
     1. `spec.md` (QUÉ se requiere; aprobado por el usuario antes de continuar).
     2. `plan.md` (CÓMO se construye; arquitectura, esquemas y decisiones técnicas).
     3. `tasks.md` (lista de checkboxes ordenada para ejecución TDD).
2. **Contenido Obligatorio de `spec.md`:**
   - **User Story:** Formato `COMO <rol> / QUIERO <capacidad> / PARA QUE <beneficio>`.
   - **Requirements:** Requisitos identificados con código (`REQ-01`, `REQ-02`, ...) verificables de forma binaria (**Sí/No**). Prohibidos términos subjetivos o ambiguos (*"rápido"*, *"veloz"*, *"amigable"*, *"seguro"*, *"eficiente"*).
   - **Acceptance Scenarios:** Cada requisito debe tener al menos un escenario `DADO <contexto> / CUANDO <acción> / ENTONCES <resultado comprobable>` lo suficientemente preciso para derivar un test automatizado.
   - **Out of Scope:** Qué queda explícitamente excluido de esta spec.
   - **Open Questions:** Dudas o decisiones pendientes antes de aprobar la spec.
3. **Neutralidad Tecnológica en `spec.md`:**
   - **PROHIBIDO** mencionar lenguajes, frameworks, bases de datos, librerías, endpoints o estructuras de código dentro de `spec.md` (nada de Python, LangGraph, FastAPI, Pydantic, SQLite o Streamlit).
   - Los detalles de implementación pertenecen exclusivamente a `plan.md`.
4. **Compuerta de Aprobación y TDD en `tasks.md`:**
   - No se crea `plan.md` ni se escribe código hasta aprobar `spec.md` y resolver sus `Open Questions` bloqueantes.
   - En `tasks.md`, cada requisito debe incluir primero la tarea de escritura de su prueba (derivada de los Acceptance Scenarios) y luego la tarea de implementación.
   - El nombre de cada función de test debe incluir el código del requisito de su spec (ej. `test_req_01_rechaza_entrada_corta`).
5. **Sincronización Estricta ante Cambios (Cero *Spec Drift*):**
   - Cualquier alteración en código que derive de una spec (reglas, umbrales, estados, comportamientos) debe propagarse **siempre de arriba hacia abajo**:
     1. Editar `spec.md` (requisitos y Acceptance Scenarios afectados) y confirmar el cambio.
     2. Editar `plan.md` si cambia la solución técnica.
     3. Editar `tasks.md` y ajustar primero las pruebas (`test_req_xx_*`).
     4. Recién entonces modificar el código productivo.
   - **PROHIBIDO** cambiar parámetros o reglas directamente en el código dejando la `spec.md` desactualizada (por ejemplo, que `spec.md` indique 15 segundos y el código use 27 segundos).

## Ejemplo Correcto (en `spec.md`)

```markdown
- **REQ-01:** El sistema debe rechazar cualquier solicitud con menos de 20 caracteres significativos antes de iniciar el análisis.
- **Escenario REQ-01.1:** DADO un texto de 10 caracteres CUANDO se solicita iniciar el análisis ENTONCES el sistema rechaza la solicitud y registra un error de validación sin invocar análisis posteriores.
```

## Ejemplo Prohibido (en `spec.md`)

```markdown
- El sistema debe usar FastAPI y Pydantic para validar rápido el JSON en SQLite.
```
