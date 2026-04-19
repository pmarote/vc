---
name: vc
version: "0.4.6"
type: monorepo
stack: python, sqlite, uv, markdown, html
os: windows, linux
---

# VC — Vibe Coding Microapps

Monorepo de microapps independentes para **auditoria fiscal** em Python.
Cada microapp tem seu próprio `pyproject.toml` + `.venv` gerido pelo `uv`.
Para detalhes completos, leia o [README.md](README.md).

---

## O que é

- Automação do ciclo de auditoria fiscal: ingestão de dados brutos → SQLite → relatórios Markdown → HTML navegável
- Microapps isolados que compartilham apenas uma pasta raiz ("vizinhança")
- Filosofia **Text-First**: sem GUI, sem dependências globais, tudo reproduzível

## O que não é

- Não é um pacote Python instalável (sem `pip install vc`)
- Não é um servidor web; os HTMLs rodam localmente no browser
- Não tem banco de dados centralizado; cada auditoria tem seus próprios `.sqlite`

---

## Microapps

| Pasta | Função |
|---|---|
| `sfia_safic/` | Build do banco SIA + relatórios SAFIC (OSF → SIA) | Linux/Win |
| `sfia_credAcCust/` | Relatórios e-CredAc Custeio (PowerBI → SQLite) | Linux/Win |
| `importador_safic/` | ETL: MDF/SQL Server → SQLite OSF | **Windows Only** |
| `exportador/` | Query SQLite → Excel / MD / TSV | Linux/Win |
| `utils/` | dump_code, sqlite2md, md2html | Linux/Win |
| `sfiaweb/` | Servidor local FastAPI para relatórios | Linux/Win |

---

## Regras de ouro (para a IA)

**Fazer:**
- Usar `uv run` sempre, nunca `python` direto
- Cada microapp é editado de forma isolada
- Arquivos temporários e logs gravados em `var/` (ignorada pelo git)
- Manter o isolamento: alterações num microapp não devem afetar o `pyproject.toml` de outro.
- Imports entre módulos do mesmo microapp usam caminhos relativos simples

**Não fazer:**
- Não criar `config.toml` na raiz (foi removido intencionalmente)
- Não sugerir instalação global de pacotes (sempre via `uv add`).
- Não instalar pacotes globalmente; sempre adicionar em `pyproject.toml` do microapp

---

## Entrypoint rápido (exemplo para Windows)

```bat
terminal.bat          # abre o terminal com os doskeys configurados
vc sfia_safic main.py report --dir ../var
exp --db var/sia.sqlite --sql query.sql --out resultado.xlsx
```
