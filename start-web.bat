@echo off
echo ========================================
echo   Ecrituria - Interface Web
echo ========================================
echo.

REM Charger la clé API depuis .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="OPENAI_API_KEY" set OPENAI_API_KEY=%%b
)

echo Demarrage du serveur web...
echo.
echo Ouvrez votre navigateur sur: http://localhost:8000
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

python -m src.server

