@echo off
chcp 65001 >nul
cd /d "%~dp0"
set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%USERPROFILE%\OneDrive\Desktop\liveclips_etapa3\.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
 echo Execute INSTALAR_ETAPA3.bat nesta pasta para preparar o Python.
 pause
 exit /b 1
)
"%PYTHON_EXE%" "iniciar_etapa5.py"
pause
