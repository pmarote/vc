@echo off
:: DESC: Processa Literate Documents (*.tmpl.md) salvos na pasta _tmpl com `hot-reload` a cada 30 segundos
:: Muda a pagina de codigo para UTF-8 para exibir acentos e emojis corretamente no terminal
chcp 65001 >nul
setlocal

echo ======================================================================
echo  🔥 VC Hot-Reload (vcth) - Compilador Continuo de Templates
echo ======================================================================
echo.
echo  💡 Como funciona:
echo   1. Este script roda um laco de repeticao infinito.
echo   2. A cada 30 segundos, ele aciona o motor de templates do SFIA.
echo   3. O motor inteligente confere a pasta '_tmpl' e so compila os 
echo      arquivos que foram salvos/modificados desde a ultima verificacao.
echo   4. O artefato gerado vai para '_mds' e abre no seu navegador (Auto-Preview).
echo.
echo ======================================================================
echo.

:loop
echo 🔄 [%TIME%] Verificando atualizacoes nos templates...
:: Executa o microapp isolado pelo uv a partir da raiz do projeto
uv run --directory "%VC_ROOT%\sfia_safic" main.py template

echo.
:: O comando CHOICE aguarda 30 segundos (/T 30). 
:: Se o tempo acabar, ele escolhe o padrao 'C' (/D C) de Continuar.
:: Se o usuario pressionar 'Q', ele registra a opcao 2 e sai do programa.
choice /C CQ /T 30 /D C /N /M "⏳ Aguardando 30s para proxima checagem... (Pressione [Q] para Sair do Hot-Reload)"

:: A avaliacao de errorlevel no .bat deve sempre ser do maior para o menor
if errorlevel 2 goto :end
if errorlevel 1 goto :loop

:end
echo.
echo 🛑 Hot-Reload encerrado com sucesso.
echo.
endlocal