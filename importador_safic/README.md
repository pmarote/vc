# Importador SAFIC

Ferramenta independente para extrair bancos de dados do sistema SAFIC (SQL Server `.mdf`) e consolidá-los em um único banco SQLite focado em auditoria.

## Fluxo de Trabalho
1. **Conversão Bruta (`mdf2sqlite.py`):** Conecta ao LocalDB, anexa o `.mdf` e copia 100% das tabelas para um arquivo SQLite (`.db3`) intermediário.
2. **Filtragem e Merge (`importador_safic.py`):** Lê os `.db3` intermediários, filtra apenas as tabelas mapeadas para auditoria (adicionando os prefixos `Dfe_`, `DocAtrib_`, etc.) e consolida tudo no banco final `osf[NUMERO].sqlite`.

## Como rodar
Utilize o `main.py` como ponto de entrada CLI via `uv`:
```bash
uv run main.py -h