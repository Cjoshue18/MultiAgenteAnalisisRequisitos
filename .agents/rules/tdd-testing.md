---
description: Reglas estrictas para pruebas unitarias con pytest, mocks y fixtures estáticas (TDD)
globs: tests/**/*.py
---

# Reglas de Pruebas Unitarias (TDD)

Estas reglas aplican a todo el directorio `tests/`.

## Directivas Obligatorias

1. **Cero Llamadas a APIs Reales de LLM:**
   - Queda terminantemente prohibido invocar endpoints de Google Gemini o Groq en `tests/unit/`.
   - Utilizar siempre `unittest.mock.patch` o `mocker.patch` para simular las respuestas del LLM.
2. **Uso de Fixtures Estáticas:**
   - Las respuestas simuladas deben provenir de `tests/fixtures/*.json` o diccionarios predefinidos.
3. **Pruebas de Transición de Estados:**
   - Probar que cada nodo recibe el `GraphState` esperado y retorna el delta correspondiente sin alterar llaves no relacionadas.
4. **Pruebas de Resiliencia / Fallbacks:**
   - Probar casos límite: JSON malformado del LLM, entradas vacías, inyecciones de texto, y verificar que Pydantic o el orquestador capturen la excepción limpiamente.

## Ejemplo Correcto

```python
from unittest.mock import MagicMock
import pytest
from src.schemas.functional import RequisitoFuncional
from src.agents.functional_agent import nodo_requisitos_funcionales

def test_nodo_rf_retorna_esquema_valido(mocker):
    # Mock de la respuesta estructurada del modelo
    mock_rf = [
        RequisitoFuncional(
            id="RF-01",
            nombre="Iniciar Sesión",
            descripcion="El sistema debe permitir autenticar usuarios.",
            actores=["Usuario"],
            referencia_texto="El usuario puede iniciar sesión."
        )
    ]
    mocker.patch("src.agents.functional_agent.extraer_rf_llm", return_value=mock_rf)

    estado_inicial = {"texto_usuario": "El usuario puede iniciar sesión."}
    resultado = nodo_requisitos_funcionales(estado_inicial)

    assert "requisitos_funcionales" in resultado
    assert len(resultado["requisitos_funcionales"]) == 1
    assert resultado["requisitos_funcionales"][0].id == "RF-01"
```

## Ejemplo Prohibido

```python
# PROHIBIDO: Llamar a la API real durante el test unitario
def test_llamada_real_gemini():
    cliente = genai.Client(api_key="AIzaSy...") # Gasta tokens y falla sin internet
    resultado = cliente.models.generate_content(...)
```
