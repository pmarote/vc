# SIA Gerador Simplificado

Projeto em Python puro para gerar o banco de dados SIA a partir do banco OSF e de planilhas Excel, e posteriormente gerar relatórios em Markdown.

## Como usar

1. Coloque o arquivo `osf13013199258.sqlite` e a planilha `TrabPaulo.xlsm` na raiz do projeto.
2. Execute o `terminal.bat` para carregar o ambiente.
3. Para construir o banco SIA:
   ```bash
   uv run main.py --build
   ```
4. Para gerar os relatórios em Markdown:

```bash
uv run main.py --report
```
