@echo off
cd /d "%~dp0"
python capturar_live.py
set RESULTADO=%ERRORLEVEL%
echo.
if not "%RESULTADO%"=="0" echo O teste terminou com erro. Mostre a mensagem ao ChatGPT.
echo Pressione qualquer tecla para fechar esta janela.
pause >nul
