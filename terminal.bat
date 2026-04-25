@echo off
:: --- CONFIGURAÇÃO DE AMBIENTE VC ---

:: 1. Codificação: Garante suporte a acentos e emojis no terminal
chcp 65001 > nul
set "PYTHONUTF8=1"

:: 2. Raiz do Projeto: Define o caminho absoluto onde o VC está instalado
:: O %~dp0 extrai o drive e o caminho da pasta onde este .bat reside
set "VC_ROOT=%~dp0"

:: 3. PATH: Injeta a pasta de utilitários no sistema para esta sessão
:: Isso permite que você digite 'vc', 'vcdir' ou 'vcclean' de qualquer lugar
set "PATH=%VC_ROOT%core\Scripts;%PATH%"

:: 4. PYTHONPATH: Permite que os microapps importem módulos de 'core/lib'
:: Inserimos a raiz para que 'import core.lib' funcione em qualquer .venv
set "PYTHONPATH=%VC_ROOT%;%PYTHONPATH%"

:: 5. Interface: Define o título e limpa a tela
title 🌊 VC - Vibe Coding Workspace

:: 6. Boot: Chama o Gerenciador para exibir o status atual
cls
uv run --directory "%VC_ROOT%core" main.py --welcome

:: Mantém o terminal aberto para uso
echo.
cmd /k