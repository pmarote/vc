@echo off
:: core/Scripts/vc_env.bat - Hidrata o console com o ecossistema VC

:: 1. Codificação e UTF-8
chcp 65001 > nul
set "PYTHONUTF8=1"

:: 2. Raiz do Projeto (Padrão limpo: Sem barra no final)
:: O modificador %%~fi resolve o caminho absoluto e já entrega sem a barra final.
for %%i in ("%~dp0..\..") do set "VC_ROOT=%%~fi"

:: 3. Limpeza do UV, apenas caso necessário, nem sempre existe
set VIRTUAL_ENV=
set UV_RUN_RECURSION_DEPTH=

:: 4. PATH e PYTHONPATH
set "PATH=%VC_ROOT%\core\Scripts;%PATH%"

:: Se o PYTHONPATH já existir, concatena com o ponto e vírgula. Se não, cria limpo.
if defined PYTHONPATH (
    set "PYTHONPATH=%VC_ROOT%;%PYTHONPATH%"
) else (
    set "PYTHONPATH=%VC_ROOT%"
)
