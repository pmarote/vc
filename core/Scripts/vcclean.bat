@echo off
echo.
echo 🧹 Iniciando limpeza profunda do workspace...
echo Varrendo pastas de microapps e removendo caches (.venv, uv.lock, __pycache__)...

:: 1. Remove .venv e uv.lock de todas as pastas filhas do VC_ROOT
for /d %%i in ("%VC_ROOT%\*") do (
    if exist "%%i\.venv" (
        echo   [-] Removendo %%~nxi\.venv...
        rmdir /s /q "%%i\.venv"
    )
    if exist "%%i\uv.lock" (
        echo   [-] Removendo %%~nxi\uv.lock...
        del /q "%%i\uv.lock"
    )
)

:: 2. Limpeza global de __pycache__
echo   [-] Limpando todos os __pycache__ recursivamente...
for /d /r "%VC_ROOT%" %%i in (__pycache__) do (
    if exist "%%i" (
        rmdir /s /q "%%i"
    )
)

echo.
echo ✅ Limpeza concluída. Na próxima execução, o 'uv' fará o sync automático!
echo.