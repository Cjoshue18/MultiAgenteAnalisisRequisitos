# Ejecución de extremo a extremo — Sistema Multiagente (Grupo 6)

La implementación es **100 % Python**. El frontend utiliza Streamlit y se comunica con FastAPI usando un cliente HTTP de la biblioteca estándar de Python. Se conservan LangGraph, SQLite, Pydantic y los cuatro subagentes.

## 1. Instalar (Python 3.11 o posterior)

Desde la carpeta del repositorio, en PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

En Linux/macOS: `python3 -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`.

## 2. Demostración SIN clave de IA (resultados ilustrativos)

Esta modalidad permite mostrar proyectos, procesamiento, revisión humana, aprobación y descargas sin consumir llamadas de IA. **La información de los agentes es ficticia y no representa análisis real del documento**.

Terminal 1:

```powershell
uvicorn src.api.demo:app --reload --port 8000
```

Terminal 2 (con el mismo entorno virtual activado):

```powershell
streamlit run src/ui/app.py
```

Abre `http://localhost:8501` y crea un proyecto. El backend demo escribe `demo_analisis.db` y `demo_reportes/` (ignorados por Git).

## 3. Ejecución REAL con Google Gemini

Copia `.env.example` a `.env`, edita `LLM_PROVIDER=gemini` y define `GEMINI_API_KEY` localmente. **No publiques `.env` en GitHub**. Se requiere Internet, credenciales válidas y acceso a un modelo vigente configurado en `.env`.

Terminal 1:

```powershell
uvicorn src.api.app:app --reload --port 8000
```

Terminal 2:

```powershell
streamlit run src/ui/app.py
```

La API crea `analisis.db`, `checkpoints.db` y `reportes/`. La interfaz muestra estados, requisitos, inconsistencias y trazabilidad; la aprobación humana es necesaria para exportar. Una corrida en modo `AMBOS` produce CUS y HU.

## 4. Pruebas

```powershell
python -m pytest -v
```

Las pruebas con mocks no requieren claves de IA. Para validar la operación real, ejecutar adicionalmente una solicitud con credenciales y comprobar que los resultados son fieles al texto original.

## 5. Consideraciones

- Archivos permitidos: `.txt`, `.md`, `.pdf`, hasta 10 MB; PDF debe contener texto extraíble.
- Los análisis aprobados son inmutables: para modificarlos hay que crear una nueva versión.
- Interfaz pensada para demostración local de un único analista, no para publicación pública sin autenticación adicional.
- Si `localhost:8000` no está disponible, define `API_BASE_URL` antes de iniciar Streamlit.
- **No es correcto afirmar 100 % de funcionamiento validado** sin ejecutar toda la suite y al menos una prueba integrada contra el proveedor de IA.
