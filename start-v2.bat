@echo off
echo.
echo ========================================
echo    ECRITURIA v2.0 - Assistant Fiction
echo ========================================
echo.
echo Demarrage du serveur web...
echo.
echo Interface: http://localhost:8000
echo API Docs:  http://localhost:8000/docs
echo.
echo Nouveautes v2.0:
echo   - Recherche hybride BM25 + vecteurs
echo   - GraphRAG (graphe de connaissances)
echo   - Agents specialises
echo   - Support Ollama (modeles locaux)
echo.
echo Appuyez sur Ctrl+C pour arreter
echo.

cd /d "%~dp0"
python src\server.py

pause

