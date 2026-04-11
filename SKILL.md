---
name: vc
version: "0.4.4"
type: monorepo
stack: python, sqlite, uv, markdown, html
os: windows
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
| `sfia_safic/` | Build do banco SIA + relatórios SAFIC (OSF → SIA) |
| `sfia_credAcCust/` | Relatórios e-CredAc Custeio (PowerBI → SQLite) |
| `importador_safic/` | ETL: MDF/SQL Server → SQLite OSF (Windows only, pywin32) |
| `exportador/` | Query SQLite → Excel / MD / TSV |
| `utils/` | dump_code, sqlite2md, md2html |

---

## Regras de ouro (para a IA)

**Fazer:**
- Usar `uv run` sempre, nunca `python` direto
- Cada microapp é editado de forma isolada — não criar dependências entre pastas
- Arquivos temporários e logs gravados em `var/` (ignorada pelo git)
- Imports entre módulos do mesmo microapp usam caminhos relativos simples
- `sfia_safic/reports/` contém os reporters individuais; o orquestrador é `reporter.py`

**Não fazer:**
- Não criar `config.toml` na raiz (foi removido intencionalmente)
- Não instalar pacotes globalmente; sempre adicionar em `pyproject.toml` do microapp
- Não misturar lógica de relatório dentro de `builder.py`
- Não usar `pandas` no `exportador` (ele usa apenas `sqlite3` + `openpyxl`), porque `pandas` adiciona muita complexidade que não precisa no `exportador`
- Não sugerir migrações para banco relacional externo ou ORM

---

## Entrypoint rápido

```bat
terminal.bat          # abre o terminal com os doskeys configurados
menu                  # abre menu_relatorios.html no navegador
vc sfia_safic main.py report --dir ../var
exp --db var/sia.sqlite --sql query.sql --out resultado.xlsx
```
