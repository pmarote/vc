# 🚀 VC - Vibe Coding Microapps

Coleção de Microapps elaborados em vibe coding. O termo **VC** reflete a filosofia de **Vibe Coding**.

VC não é um bloco monolítico, mas ferramentas independentes que compartilham uma vizinhança.

- **Isolamento dos Microapps:** Cada pasta tem o seu próprio ficheiro `pyproject.toml`, assim como cada pasta tem seu próprio `.venv`, por isso utilizamos o `uv` de forma independente dentro de cada pasta. Exemplo:

```bash
cd importador_safic
uv sync
```

Historicamente, o projeto **VC** é uma suíte de ferramentas de auditoria fiscal e processamento de dados estruturada como um monorepo de microapps. Este projeto evoluiu de scripts isolados (anteriormente sob os nomes **SIA** e **sfia**) para uma arquitetura organizada onde cada utilitário possui seu próprio ambiente isolado, mas compartilha uma configuração global.

O isolamento de microapps é usado basicamente para economizar tokens e focar em cada uma das funcionalidades de forma objetiva.

### Gestão de Dependências

Para garantir a estabilidade e evitar conflitos entre as ferramentas:

**Como executar um projeto:**
Navegue para a pasta do projeto desejado e utilize o `uv` para preparar o ambiente. Exemplo:

```bash
cd importador_safic
uv sync
```

## 🏷️ Versionamento

A versão global deste conjunto de aplicações é controlada através do ficheiro [CHANGELOG.md](CHANGELOG.md). As microaplicações individuais podem conter as suas próprias versões nos seus respetivos ficheiros `pyproject.toml`, mas a "versão do pacote" atual encontra-se documentada no histórico central.

## 📋 Visão Geral
O **SIA** e depois o **sfia**, agora partes deste vc, é um sistema modular de auditoria fiscal projetado para automatizar o ciclo de vida dos dados de auditoria, desde a ingestão de bases brutas até a geração de relatórios sofisticados e auditáveis. O foco está na **produtividade, transparência e reprodutibilidade**, operando sem dependências globais no sistema.

### 📌 Objetivo
Transformar bancos SQLite brutos em relatórios consistentes e auditáveis usando apenas **Python + Markdown + SQL**.

## 📂 Estrutura do Repositório

Este repositório está estruturado como um conjunto de **projetos independentes**. Cada subdiretório (como `importador_safic`, `sfia_safic`, `exportador`, `sfia_credAcCust`, etc.) funciona como uma microaplicação isolada.

```text
vc/
├── config.toml           # Configurações globais (Caminhos, Versão)
├── terminal.bat          # Porta de entrada (Atalhos e Ambiente)
├── .gitignore            # Regras de exclusão globais
├── data/                 # Bases de dados brutas (Excel/SQLite)
├── var/                  # Saídas (Logs, Temp, Relatórios MD/HTML)
│   ├── logs/
│   └── temp/
├── exportador/           # Microapp: SQL -> Excel/MD/TSV
├── importador_safic/     # Microapp: SQL Server -> SQLite
├── sfia_credAcCust/      # Microapp: e-CredAc Custeio (BI -> SQLite)
├── sfia_safic/           # Microapp: Auditoria SAFIC (OSF -> SIA)
├── utils/                # Microapp: Toolkit (Dump, SQLite2MD, MD2HTML)
└── modelo/               # Template genérico para novos microapps
```

---

## 🛠️ Configuração e Ambiente

O projeto utiliza o **UV** para gerenciamento de pacotes e isolamento de versões do Python.

### Terminal de Trabalho (`terminal.bat`)
O arquivo `terminal.bat` na raiz configura o ambiente UTF-8 e define atalhos (**doskeys**) para facilitar o uso:
* `vc`: Atalho para rodar qualquer microapp (`uv run --directory ...`).
* `vcdump`: Gera o consolidado de código do projeto para contexto de IA.
* `sqlite2md`: Atalho rápido para o utilitário de inspeção de banco de dados.

### Configuração Global
* Cada pasta tem seu microapp, isolado.
* Os dados da auditoria ficam em pastas externas, ligadas ao trabalho de auditoria.
* As variáveis dos microapps, onde necessárias, ficam centralizadas `var`, que tem as subpastas `logs` e `data`

---

## 📦 Microapps Principais

### 1. [sfia_credAcCust] - e-CredAc Custeio
Especializado em processar planilhas de Business Intelligence para auditoria de custeio:
* **build**: Ingestão de planilhas como *Movimentação*, *Tabelas Gerais* e *Lançamentos Complementares* em um banco SQLite (`siaCredAc.sqlite`).
* **report**: Gera relatórios de amostragem, listagens completas e **Confrontos** (GIA vs Custeio por Mês/CFOP).

### 2. [sfia_safic] - Auditoria Fiscal
O motor original de auditoria:
* **build**: Transforma o banco de dados da OSF em um banco SIA enriquecido com Views de inteligência e Índices de aceleração.
* **report**: Gera relatórios detalhados de inconsistências e análises econômicas.

### 3. [utils] - Toolkit de Suporte
Coleção de utilitários para o dia a dia:
* [cite_start]**dump_code**: Consolida o código-fonte em um único Markdown para análise de IA[cite: 9].
* **sqlite2md**: Gera documentação técnica de qualquer banco SQLite.
* **md2html**: Converte relatórios Markdown em arquivos HTML *standalone* com CSS embutido.

### 4. [exportador] - Extração Flexível
Permite extrair resultados de consultas SQL complexas para múltiplos formatos:
* Suporta **Excel (.xlsx)** com formatação automática, **TSV (.txt)** e **Markdown (.md)**.
* Permite o uso de `ATTACH DATABASE` para cruzar dados de múltiplos bancos via linha de comando.

---

## 🚀 Como Iniciar

1. Clone o repositório.
2. Execute o arquivo `terminal.bat` na raiz.
3. Use os comandos configurados. Exemplos:
   ```bash
   # Gerar banco de custeio
   vc sfia_credAcCust main.py build --src ../data/BI_Excel --out ../var/siaCredAc.sqlite

   # Gerar relatórios de auditoria
   vc sfia_credAcCust main.py report --dir ../var

   # Exportar um cruzamento de dados para Excel
   vc exportador main.py --db var/sia.sqlite --attach var/osf.sqlite osf --sql "query.sql" --out var/resultado.xlsx
   ```

---
**Versão Atual:** Ver CHANGELOG.md | **Filosofia:** Vibe Coding 🌊