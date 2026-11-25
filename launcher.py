# -*- coding: utf-8 -*-
"""
Launcher del Sistema Multiagente de Analisis de Requisitos - Grupo 6
Lanza backend (FastAPI/Uvicorn) y frontend (Streamlit) en procesos separados.
"""
import os
import sys
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

# Ruta al interprete de Python del entorno virtual
venv_python = os.path.join(BASE, ".venv", "Scripts", "python.exe")

print("\n" + "=" * 50)
print("  Sistema Multiagente de Analisis de Requisitos")
print("  Grupo 6  |  Arquitectura y Evolucion de Software (2026-2)")
print("=" * 50 + "\n")

# Crear entorno virtual si no existe
if not os.path.exists(venv_python):
    print("[i] Creando entorno virtual (.venv)...")
    subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)

# Instalar dependencias (modo silencioso: solo muestra errores)
print("[i] Verificando dependencias...")
result = subprocess.run(
    [venv_python, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
    capture_output=True,
    text=True,
)
if result.returncode != 0:
    print("[!] Error instalando dependencias:")
    print(result.stderr[-2000:])
    sys.exit(1)
else:
    print("[i] Dependencias listas")

print("\n" + "=" * 50)
print("  Lanzando servicios...")
print("=" * 50 + "\n")

# Lanzar backend (FastAPI + Uvicorn)
print("[1/2] Iniciando API Backend (FastAPI)...")
subprocess.Popen(
    [venv_python, "-m", "uvicorn", "src.api.main:app", "--reload"],
    cwd=BASE,
    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
)

time.sleep(3)

# Lanzar frontend (Streamlit)
print("[2/2] Iniciando Interfaz Frontend (Streamlit)...")
subprocess.Popen(
    [venv_python, "-m", "streamlit", "run", "src/ui/streamlit_app.py"],
    cwd=BASE,
    creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
)

print("\n" + "=" * 50)
print("  ¡Listo!")
print("  - Backend (API):  http://127.0.0.1:8000")
print("  - Frontend (UI):  http://localhost:8501")
print("=" * 50)
print("\nCierra estas ventanas para detener el sistema.")
input("Presiona Enter para salir...")