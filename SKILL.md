---
name: vc
version: "0.4.7"
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

- Automação do ciclo de auditoria fiscal: ingestão de dados brutos → SQLite → Templates Dinâmicos (`*.tmpl.md`) → HTML navegável interativo.
- Microapps isolados que compartilham apenas uma pasta raiz ("vizinhança").
- Filosofia **Text-First**: sem GUI complexa acoplada, sem dependências globais, uso intensivo de YAML Frontmatter e Markdown para anotação.

## O que não é

- Não é um pacote Python instalável (sem `pip install vc`)
- Não possui painéis pesados de BI; o HTML gerado é focado em leitura estruturada e exportação fluida.
- Não tem banco de dados centralizado; cada auditoria tem seus próprios `.sqlite` isolados por *workspace* e orquestrados por `init`.

---

## Microapps

| Pasta | Função | SO |
|---|---|---|
| `sfiaweb/` | Estação de Trabalho (FastAPI local, Consultas SQL e Visualizador MD) | Linux/Win |
| `sfia_safic/` | Workspace setup, Build SIA, Relatórios e Compilador de Templates | Linux/Win |
| `sfia_credAcCust/` | Relatórios e-CredAc Custeio (PowerBI → SQLite) | Linux/Win |
| `importador_safic/` | ETL: MDF/SQL Server → SQLite OSF (com merge dinâmico) | **MDF Win Only** |
| `exportador/` | Query SQLite → Excel / MD / TSV ad-hoc | Linux/Win |
| `utils/` | Mapeador FK/PK, dump_code, sqlite2md, pmcloud | Linux/Win |

---

## Regras de ouro (para a IA)

**Fazer:**
- Usar `uv run` sempre, nunca `python` direto
- Cada microapp é editado de forma isolada
- O contexto atual do sistema é sempre guiado pelo arquivo `var/sfia_config.toml` (o CLI lida com isso sozinho).
- Arquivos temporários e logs gravados em `var/` (ignorada pelo git)
- Manter o isolamento: alterações num microapp não devem afetar o `pyproject.toml` de outro.
- Imports entre módulos do mesmo microapp usam caminhos relativos simples

**Não fazer:**
- Não criar `config.toml` na raiz (foi removido intencionalmente)
- Não sugerir instalação global de pacotes (`pip install`). Sempre modificar o `pyproject.toml` e usar `uv add`.
- Não inserir lógicas interativas nos relatórios básicos em Markdown. A interatividade pertence ao frontend (`sfiaweb`).

---

## Entrypoint rápido (exemplo para Windows)

```bat
terminal.bat          # abre o terminal com os doskeys configurados
vc sfia_safic main.py report --dir ../var
exp --db var/sia.sqlite --sql query.sql --out resultado.xlsx
```
