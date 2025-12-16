@echo off
echo ========================================
echo   Assistant Fiction RAG - Indexation
echo ========================================
echo.

REM Verifier si un projet est specifie
if "%1"=="" (
    echo Usage: index.bat nom_projet
    echo Exemple: index.bat anomalie2084
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

REM Indexer
echo Indexation du projet '%PROJECT%'...
echo.
python -m src.indexer %PROJECT%
echo.
echo ========================================
echo Indexation terminee!
echo Vous pouvez maintenant lancer: start.bat %PROJECT%
echo ========================================
echo.
pause

