@echo off
:: Inicia o servidor web em uma nova janela para liberar o terminal de trabalho
:: O título deixa a janela "bonitinha" e o cmd /c garante que ela feche ao encerrar o servidor
start "🌍 VC - Servidor Web" cmd /c "uv run --directory "%VC_ROOT%\core" main.py serve %*"