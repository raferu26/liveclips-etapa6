@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Voce precisa executar INSTALAR_ETAPA3.bat antes.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" "iniciar.py"
pause
