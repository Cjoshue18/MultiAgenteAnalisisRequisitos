---
description: Reglas de arquitectura para nodos, transiciones y manejo de estado en LangGraph
globs: src/agents/**/*.py, src/graph/**/*.py
---

# Reglas para Nodos de LangGraph

Estas reglas aplican a la definición de nodos en `src/agents/` y a la construcción del grafo en `src/graph/`.

## Directivas Obligatorias

1. **Funciones Puras de Nodo:**
   - Todo nodo recibe el estado actual (`state: GraphState`) y retorna únicamente un diccionario con las claves actualizadas (`return {"clave": nuevo_valor}`).
   - **NUNCA** mutar el objeto `state` directamente ni usar variables globales.
2. **Uso de Structured Output:**
   - La llamada al LLM dentro de un subagente debe forzar el contrato Pydantic correspondiente usando `with_structured_output(ModeloPydantic)` o `response_schema`.
3. **Flujo de Ejecución Canónico:**
   - `Orquestador` -> Fork concurrente: `Subagente 1 (RF)` y `Subagente 2 (RNF)`.
   - Join: Ambos convergen hacia `Subagente 3 (Inconsistencias y Ambigüedades)`.
   - `Subagente 4 (Modelador CUS / HU)` genera Casos de Uso (`CUS`) o Historias de Usuario (`HU`) según el formato seleccionado previamente, usando `rf_aprobados` si existen o `requisitos_funcionales` en la primera pasada antes del HITL final.
4. **Manejo de Errores y Timeouts:**
   - Envolver las llamadas externas en bloques `try/except` tipados. Si el LLM falla, registrar el error en el estado (`state["errores"]`) en lugar de provocar un *crash* del proceso.

## Ejemplo Correcto

```python
from src.schemas.state import GraphState
from src.schemas.functional import RequisitoFuncional
from src.services.llm_client import obtener_cliente_llm

def nodo_requisitos_funcionales(state: GraphState) -> dict:
    texto = state.get("texto_usuario", "")
    llm = obtener_cliente_llm().with_structured_output(list[RequisitoFuncional])
    
    try:
        resultado = llm.invoke(f"Extrae RF de: {texto}")
        return {"requisitos_funcionales": resultado}
    except Exception as e:
        return {"errores": [f"Error en Subagente RF: {str(e)}"]}
```

## Ejemplo Prohibido

```python
# PROHIBIDO: Modificar estado in-place o usar globals
global_datos = []

def nodo_malo(state):
    state["requisitos_funcionales"].append("RF-01") # Mutación directa prohibida
    global_datos.append(state)
```
