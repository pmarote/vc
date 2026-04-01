@echo off
chcp 65001 > nul
set PYTHONUTF8=1
title Vibe Code Workspace

:: Configurando os atalhos (macros) com DOSKEY usando caminhos absolutos (%~dp0)
doskey vc=uv run --directory %~dp0$*
doskey vcdump=uv run --directory %~dp0utils main.py dump $*
doskey sqlite2md=uv run --directory %~dp0utils main.py sqlite2md $*
doskey exp=uv run --directory %~dp0exportador main.py $*

echo ============================================================
echo          🚀 AMBIENTE VIBE CODE INICIADO
echo ============================================================
echo.
echo O ambiente esta configurado. Use o 'uv' para rodar os scripts.
echo   Exemplo: se estiver na pasta %~dp0utils
echo     uv run main.py -h
echo   Exemplo: se estiver em qualquer outra pasta
echo     uv run --directory %~dp0utils main.py -h
echo.
echo Por isso, para facilitar, neste arquivo terminal.bat foi configurado o doskey 'vc':
echo   Assim, os comandos acima podem ser feitos de qualquer pasta, desta forma:
echo     vc utils main.py -h
echo.
echo Comandos disponiveis em utils:
echo   vc utils main.py dump --root ../projeto_alvo --dst ../var
echo   vc utils main.py sqlite2md --src ../data/seu_banco.sqlite --dst ../var/relatorio_banco.md
echo.
echo Demais atalhos configurados para os utilitarios:
echo.
echo   vcdump      -^> Gera o consolidado (Markdown) do projeto
echo                 Uso: vcdump --root sfia_safic
echo                 (Se omitir --root, faz o dump da raiz)
echo.
echo   sqlite2md   -^> Gera o relatorio Markdown de um SQLite
echo                 Uso: sqlite2md --src data/meubanco.db3
echo.
echo   exp   -^> Exportaação do módulo exportador/main.py
echo                 Uso: exp -h
echo doskey exp=uv run --directory %~dp0exportador main.py $*
echo ============================================================
echo.
:: Mantem o prompt de comando aberto
cmd /k