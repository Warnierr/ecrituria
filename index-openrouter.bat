@echo off
echo ========================================
echo   Assistant Fiction RAG - Indexation
echo   (OpenRouter compatible)
echo ========================================
echo.

REM Charger la clé API depuis .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="OPENAI_API_KEY" set OPENAI_API_KEY=%%b
)

REM Vérifier si un projet est spécifié
if "%1"=="" (
    echo Usage: index-openrouter.bat nom_projet
    echo Exemple: index-openrouter.bat anomalie2084
    echo.
    echo Projets disponibles:
    dir /b data
    echo.
    pause
    exit /b 1
)

set PROJECT=%1

REM Vérifier si le projet existe
if not exist "data\%PROJECT%" (
    echo Erreur: Le projet '%PROJECT%' n'existe pas dans data/
    echo.
    echo Projets disponibles:
    dir /b data
    echo.
    pause
    exit /b 1
)

REM Indexer
echo Indexation du projet '%PROJECT%' via OpenRouter...
echo.
python -m src.indexer %PROJECT%
echo.
echo ========================================
echo Indexation terminée!
echo Vous pouvez maintenant lancer: start-openrouter.bat %PROJECT%
echo ========================================
echo.
pause

