@echo off
echo ========================================================
echo Iniciando Google Chrome para el Bot en puerto 9222...
echo Abre el portal de empleo USAL e inicia sesion normalmente.
echo ========================================================

set "CHROME_PATH=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" set "CHROME_PATH=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_PATH%" set "CHROME_PATH=chrome.exe"

start "" "%CHROME_PATH%" --remote-debugging-port=9222 --user-data-dir="%LOCALAPPDATA%\Google\Chrome\BotProfile" "https://empleos.usal.edu.ar/index.php"

