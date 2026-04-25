---
name: vc
version: "0.4.9"
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
| `core/` | Central de Comando (FastAPI, Launchpad, Terminal Web, Editor Monaco e Scripts base) | Linux/Win |
| `sfia_safic/` | Workspace setup, Build SIA, Relatórios e Compilador de Templates | Linux/Win |
| `sfia_credAcCust/` | Relatórios e-CredAc Custeio (PowerBI → SQLite) | Linux/Win |
| `importador_safic/` | ETL: MDF/SQL Server → SQLite OSF (com merge dinâmico) | **MDF Win Only** |
| `exportador/` | Query SQLite → Excel / MD / TSV ad-hoc | Linux/Win |
| `utils/` | Mapeador FK/PK, dump_code, sqlite2md, pmcloud | Linux/Win |

---

## Regras de ouro (para a IA)

**Fazer:**
- **a única forma de iniciar o VC é através de `terminal.bat`**
- Usar `uv run` sempre, nunca `python` direto
- Cada microapp é editado de forma isolada
- O contexto atual do sistema é sempre guiado pelo arquivo `var/sfia_config.toml` (o CLI lida com isso sozinho).
- Arquivos temporários e logs gravados em `var/` (ignorada pelo git)
- Templates: O motor de templates (template_engine.py) usa a arquitetura Lexical/Linear (Passada única de cima para baixo). O estado das variáveis se mantém no documento. A definição conceitual completa dos templates está na pasta raiz, em [SFIA_TMPL_SPEC.md](SFIA_TMPL_SPEC.md).
- Manter o isolamento: alterações num microapp não devem afetar o `pyproject.toml` de outro.
- Imports entre módulos do mesmo microapp usam caminhos relativos simples
- **Estrutura de Templates e Temporários**: Os arquivos fontes dos templates devem ficar na pasta `_tmpl/`. Arquivos temporários ad-hoc do sistema devem ir para `var/temp/`.
- **Arquitetura Core**: Funções e utilitários que não dependam de bibliotecas externas pesadas e que servem a múltiplos microapps devem ser adicionadas em `core/lib/vccore.py`. Scripts `.bat` utilitários globais devem ir para `core/Scripts/`.

**Não fazer:**
- Não criar `config.toml` na raiz (foi removido intencionalmente)
- Não sugerir instalação global de pacotes (`pip install`). Sempre modificar o `pyproject.toml` e usar `uv add`.

---

## Entrypoint rápido (exemplo para Windows)

```bat
terminal.bat          # abre o terminal com os doskeys configurados
vc sfia_safic main.py report --dir ../var
exp --db var/sia.sqlite --sql query.sql --out resultado.xlsx
```
