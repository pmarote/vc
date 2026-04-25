@echo off
setlocal

:: Verifica se o usuário passou pelo menos o nome do microapp
if "%~1"=="" (
    echo.
    echo ❌ Uso incorreto.
    echo 💡 Exemplo: vc sfia_safic main.py -h
    echo.
    exit /b 1
)

:: Pega o primeiro argumento como o diretório alvo
set "MICROAPP=%~1"

:: O uv run executa a partir do VC_ROOT combinando com o microapp.
:: Passamos do %2 ao %9 para garantir que todos os comandos (como "main.py build --dir var") cheguem lá.
uv run --directory "%VC_ROOT%\%MICROAPP%" %2 %3 %4 %5 %6 %7 %8 %9

endlocal