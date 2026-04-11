# 🚀 VC - Vibe Coding Microapps

Coleção de Microapps elaborados em vibe coding. O termo **VC** reflete a filosofia de **Vibe Coding**.

VC não é um bloco monolítico, mas ferramentas independentes que compartilham uma vizinhança.

- **Isolamento dos Microapps:** Cada pasta tem o seu próprio ficheiro `pyproject.toml`, assim como cada pasta tem seu próprio `.venv`, por isso utilizamos o `uv` de forma independente dentro de cada pasta. Exemplo:

```bash
cd importador_safic
uv sync
```

Historicamente, o projeto **VC** é uma suíte de ferramentas de auditoria fiscal e processamento de dados estruturada como um monorepo de microapps. Este projeto evoluiu de scripts isolados (anteriormente sob os nomes **SIA** e **sfia**) para uma arquitetura organizada onde cada utilitário possui seu próprio ambiente isolado, mas compartilha vizinhanças.

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
├── CHANGELOG.md        # Histórico de versões
├── README.md           # Este ficheiro
├── terminal.bat        # Entrypoint interativo e doskeys do ambiente Windows
├── sfia_safic/         # [Microapp] Automação e relatórios de auditoria SAFIC (->OSF SAFIC->SIA/sfia.sqlite)
├── sfia_credAcCust/    # [Microapp] Automação e relatórios e-CredAc Custeio (->PowerBI->SQLite)
├── importador_safic/   # [Microapp] ETL (MDF/SQL Server -> SQLite OSF) 
├── exportador/         # [Microapp] Utilitário flexível de extração (SQL -> Excel/MD/TSV)
├── sfiaweb/            # [Microapp] Servidor web local (FastAPI) para leitura e anotação em relatórios
├── ollama_analyst/     # [Microapp] Integração com LLMs locais para análise em lote de auditorias
├── utils/              # [Microapp] Ferramentas de suporte (Dumper, MD2HTML, Scraper, Gestão de Disco, etc)
└── var/                # (Pasta Ignorada) Log, config_auditoria.toml, temp e arquivos diversos
    ├── logs/
    └── temp/
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
* As variáveis dos microapps, onde necessárias, ficam centralizadas na raiz, pasta `var`, que tem as subpastas `logs` e `tmp`

---

## 🛠️ Microapps (Ecossistema)

### 1. [importador_safic] - O Motor de Ingestão
Ferramenta para converter bancos brutos do SQL Server (`.mdf`) ou arquivos pesados de texto em bancos SQLite (`osf*.sqlite`) padronizados para o motor do VC.

### 2. [sfia_safic] & [sfia_credAcCust] - Os Auditores
A inteligência fiscal. Orquestra a execução da auditoria:
* **build**: Transforma o banco de dados da OSF em um banco SIA enriquecido com Views de inteligência e Índices de aceleração.
* **report**: Gera relatórios detalhados de inconsistências e análises econômicas. Suporta caching físico (`item[osf].sqlite`) para ganho extremo de performance.
* **Menus Interativos**: Gera arquivos HTML (`menu_relatorios.html`) para anotações locais dinâmicas via `contenteditable`.

### 3. [sfiaweb] - Interface Dinâmica
Um servidor FastAPI ultraleve servindo uma interface web moderna:
* **Leitura Direta**: Consome arquivos .md gerados pelas auditorias diretamente do Drive de trabalho.
* **Anotações Inteligentes**: Permite edição ao vivo do relatório gerado com auto-salvamento (Ctrl+S).

### 4. [ollama_analyst] - Análise de IA Local
Microapp dedicado a extrair insights de auditoria usando inteligência artificial:
* **Vibe Coding Nativo**: Processa lotes de prompts/relatórios enviando para modelos rodando em máquina local (Ollama).
* **Eficiência**: Realiza o flush automático de memória (RAM/VRAM) após as rotinas pesadas.

### 5. [utils] - Toolkit de Suporte
Coleção de utilitários para o dia a dia:
* **dump_code**: Consolida o código-fonte em um único Markdown para análise de IA.
* **scan_pastas**: Mapeador de consumo de disco, gerando relatórios de diretórios pesados.
* **sqlite2md**: Gera documentação técnica de qualquer banco SQLite.
* **md2html**: Converte relatórios Markdown em arquivos HTML *standalone* com CSS embutido.
* **visualizador_md.html**: Leitor Standalone com interface Drag-and-Drop, otimizado para tabelas Markdown massivas.
* **aiim.py**: Scraper automatizado para extração em lote de Autos de Infração (AIIM) do portal da SEFAZ, com persistência relacional em banco de dados SQLite e download automático de PDFs de decisões.
* **pmcloud.py**: Sincronizador de arquivos conectado à sua nuvem privada via API PHP. Implementa backups incrementais com versionamento point-in-time, desduplicação inteligente baseada em SQLite e exclusão de arquivos órfãos via Garbage Collector. 

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
**Versão Atual:** Ver [CHANGELOG.md](CHANGELOG.md) | **Filosofia:** Vibe Coding 🌊