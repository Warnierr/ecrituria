@echo off
echo ========================================
echo   Assistant Fiction RAG - OpenRouter
echo ========================================
echo.

REM Charger la clé API depuis .env
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="OPENAI_API_KEY" set OPENAI_API_KEY=%%b
)

REM Vérifier si un projet est spécifié
if "%1"=="" (
    echo Usage: start-openrouter.bat nom_projet
    echo Exemple: start-openrouter.bat anomalie2084
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

REM Vérifier si l'index existe
if not exist "db\%PROJECT%" (
    echo L'index pour '%PROJECT%' n'existe pas encore.
    echo Indexation en cours...
    echo.
    python -m src.indexer %PROJECT%
    echo.
)

REM Lancer le chat
echo Lancement du chat pour le projet '%PROJECT%'...
echo Utilisation d'OpenRouter
echo.
python -m src.cli %PROJECT%

