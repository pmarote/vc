@echo off
:: Intercepta a chamada de limpeza (vcclean) para rodar a rotina e voltar pro terminal
if "%~1"=="clean" goto :do_clean

:: Configuração de Codificação para suportar acentos e emojis
chcp 65001 > nul
set PYTHONUTF8=1
title 🌊 VC - Vibe Coding Workspace v0.4.5

:: Definição de Cores (ANSI Escapes)
set "ESC="
set "RESET=%ESC%[0m"
set "CYAN=%ESC%[36m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "BLUE=%ESC%[34m"
set "MAGENTA=%ESC%[35m"
set "BOLD=%ESC%[1m"

:: --- CONFIGURAÇÃO DE MACROS (DOSKEY) ---

:: Core: O coração do sistema (uv run isolado por diretório)
doskey vc=uv run --directory %~dp0$*
doskey vls=dir /ad /b %~dp0
doskey vcclean="%~dp0terminal.bat" clean

:: Auditoria & Relatórios
doskey vcw=uv run --directory %~dp0sfiaweb main.py
doskey exp=uv run --directory %~dp0exportador main.py $*

:: Inteligência Artificial & Cloud
doskey vcaia=uv run --directory %~dp0ollama_analyst main.py $*
doskey vcc=uv run --directory %~dp0utils pmcloud.py $*

:: Utilitários de Contexto e Dados
doskey vcdump=uv run --directory %~dp0utils main.py dump $*
doskey sqlite2md=uv run --directory %~dp0utils main.py sqlite2md $*
doskey vcmd=start "" "%~dp0utils\visualizador_md.html"
doskey vm=start "" "%~dp0utils\visualizador_md.html"

:: Verificação e Mapeamento de Ferramentas Externas (Portáteis)
if exist "%~dp0..\usr\" (
    doskey wm=start "" "%~dp0..\usr\WinMerge\WinMergeU.exe"
    doskey dbb=start "" "%~dp0..\usr\DB.Browser.for.SQLite-v3.13.1-win64\DB Browser for SQLite.exe"
    doskey ct=start "" "%~dp0..\usr\cudatext\cudatext.exe" %~dp0README.md
    doskey mp=start "" "%~dp0..\usr\Markpad_2.6.4_x64.exe" %~dp0README.md
)

:: --- INTERFACE INICIAL ---

cls
echo %BOLD%%CYAN%============================================================%RESET%
echo %BOLD%%CYAN% 🚀 VC - VIBE CODING WORKSPACE v0.4.5%RESET% %BLUE%  [Raiz: %~dp0]%RESET%
echo %BOLD%%CYAN%============================================================%RESET%
echo  Use o 'uv' para rodar os scripts.
echo    se estiver na pasta %~dp0utils  -^> uv run main.py -h
echo   %YELLOW% %BOLD%se estiver em qualquer outra pasta%RESET% -^> uv run --directory %~dp0utils main.py -h
echo.
echo  Atalhos criados com doskey:
echo %YELLOW% %BOLD%[CORE]%RESET%
echo   %GREEN%vc%RESET% ^<pasta^> main.py    Executa microapp via uv
echo   %GREEN%vls%RESET%                   Lista microapps disponíveis
echo   %GREEN%vcclean%RESET%               Limpa ambientes (.venv, uv.lock e __pycache__)
echo %YELLOW% %BOLD%[AUDITORIA]%RESET%
echo   %GREEN%vcw%RESET%                   Inicia Servidor SFIA Web (FastAPI)
echo   %GREEN%exp%RESET%                   Exportador (SQL -^> Excel/MD/TSV)
echo %YELLOW% %BOLD%[IA / CLOUD / CONTEXTO]%RESET%
echo   %GREEN%vcaia%RESET%                 Ollama Analyst (Análise local)
echo   %GREEN%vcc%RESET%                   PMCloud (Sync/Backup privado)
echo   %GREEN%vcdump%RESET%                Gera Contexto IA do projeto (Dump)
echo   %GREEN%vcmd%RESET%                  Abre Visualizador Markdown Interativo
echo %YELLOW% %BOLD%[DADOS]%RESET%
echo   %GREEN%sqlite2md%RESET%             Gera relatório técnico de um .sqlite

if exist "%~dp0..\usr\" (
    echo %YELLOW% %BOLD%[FERRAMENTAS]%RESET%
    echo   %GREEN%wm%RESET%, %GREEN%dbb%RESET%, %GREEN%ct%RESET%, %GREEN%mp%RESET%       WinMerge, DBBrowser, CudaText, Markpad^(Editor ^.md^)
) else (
    echo %MAGENTA% [!] Pasta ../usr não detectada. Atalhos de ferramentas externas desativados.%RESET%
)

echo.
:: Mantem o prompt de comando aberto
cmd /k
exit /b

:: ============================================================================
:: --- ROTINAS EXTRAS E AUTOMAÇÕES ---
:: ============================================================================

:do_clean
echo.
echo %CYAN%🧹 Iniciando limpeza profunda do workspace...%RESET%
echo %YELLOW%Varrendo pastas de microapps e removendo caches...%RESET%

:: 1. Itera sobre todas as pastas na raiz e remove .venv e uv.lock
for /d %%i in ("%~dp0*") do (
    if exist "%%i\.venv" (
        echo   [-] Removendo %%~nxi\.venv...
        rmdir /s /q "%%i\.venv"
    )
    if exist "%%i\uv.lock" (
        echo   [-] Removendo %%~nxi\uv.lock...
        del /q "%%i\uv.lock"
    )
)

:: 2. Limpeza global de __pycache__ (Recursiva em todo o projeto)
echo   [-] Limpando todos os __pycache__ recursivamente...
for /d /r "%~dp0" %%i in (__pycache__) do (
    if exist "%%i" rmdir /s /q "%%i"
)

echo %GREEN%✅ Limpeza concluida com sucesso!%RESET%
echo.
exit /b