@echo off
echo ========================================================
echo Iniciando Google Chrome con puerto de depuracion 9222...
echo Abre el portal de empleo USAL e inicia sesion normalmente.
echo ========================================================
start "" "chrome.exe" --remote-debugging-port=9222
