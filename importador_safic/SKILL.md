---
name: importador_safic
description: Converte MDFs do SAFIC para SQLite e consolida as tabelas de auditoria.
type: standalone_tool
---

# Extração e Merge SAFIC

Esta automação utiliza o `win32com` para acessar o LocalDB do Windows.

```bash
# 1. Converter os bancos (Exemplo para o principal e o Dfe)
uv run main.py convert --mdf "C:\caminho\13013199258.mdf" --ldf "C:\caminho\13013199258.ldf" --out "13013199258_Principal.db3"
uv run main.py convert --mdf "C:\caminho\13013199258_Dfe.mdf" --ldf "C:\caminho\13013199258_Dfe.ldf" --out "13013199258_Dfe.db3"

# 2. Consolidar no banco de auditoria
uv run main.py merge --osf "13013199258" --arquivos "13013199258_Principal.db3" "13013199258_Dfe.db3"

```