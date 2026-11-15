---
description: Estándares de estilo de código, tipado estricto Python 3.11+ y seguridad
globs: src/**/*.py
---

# Estándares de Código y Seguridad

Estas reglas aplican a todo el código fuente en `src/`.

## Directivas Obligatorias

1. **Tipado Estricto (Type Hinting):**
   - Todas las funciones y métodos deben declarar el tipo de sus argumentos y el tipo de retorno.
   - Usar la sintaxis moderna de Python 3.11+ (ej. `list[str]` o `dict[str, Any]` en lugar de importar `List` o `Dict` de `typing` cuando sea posible; `str | None` en lugar de `Optional[str]`).
2. **Seguridad y Secretos:**
   - **NUNCA** escribir API keys en el código fuente.
   - Utilizar siempre `pydantic-settings` (`BaseSettings`) o variables de entorno leídas desde un archivo `.env`.
3. **Logging vs Print:**
   - Prohibido el uso de `print()` para depuración en código productivo.
   - Utilizar el módulo estándar `logging` configurado en `src/core/logger.py`.

## Ejemplo Correcto

```python
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    gemini_api_key: str
    groq_api_key: str | None = None

    class Config:
        env_file = ".env"

def formatear_codigo(prefijo: str, numero: int) -> str:
    logger.debug("Generando código %s-%02d", prefijo, numero)
    return f"{prefijo}-{numero:02d}"
```

## Ejemplo Prohibido

```python
# PROHIBIDO: Hardcodear llaves y usar print
API_KEY = "AIzaSyD-1234567890"

def formatear(prefijo, numero):
    print("depurando...")
    return prefijo + str(numero)
```
