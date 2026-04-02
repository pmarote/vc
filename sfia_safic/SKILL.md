# SKILL: SIA Gerador Simplificado

**Objetivo**: Manter a simplicidade. Este projeto não utiliza parseadores de `.md` para executar código. Todo o SQL está diretamente codificado nos arquivos Python (`builder.py` e `reporter.py`).

**Arquitetura**:
- `main.py`: CLI que roteia as ações.
- `builder.py`: Conecta no banco alvo (`sia...sqlite`), anexa o banco origem (`osf...sqlite` usando `ATTACH DATABASE`), lê o Excel com `pandas` e executa os DDLs/DMLs.
- `reporter.py`: Executa `SELECTs` no banco SIA e formata a saída em Markdown usando manipulação básica de strings.
2. Códigos Python