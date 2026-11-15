---
description: Reglas y estándares para la definición de esquemas Pydantic v2 y GraphState (Specification-Driven Development)
globs: src/schemas/**/*.py
---

# Reglas de Esquemas y Contratos (SDD)

Estas reglas aplican a todos los modelos de datos en `src/schemas/`.

## Directivas Obligatorias

1. **Pydantic v2 Estricto:** Todos los modelos de datos deben heredar de `pydantic.BaseModel`.
2. **Campos Documentados:** Cada atributo debe utilizar `Field(...)` con una descripción explícita para que el LLM entienda qué generar al forzar structured output.
3. **Inmutabilidad Opcional:** Definir `model_config = ConfigDict(frozen=True)` en modelos de salida de agentes para evitar mutaciones accidentales.
4. **Contratos de Requisitos:**
   - **RF:** Atributos obligatorios: `id` (e.g. `RF-01`), `nombre`, `descripcion`, `actores` (lista), `referencia_texto`.
   - **RNF:** Atributos obligatorios: `id` (e.g. `RNF-01`), `categoria_iso` (debe ser una de las 8 categorías de ISO 25010), `descripcion`, `metrica_objetiva`, `valor_umbral`.
   - **CUS:** Atributos obligatorios: `id` (e.g. `CUS-01`), `nombre`, `actor_principal`, `precondiciones`, `flujo_principal` (lista numerada), `flujos_alternativos`, `postcondiciones`.
   - **Inconsistencias:** Atributos: `tipo` (ambigüedad, contradicción, vacío), `severidad` (Alta, Media, Baja), `descripcion`, `pregunta_clarificacion`.

## Ejemplo Correcto

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import List

class RequisitoFuncional(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Identificador único del requisito (e.g. RF-01)")
    nombre: str = Field(..., description="Título representativo del requisito")
    descripcion: str = Field(..., description="Redacción atómica: El sistema debe...")
    actores: List[str] = Field(default_factory=list, description="Lista de actores involucrados")
    referencia_texto: str = Field(..., description="Cita textual de la entrada que sustenta el requisito")
```

## Ejemplo Prohibido

```python
# PROHIBIDO: Sin Field, tipos vagos, sin descripciones para el LLM
class RF:
    id = "RF-01"
    datos = {}
```
