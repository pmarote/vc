@echo off
:: DESC: Executa ferramentas [microappDir] [pythonFile] [args] (ex: vc core main.py -h)
:: ARGS: [mcapDir] [.py] [args]
setlocal

:: Verifica se o usuário passou pelo menos o nome do microapp
if "%~1"=="" (
    echo.
    echo ❌ Uso incorreto.
    echo 💡 Exemplo: vc sfia_safic main.py -h
    echo.
    exit /b 1
)

:: 1. Pega o primeiro argumento (microapp) e "shifta" para retirá-lo da fila
set "MICROAPP=%~1"
shift

:: 2. Acumula infinitamente os demais parâmetros em uma única variável
set "PARAMS="
:collect_params
if "%~1"=="" goto execute
set "PARAMS=%PARAMS% %1"
shift
goto collect_params

:execute
:: 3. O uv run executa a partir do VC_ROOT combinando com o microapp.
uv run --directory "%VC_ROOT%\%MICROAPP%" %PARAMS%

endlocal