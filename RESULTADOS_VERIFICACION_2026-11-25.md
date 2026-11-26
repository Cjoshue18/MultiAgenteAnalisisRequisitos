# Revisión técnica — 25 de noviembre de 2026

## Avances añadidos en esta entrega

1. **Frontend Streamlit** (`src/ui/app.py`): tablero visual y navegación, creación/selección de proyectos, ingreso por texto o archivos, modalidades CUS/HU/AMBOS, revisión editable de RF/RNF/CUS/HU, inconsistencias y respuestas, trazabilidad y trazas, aprobación humana, historial, versiones y descarga de MD/JSON/PDF/DOCX.
2. **Cliente HTTP de UI** (`src/services/api_client.py`): conexión con endpoints reales de FastAPI sin dependencia adicional de `requests`, validación del archivo, errores legibles.
3. **Backend para demo local** (`src/api/demo.py`): mantiene la interfaz y la arquitectura, pero utiliza respuestas fijas para una demostración sin credenciales. **No ejecuta inferencia real de IA.**
4. **Pruebas** (`tests/unit/test_api_client_ui.py`): cinco pruebas de cliente HTTP con servidor local, sin Internet.
5. **Integración de proyecto**: Streamlit incorporado a `pyproject.toml`; README, guía de ejecución, `.gitignore` y GitHub Actions en `main` y `principal`.
6. Se conservó el backend original, los cuatro subagentes, contratos Pydantic, LangGraph, persistencia SQLite y tests preexistentes.

## Verificaciones realizadas aquí

- `python -m compileall -q src`: **correcto**.
- `pytest -q tests/unit/test_api_client_ui.py`: **5 aprobadas**.
- Suite seleccionada que no requiere LangGraph ni `pytest-mock`: **31 pruebas aprobadas**.
- Intento de suite ampliada: **38 aprobadas y 1 error de fixture `mocker` ausente** cuando se incluyó una prueba que requiere `pytest-mock`. En el proyecto `pytest-mock` está incluido en `.[dev]`.
- No se pudo ejecutar la suite completa porque `langgraph`, `streamlit`, `langchain-google-genai` y `pytest-mock` no están instalados en este entorno y la conexión a PyPI no está disponible.
- No se ejecutaron pruebas integradas con Google Gemini ni la interfaz interactiva real. Por ello **no se certifica que el sistema funcione al 100 %**.

## Para confirmar cierre real

En Windows, instalar las dependencias de `.[dev]` y ejecutar `pytest -v`. Luego levantar FastAPI y Streamlit según `GUIA_EJECUCION_FINAL.md`, comprobar el flujo de demostración y después una corrida de inferencia real autorizada con credenciales propias. Revisar especialmente el flujo de generación, revisión, aprobación, exportación, recuperación de checkpoints y errores 429.

## Estado de GitHub

Los cambios están preparados en este ZIP; **no se realizó push ni merge remoto**. Subir desde GitHub Desktop, idealmente en una rama `feat/interfaz-streamlit`, y validar el CI antes de fusionar para no pisar el trabajo del equipo. Antes de copiar, hacer `Fetch origin` y `Pull origin` y revisar si el compañero introdujo cambios nuevos después de la copia analizada.
