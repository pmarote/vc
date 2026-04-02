@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title Terminal - Importador SAFIC

echo ========================================================
echo          IMPORTADOR SAFIC (MDF -^> SQLITE)
echo ========================================================
echo.
echo O ambiente esta configurado. Use o 'uv' para rodar os scripts.
echo.
echo Comandos disponiveis no main.py:
echo   uv run main.py convert --mdf arquivo.mdf --ldf arquivo.ldf --out saida.db3
echo   uv run main.py merge --osf 13013199258 --arquivos arquivo1.db3 arquivo2.db3
echo.
cmd /k