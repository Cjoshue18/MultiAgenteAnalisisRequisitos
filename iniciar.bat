@echo off
cd /d "%~dp0"
echo ========================================
echo  Sistema Multiagente de Analisis de
echo  Requisitos de Software - Grupo 6
echo ========================================
echo.
echo [1/3] Activando entorno y dependencias...
call .venv\Scripts\activate.bat >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] No se encontro entorno virtual. Instalando dependencias globalmente...
    pip install -r requirements.txt
)
echo.
echo [2/3] Iniciando API Backend (FastAPI)...
start "" cmd /k "uvicorn src.api.main:app --reload"
timeout /t 3 >nul
echo.
echo [3/3] Iniciando Interfaz Frontend (Streamlit)...
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