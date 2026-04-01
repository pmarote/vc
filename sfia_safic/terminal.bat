@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title Terminal - SFIA SAFIC

echo ========================================================
echo                          SFIA SAFIC
echo ========================================================
echo.
echo O ambiente esta configurado. Use o 'uv' para rodar os scripts.
echo.
echo Comandos disponiveis no main.py:
echo   uv run main.py --h
echo   uv run main.py --build
echo   uv run main.py --report
echo.
cmd /k