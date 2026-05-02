---
name: vc
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

- Automação do ciclo de auditoria fiscal: ingestão de dados brutos (otimizados para performance) → SQLite → Templates Dinâmicos (`*.tmpl.md`) em Hot-Reload → HTML navegável interativo.
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
| `core/` | Central de Comando (FastAPI, Launchpad, Terminal Web, Bibliotecas Globais e Scripts base) | Linux/Win |
| `sfia_safic/` | Workspace setup, Build SIA, Relatórios e Compilador de Templates | Linux/Win |
| `sfia_credAcCust/` | Relatórios e-CredAc Custeio (PowerBI → SQLite) | Linux/Win |
| `importador_safic/` | ETL: MDF/SQL Server → SQLite OSF (com merge dinâmico inteligente) | **MDF Win Only** |
| `exportador/` | Query SQLite → Excel / MD / TSV ad-hoc | Linux/Win |
| `utils/` | Mapeador FK/PK, dump_code, sqlite2md, pmcloud | Linux/Win |

---

## Regras de ouro (para a IA)

**Fazer:**
- **A forma primária de iniciar o VC é através de `terminal.bat`**.
- O `terminal.bat` delega a autoconfiguração ao `core/Scripts/vc_env.bat`, que calcula o `VC_ROOT` dinamicamente (sem barra no final) e injeta o `PYTHONPATH`.
- Ferramentas são acionadas através de scripts `.bat` em `core/Scripts`. O Launchpad Web lista esses scripts automaticamente lendo os marcadores de Frontmatter `:: DESC:` e `:: ARGS:` no topo dos arquivos `.bat`.
- O script `vc.bat` orquestra as chamadas executando `uv run --directory "%VC_ROOT%\%MICROAPP%" %*`. O uso de `%*` combinado com laços internos garante que infinitos parâmetros possam ser passados, onde `%MICROAPP%` é a pasta do projeto desejada, que chamaremos de microapp, que é executado de forma isolada, cada uma delas com seu `pyproject.toml`, `.venv` e `uv.lock`.
- O contexto atual do sistema é sempre guiado pelo arquivo `var/sfia_config.toml` (o CLI lida com isso sozinho).
- Arquivos temporários e logs gravados em `var/` (ignorada pelo git).
- Templates: O motor de templates (`template_engine.py`) usa a arquitetura Lexical/Linear (Passada única de cima para baixo). O estado das variáveis se mantém no documento. A definição conceitual completa dos templates está na pasta raiz, em [SFIA_TMPL_SPEC.md](SFIA_TMPL_SPEC.md).
- Manter o isolamento: alterações num microapp não devem afetar o `pyproject.toml` de outro.
- **Arquitetura Core:** Funções vitais transversais devem ser isoladas em `core/lib/vccore.py` (caminhos, logs) e `core/lib/to_markdown.py`.
- Os microapps devem importar as bibliotecas centrais de forma limpa, utilizando *namespaces* explícitos (Ex: `import core.lib.vccore as vc` ou `import core.lib.to_markdown as vctm`).

**Não fazer:**
- Não usar gambiarras como `sys.path.insert()` para importar módulos. Confie no `PYTHONPATH` injetado pelo sistema.
- Não usar `print()` genéricos para outputs do sistema. Sempre importar e utilizar o `vc.log(mensagem, level="INFO")` para garantir a padronização de cores e alertas ANSI no terminal.
- Não criar `config.toml` na raiz (foi removido intencionalmente).
- Não sugerir instalação global de pacotes (`pip install`). Sempre modificar o `pyproject.toml` e usar `uv add`.

---

## Entrypoint rápido (exemplo para Windows)

```bat
terminal.bat                      # abre o terminal com ambiente hidratado
vc sfia_safic main.py report      # utiliza contexto do TOML ativo
vc utils sqlite2md.py --db var/sia.sqlite --sql query.sql --out relatorio.md
```