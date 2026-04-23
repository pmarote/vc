@echo off
:: Intercepta a chamada de limpeza (vcclean) para rodar a rotina e voltar pro terminal
if "%~1"=="clean" goto :do_clean

:: Configuração de Codificação para suportar acentos e emojis
chcp 65001 > nul
set PYTHONUTF8=1
title 🌊 VC - Vibe Coding Workspace

:: Definição de Cores (ANSI Escapes)
set "ESC="
set "RESET=%ESC%[0m"
set "CYAN=%ESC%[36m"
set "GREEN=%ESC%[32m"
set "YELLOW=%ESC%[33m"
set "RED=%ESC%[31m"
set "BLUE=%ESC%[34m"
set "MAGENTA=%ESC%[35m"
set "BOLD=%ESC%[1m"
set "BG_RED=%ESC%[41;97m"

:: --- DETERMINA A PASTA PAI DE FORMA ABSOLUTA ---
:: Pega a raiz atual (%~dp0), sobe um nível (..) e resolve o caminho limpo (%%~fI)
for %%I in ("%~dp0..") do set "PARENT_DIR=%%~fI"
set "USR_DIR=%PARENT_DIR%\usr"

:: --- CONFIGURAÇÃO DE MACROS (DOSKEY) ---

:: Core: O coração do sistema (uv run isolado por diretório)
doskey vc=uv run --directory %~dp0$*
doskey vcdir=dir /ad /b %~dp0
doskey vcclean="%~dp0terminal.bat" clean

:: Auditoria & Relatórios
doskey vcw=start "SFIA Web Server" uv run --directory %~dp0sfiaweb main.py serve
doskey exp=uv run --directory %~dp0exportador main.py $*

:: Inteligência Artificial & Cloud
doskey vcaia=uv run --directory %~dp0ollama_analyst main.py $*

:: Utilitários
doskey utils=uv run --directory %~dp0utils main.py list
doskey scvc=uv run --directory %~dp0utils sc.py $*
doskey pmc=uv run --directory %~dp0utils pmcloud.py $*
doskey sqlite2md=uv run --directory %~dp0utils sqlite_dump.py $*

:: Verificação e Mapeamento de Ferramentas Externas (Portáteis)
:: Retirado o start e adicionado o $* para permitir abrir arquivos passando o nome
if exist "%USR_DIR%\" (
    doskey wm="%USR_DIR%\WinMerge\WinMergeU.exe" $*
    doskey dbb="%USR_DIR%\DB.Browser.for.SQLite-v3.13.1-win64\DB Browser for SQLite.exe" $*
    doskey ct="%USR_DIR%\cudatext\cudatext.exe" $*
    doskey mp="%USR_DIR%\Markpad_2.6.4_x64.exe" $*
)

:: --- INTERFACE INICIAL ---

cls
echo %BOLD%%CYAN%============================================================%RESET%
echo %BOLD%%CYAN% 🚀 VC - VIBE CODING WORKSPACE %RESET% %BLUE%  [Raiz: %~dp0]%RESET%
echo %BOLD%%CYAN%============================================================%RESET%
echo  Use o 'uv' para rodar os scripts.
echo    se estiver na pasta %~dp0utils  -^> uv run main.py -h
echo   %YELLOW% %BOLD%se estiver em qualquer outra pasta%RESET% -^> uv run --directory %~dp0utils main.py -h
echo.
echo  Atalhos criados com doskey:
echo %YELLOW% %BOLD%[CORE]%RESET%
echo   %GREEN%vc%RESET% ^<pasta^> main.py -h Executa microapp (uv run --directory %~dp0$*)
echo   %GREEN%vcdir%RESET%                 Lista microapps disponíveis (dir /ad /b %~dp0)
echo   %GREEN%vcclean%RESET%               Limpa ambientes (.venv, uv.lock e __pycache__)
echo %YELLOW% %BOLD%[AUDITORIA]%RESET%
echo   %GREEN%vcw%RESET%                   SFIA Web (uv run --directory %~dp0sfiaweb main.py)
echo   %GREEN%exp%RESET%                   SQL -^> Excel/MD/TSV (uv run --directory %~dp0exportador main.py $*)
echo %YELLOW% %BOLD%[IA]%RESET%
echo   %GREEN%vcaia%RESET%                 Ollama Analyst (uv run --directory %~dp0ollama_analyst main.py $*)
echo %YELLOW% %BOLD%[UTILS]%RESET%
echo   %GREEN%utils%RESET%                 Lista utilitários (vc utils main.py list)
echo   %GREEN%scvc%RESET%                  ShortCuts do sistema VC (uv run --directory %~dp0utils sc.py $*)
echo   %GREEN%pmc%RESET%                   PMCloud Sync/Backup privado (uv run --directory %~dp0utils pmcloud.py $*)
echo   %GREEN%sqlite2md%RESET%             sqlite2md (uv run --directory %~dp0utils sqlite_dump.py $*)

if exist "%USR_DIR%\" (
    echo %YELLOW% %BOLD%[FERRAMENTAS]%RESET%
    echo   %GREEN%wm%RESET%, %GREEN%dbb%RESET%, %GREEN%ct%RESET%, %GREEN%mp%RESET%       WinMerge, DBBrowser, CudaText, Markpad^(Editor ^.md^)
) else (
    echo %BG_RED%================================================================================%RESET%
    echo %BG_RED% AVISO CRÍTICO: PASTA DE FERRAMENTAS 'usr' NÃO ENCONTRADA!                      %RESET%
    echo %BG_RED%================================================================================%RESET%
    echo %YELLOW%A pasta %BOLD%%USR_DIR%%RESET%%YELLOW% não foi detectada. Atalhos de ferramentas externas desativados.%RESET%
    echo.
    echo %RED%%BOLD%Por que isso é um problema?%RESET%
    echo As ferramentas contidas nela ^(WinMerge, DB Browser, CudaText e Markpad^) são
    echo %BOLD%EXTREMAMENTE IMPORTANTES%RESET% para o trabalho diário de auditoria. Elas garantem
    echo agilidade para inspecionar bancos de dados, comparar códigos e editar os
    echo templates Markdown de forma eficiente.
    echo.
    echo %GREEN%%BOLD%Ação Altamente Recomendada:%RESET%
    echo Providencie a cópia desta pasta 'usr'. Ela provavelmente existe em outro drive
    echo ou em outro computador onde o sistema VC já foi utilizado anteriormente.
    echo Copie a pasta inteira e cole-a exatamente no seguinte caminho:
    echo %YELLOW%Caminho Exigido: %BOLD%%USR_DIR%%RESET%
    echo %BG_RED%================================================================================%RESET%
)

echo.

:: --- VERIFICAÇÃO CRÍTICA DO DRIVE (Restrição ao Drive C:) ---
if /i not "%~d0"=="C:" (
    echo.
    echo %BG_RED%================================================================================%RESET%
    echo %BG_RED% ALERTA CRÍTICO: AMBIENTE FORA DO DRIVE C: !                                    %RESET%
    echo %BG_RED%================================================================================%RESET%
    echo %YELLOW%Você está executando o VC a partir do drive %BOLD%%~d0%RESET%%YELLOW%.%RESET%
    echo.
    echo %RED%%BOLD%Por que isso é um problema e não é recomendável?%RESET%
    echo Se você der boot no computador usando outro Windows ^(dual boot, disco externo,
    echo etc.^), o sistema operacional pode reatribuir a letra deste drive original 
    echo ^(por exemplo, o que era C: passa a ser E:^).
    echo.
    echo O ecossistema VC, o Python e os ambientes virtuais ^(.venv^) gerados pelo 'uv'
    echo dependem de caminhos absolutos para criar links de sistema corretos. 
    echo A mudança da letra do drive %BOLD%QUEBRARÁ%RESET% os links do ambiente, corromperá as 
    echo bibliotecas e causará falhas imprevisíveis nos relatórios.
    echo.
    echo %GREEN%%BOLD%Recomendação Fortemente Aconselhada:%RESET%
    echo Feche este terminal, mova a pasta inteira do VC para o seu drive C:, limpe os ambientes 
    echo virtuais com o comando %BOLD%vcclean%RESET% e execute o terminal.bat a partir de seu drive C:.
    echo.
    echo %BG_RED%================================================================================%RESET%
    echo.
    echo Se deseja continuar mesmo assim ^(ciente de que o sistema pode quebrar^)...
    pause
    echo.
    echo %YELLOW%Iniciando terminal em modo de risco...%RESET%
    echo.
)
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
echo Todos os ambientes virtuais foram destruídos.
echo Eles serão recriados automaticamente na próxima vez que você rodar um 'vc [pasta]'.
echo.
exit /b