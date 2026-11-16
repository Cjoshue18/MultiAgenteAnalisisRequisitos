@echo off
cd /d "%~dp0"

echo ========================================
echo  Sistema Multiagente de Analisis de
echo  Requisitos de Software - Grupo 6
echo ========================================
echo.

:: Verificar si existe el entorno virtual
if not exist ".venv\Scripts\activate.bat" (
    echo [!] No se encontro el entorno virtual (.venv).
    echo [i] Creando entorno virtual e instalando dependencias...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

echo.
echo [1/3] Iniciando API Backend (FastAPI)...
start "" cmd /k "uvicorn src.api.main:app --reload"
timeout /t 3 >nul

echo.
echo [2/3] Iniciando Interfaz Frontend (Streamlit)...
start "" cmd /k "streamlit run src/ui/streamlit_app.py"

echo.
echo ========================================
echo  ¡Listo!
echo  - Backend:  http://127.0.0.1:8000
echo  - Frontend: http://localhost:8501
echo ========================================
echo.
echo Cierra estas ventanas para detener el sistema.
pause