@echo off
echo ========================================
echo   Assistant Fiction RAG - Demarrage
echo ========================================
echo.

REM Verifier si un projet est specifie
if "%1"=="" (
    echo Usage: start.bat nom_projet
    echo Exemple: start.bat anomalie2084
    echo.
    echo Projets disponibles:
    dir /b data
    echo.
    pause
    exit /b 1
)

set PROJECT=%1

REM Verifier si le projet existe
if not exist "data\%PROJECT%" (
    echo Erreur: Le projet '%PROJECT%' n'existe pas dans data/
    echo.
    echo Projets disponibles:
    dir /b data
    echo.
    pause
    exit /b 1
)

REM Verifier si l'index existe
if not exist "db\%PROJECT%" (
    echo L'index pour '%PROJECT%' n'existe pas encore.
    echo Indexation en cours...
    echo.
    python -m src.indexer %PROJECT%
    echo.
)

REM Lancer le chat
echo Lancement du chat pour le projet '%PROJECT%'...
echo.
python -m src.cli %PROJECT%

