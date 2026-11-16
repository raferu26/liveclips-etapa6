@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ===============================================
echo  LIVECLIPS - INSTALACAO ETAPA 3 (GRATUITA)
echo ===============================================
echo.
where ffmpeg >nul 2>&1
if errorlevel 1 (
 echo ERRO: ffmpeg nao encontrado no PATH.
 pause
 exit /b 1
)
py -3.11 -c "import sys; print(sys.version)" >nul 2>&1
if errorlevel 1 (
 echo Python 3.11 nao encontrado via launcher py.
 echo Instale a versao 3.11 com:
 echo winget install --id Python.Python.3.11 -e
 echo Feche este terminal e rode o instalador novamente.
 pause
 exit /b 1
)
if not exist .venv\Scripts\python.exe (
 py -3.11 -m venv .venv
 if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto erro
".venv\Scripts\python.exe" -m pip install "faster-whisper>=1.1,<2"
if errorlevel 1 goto erro
".venv\Scripts\python.exe" -c "from faster_whisper import WhisperModel; print('Biblioteca pronta!')"
if errorlevel 1 goto erro
echo.
echo INSTALACAO CONCLUIDA.
echo A primeira execucao baixara o modelo de voz tiny gratuitamente.
echo Rode INICIAR_OS_DOIS_AGENTES.bat
pause
exit /b 0
:erro
echo.
echo A instalacao nao terminou. Copie o erro e envie ao ChatGPT.
pause
exit /b 1
