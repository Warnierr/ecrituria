@echo off
echo.
echo ========================================
echo    ECRITURIA v2.0 - Indexation
echo ========================================
echo.

cd /d "%~dp0"

if "%1"=="" (
    echo Usage: index-v2.bat [nom_projet] [options]
    echo.
    echo Options:
    echo   --full    Reconstruction complete de l'index
    echo   --update  Mise a jour incrementale (defaut)
    echo   --stats   Afficher les statistiques
    echo.
    echo Exemples:
    echo   index-v2.bat anomalie2084
    echo   index-v2.bat anomalie2084 --full
    echo   index-v2.bat anomalie2084 --stats
    echo.
    pause
    exit /b 1
)

set PROJECT=%1
set MODE=%2

if "%MODE%"=="" set MODE=--update

echo Projet: %PROJECT%
echo Mode: %MODE%
echo.

python -m src.indexer %PROJECT% %MODE%

echo.
pause

