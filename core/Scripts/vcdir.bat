@echo off
:: DESC: Lista Microapps disponíveis
echo.
echo 📁 Microapps disponíveis no Workspace VC:
echo.
:: Lista apenas diretórios, filtrando pastas base como var, core e pastas ocultas do git
dir /B /A:D "%VC_ROOT%" | findstr /V /I /C:"var" /C:"core" /C:".git" /C:".vscode"
echo.