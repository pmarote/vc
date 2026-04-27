@echo off
echo.
echo 🧹 Iniciando limpeza profunda do workspace VC...
echo 📂 Raiz: %VC_ROOT%
echo.
echo Varrendo pastas de microapps e removendo caches (.venv, uv.lock, __pycache__)...

:: 1. Remove .venv e uv.lock de todas as pastas filhas do VC_ROOT
:: O "%VC_ROOT%\*" agora funciona perfeitamente pois a variável base não tem barra extra
for /d %%i in ("%VC_ROOT%\*") do (
    if exist "%%i\.venv" (
        echo   [-] Removendo ambiente: %%~nxi\.venv
        rmdir /s /q "%%i\.venv"
    )
    if exist "%%i\uv.lock" (
        echo   [-] Removendo lockfile: %%~nxi\uv.lock
        del /q "%%i\uv.lock"
    )
)

:: 2. Limpeza global de __pycache__
echo   [-] Limpando todos os __pycache__ recursivamente...
:: A sintaxe /r "%VC_ROOT%" exige um caminho base limpo, o que bate com a nossa nova regra
for /d /r "%VC_ROOT%" %%i in (__pycache__) do (
    if exist "%%i" (
        rmdir /s /q "%%i"
    )
)

echo.
echo ✅ Limpeza concluida. 
echo 💡 Na proxima execucao de um microapp, o 'uv' fara o sync automatico!
echo.