@echo off
:: DESC: Abre o terminal de trabalho do VC com o banner de boas-vindas

:: Se for chamado diretamente (fora do terminal.bat), garante o ambiente
if "%VC_ROOT%"=="" call "%~dp0vc_env.bat"

title 🌊 VC - Vibe Coding Workspace

:: Boot: Exibe o status atual e o banner
cls
uv run --directory "%VC_ROOT%\core" main.py --welcome

:: Mantém o terminal aberto e interativo
echo.
cmd /k