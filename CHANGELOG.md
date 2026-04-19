# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [0.4.7] - 2026-04
- versão em desenvolvimento

## [0.4.6] - 2026-04-19

### Arquitetura e Gestão de Ambiente
- **Versionamento Centralizado:** Introdução do `pyproject.toml` na raiz para controle global da versão 0.4.6.
- **Isolamento Total:** Configuração de `pyproject.toml` individuais por microapp, garantindo que o `uv` crie ambientes `.venv` isolados e sob demanda em cada pasta.
- **Terminal Windows v0.4.6:** Refatoração do `terminal.bat` com suporte a caminhos absolutos (resolução de pasta pai), atalhos de navegação rápida (`root`, `utils`, `sfia`, etc.) e suporte a parâmetros `$*` para ferramentas externas (CudaText, DB Browser).

### Microapp `utils` (Refatoração CLI)
- **Orquestrador `main.py`:** Transformado em um seletor de ferramentas que não depende mais de arquivo de configuração fixo.
- **Auto-explicação:** Novo comando `list` que executa automaticamente o `-h` de todos os scripts da pasta para apresentar as funcionalidades ao usuário.
- **Scripts Independentes:** `dump_code.py` e `sqlite_dump.py` agora operam como CLIs autônomas com seus próprios argumentos de linha de comando.

### Microapp `sfia_safic` (Pipeline Inteligente)
- **Persistência de Contexto:** Criação do `sfia_config.toml` na pasta `var`, permitindo que o pipeline "lembre" da pasta de trabalho sem necessidade de repetir o parâmetro `--dir`.
- **Estrutura Automática de Pastas:** Organização automática do workspace em subpastas prefixadas (`_dbs`, `_xls`, `_mds`).
- **Movimentação Automática:** O sistema agora detecta o arquivo `osf*.sqlite` na raiz e o organiza automaticamente dentro de `_dbs/`.
- **Performance no Builder:** Injeção de PRAGMAs de performance no SQLite e tratamento de caminhos cross-platform (Windows/Linux).

### Microapp `sfiaweb` (Explorer & Viewer)
- **File Explorer Web:** Transformação da interface em um navegador de arquivos completo, mostrando nome, data e tamanho.
- **Navegação Restrita:** Implementada segurança para navegação apenas dentro do `work_dir` definido.
- **Renderizador Integrado:** Integração do `markdown-it.html` para renderização fluida de arquivos `.md` com suporte a Mermaid, emojis e callouts.
- **Otimização de UI:** Implementada quebra de linha inteligente em tabelas Markdown e eliminação de "piscadas" visuais durante o carregamento da interface.
- **Gestão de Processo:** Adicionado botão de desligamento (Shutdown) do servidor via interface web.

## [0.4.5] - 2026-04-17

### Arquitetura de Dados e Performance (Data Marts)
- **Data Mart de Operações (`oper.py`):** Refatoração profunda na geração do relatório de operações. Eliminação de queries repetitivas através da criação dinâmica de um banco SQLite analítico dedicado (`oper_base.sqlite`) diretamente na pasta da auditoria.
- **Integração de Exportação Direta:** O relatório de operações agora aciona dinamicamente o microapp `exportador` via `sys.path`, gerando automaticamente amostras em `.xlsx` (10k linhas) e a base completa em `.txt` (TSV) lado a lado com os relatórios.
- **Flattening de Queries:** Achatamento estrutural de blocos `CASE WHEN` complexos em SQL, melhorando a legibilidade e a performance do motor SQLite, com blindagem extra contra divisão por zero (`NULLIF`).

### Relatórios Analíticos (Drill-Down e Top N)
- **Consolidação de Drill-Down (`safic_menu_det.py`):** Nova arquitetura relacional para detalhamento de notas. O script agora cria uma tabela persistente (`safic_drilldown`) no banco principal.
- **Lógica de Cauda Longa:** Implementação de limite de faturas (Top 10 por grupo). O sistema utiliza CTEs e Window Functions (`ROW_NUMBER()`) para detalhar as maiores notas e agregar o restante numa linha "DEMAIS NOTAS (SOMA)".
- **Relacionamento Estrela (Star Schema):** O Excel unificado gerado no final agora se relaciona nativamente com a tabela raiz `chaveNroTudao` via `ZRowId`, permitindo um cruzamento de dados limpo e sem duplicação estrutural.
- **Ordenação Inteligente:** Implementação de extração numérica *inline* no SQL (`CAST(REPLACE(...))`) para garantir que classificações em texto (ex: `[2]`, `[10]`, `[100]`) sejam ordenadas matematicamente, e não de forma alfabética.

### UI/UX e Utilitários de Terminal
- **Comando de Limpeza Global (`vcclean`):** Nova rotina inteligente no `terminal.bat` que varre recursivamente todo o monorepo, destruindo pastas `__pycache__`, `.venv` e arquivos `uv.lock` obsoletos, resetando o ambiente de forma rápida sem fechar o terminal.
- **Quebra de Texto Inteligente:** Expansão da formatação de strings longas (observações e descrições) via SQL nativo, suportando a injeção de `<br>` a cada 30/40 caracteres até o limite de 400 caracteres, finalizando com `(...CORTADO)` para não estourar as tabelas Markdown.


## [0.4.4] - 2026-04-11

### Automação e Extração de Dados (Web Scraping)
- **Lançamento do Extrator AIIM (`utils/aiim.py`):** Novo scraper para automação de leitura de Autos de Infração e Imposição de Multa do portal da SEFAZ.
  - **Integração Web:** Utiliza `requests` e `BeautifulSoup` para acessar, baixar e fazer o parseamento estruturado do HTML nativo dos extratos de processo.
  - **Armazenamento Relacional:** Persistência de dados em SQLite (`var/tit_aiims.sqlite`), modelando tabelas independentes e conectadas para a capa do `aiim`, `andamentos` e `decisoes`.
  - **Gestão de Anexos:** Identificação e download automatizado de arquivos físicos (PDFs) referentes a defesas e decisões, com padronização de nomenclatura.
  - **CLI:** Suporte a parâmetros de linha de comando (`--inicial`, `--final`, `--pasta`) para processamento em lote de faixas numéricas de autos.

### Nuvem e Sincronização
- **Lançamento do PMCloud (`utils/pmcloud.py`):** Novo utilitário de terminal para gestão e backup de arquivos de auditoria na nuvem (arquitetura Python + PHP/SQLite).
  - **Desduplicação Inteligente:** Utiliza SQLite no lado do servidor para garantir que arquivos idênticos nunca sejam armazenados em duplicidade.
  - **Transporte Otimizado:** Empacotamento efêmero em `.zip` apenas para a transferência de rede, minimizando o tráfego e requisições HTTP.
  - **Versionamento no Tempo (`-pull`):** Capacidade de restaurar pastas inteiras exatamente como estavam em uma data específica (*Point-in-Time Recovery*).
  - **Listagem e Resumo (`-ls`):** Consulta do tamanho total ocupado (com cálculo de economia da desduplicação) e histórico de backups por pasta.
  - **Garbage Collector (`-rm`):** Exclusão segura de histórico na nuvem que remove apenas arquivos físicos "órfãos", preservando dados compartilhados com outros backups e liberando espaço real no servidor.

### Interface e Relatórios Dinâmicos
- **Lançamento do sfiaweb:** Novo microapp contendo um servidor web local e ultraleve via FastAPI.
  - **Edição em Tempo Real:** Interface web com layout de dashboard, permitindo a leitura e anotação direta em relatórios Markdown via `contenteditable` com atalho de salvamento (`Ctrl+S`).
  - **Isolamento de Contexto:** Leitura dinâmica do diretório de auditoria alvo através do arquivo de configuração centralizado `var/config_auditoria.toml`.

### Análise com Inteligência Artificial
- **Lançamento do ollama_analyst:** Novo microapp dedicado à análise em lote de relatórios utilizando modelos de IA locais (ex: gemma4).
  - **Processamento em Batch:** Lê automaticamente múltiplos prompts `.md` gerados pelo sistema, envia para a API local do Ollama e salva os insights.
  - **Gestão de Memória:** Implementação de liberação forçada de VRAM/RAM (`keep_alive=0`) ao final do lote para otimização de recursos da máquina.

### Utilitários de Sistema
- **Novo Utilitário `scan_pastas.py`:** Ferramenta recursiva na pasta `utils/` para mapear diretórios que excedem um limite configurável (ex: 1GB) e gerar relatórios em Markdown, auxiliando na gestão de armazenamento dos drives de auditoria.

## [0.4.3] - 2026-04-05

### Arquitetura de Dados e Performance
- **Caching Definitivo (Data Marts):** Implementação de banco de aceleração dedicado (`item[osf].sqlite`) no `report_item`, utilizando a estratégia de ETL em estágios (Extração em Memória RAM via `PRAGMA temp_store` -> Agrupamento -> Carga) para processamento de milhões de linhas de forma instantânea.
- **Window Functions Analíticas:** Adoção massiva de `ROW_NUMBER() OVER()` para rankeamento dinâmico (Top 20 vs Demais Itens) e cálculos de porcentagens relativas (`pct`) diretamente no SQL, eliminando subconsultas custosas em `an_econ.py` e `item.py`.

### UI/UX e Ferramentas do Auditor
- **Caderno de Notas Interativo:** Criação do `menu_relatorios.html`, atuando como um *hub* local com atributos `contenteditable="true"` para que o auditor faça anotações e salve localmente (`Ctrl+S`).
- **VC Reader:** Lançamento de um visualizador de Markdown Standalone em HTML (`utils/visualizador_md.html`) com suporte a *Drag and Drop*, tabelas otimizadas para finanças e isolamento visual de metadados YAML. Integrado globalmente pelo doskey `vcmd`.

### Refatoração e Correções
- **Modularização de Reports:** O arquivo gigante `reporter.py` foi fatiado. Cada relatório de auditoria agora é um micro-módulo isolado dentro da pasta `reports/`.
- **Blindagem Markdown:** Implementação de *escapes* na função `fmt_br` (`to_markdown.py`) substituindo pipes (`|`) por `&#124;` e quebras de linha (`\n`) por `<br>`, impedindo que descrições sujas de NFes quebrem as tabelas do relatório.
- **Correção da Documentação:** O arquivo `config.toml` foi definitivamente retirado da árvore de diretórios do `README.md`, refletindo a realidade arquitetural da purificação iniciada na v0.4.2.

## [0.4.2] - 2026-04-02

### Documentação
- Consolidação do `README.md` definindo o projeto **VC** como uma coleção de microapps independentes baseada em *Vibe Coding*, mas que compartilham uma vizinhança, bem como este `CHANGELOG.md` que vai conter a versão em desenvolvimento e o histórico das anteriores.

### Alterações de Arquitetura
- **Purificação da Raiz:** Remoção do ficheiro `config.toml` da raiz para reforçar o desacoplamento total dos microapps.

## [0.4.1] - 2026-03

### Mudança do nome do projeto para VC (Vibe Coding), com microapps independentes, mas que compartilham uma vizinhança.

### Estrutura e Arquitetura
- **Desacoplamento de Microaplicações:** Formalização da estrutura onde cada subprojeto (`importador_safic`, `sfia_safic`, `exportador`, `utils`, etc.) atua de forma totalmente independente.
- **Gestão Isolada:** Definição da regra de que cada pasta deve manter o seu próprio `pyproject.toml` e ambiente virtual (`.venv`) gerido pelo `uv`.
- **Documentação Global:** Adição de um `README.md` e deste ficheiro de histórico na raiz do projeto para clarificar a arquitetura e acompanhar a versão global do monorepo.

### Correções e Ajustes nos Subprojetos (Em curso)
- Atualização dos metadados (nome e descrição) no ficheiro `pyproject.toml` do módulo `sfia_credAcCust`, que continha dados duplicados do módulo `sfia_safic`.
- Revisão das versões exigidas de Python (`requires-python`) nos diferentes ficheiros de configuração para garantir compatibilidade com as ferramentas desenvolvidas.

## [0.4.0] - 2026-03-02

### Added
- **Motor de Cookbooks (`sia.cookbook_parser`)**: Introdução do mecanismo de renderização de relatórios "Text-First". O parser lê arquivos Markdown (cookbooks), extrai blocos de código SQL, executa-os e os substitui diretamente por tabelas renderizadas no Markdown final.
- **Gerador de Configuração de Banco (`sia.utils.gen_db_config`)**: Novo utilitário de terminal para gerar automaticamente o `var/db_config.toml`, suportando o banco principal e múltiplos bancos anexados (`--attach`).
- **Explorador Automático de Dados (`sia.utils.gen_cookbook`)**: Ferramenta que varre a estrutura interna de um banco de dados SQLite desconhecido e gera dinamicamente um "cookbook exploratório" em Markdown contendo os metadados e os selects das primeiras linhas de cada tabela e view.
- **Automação de Setup de Auditoria (`prep_safic.py`)**: Script autônomo na raiz para orquestrar a inicialização de novas auditorias (copia templates `.db3` de forma segura, gera o TOML e processa o primeiro relatório base).

### Changed
- **Refatoração Visual do Markdown Exporter (`sia.to_markdown` e `sia.reporter`)**: O `RICH FOOTER` foi otimizado. Todos os metadados analíticos cruciais (data da execução, base principal, anexos ATTACH, nome do arquivo `.sql` temporário e a query original) agora ficam consolidados de forma limpa no topo do relatório, escondidos nativamente sob uma tag `<details>`, mantendo o foco visual puramente nos dados, preservando a otimização de RAM.
- **Melhoria no Diagnóstico (`sia.utils.info`)**: O script de info do sistema agora possui inteligência para ler, validar e exibir visualmente a árvore de configuração do `var/db_config.toml` (Banco Principal e Anexos), emitindo alertas visuais (🚨) caso haja parâmetros críticos faltando no ambiente.

## [0.3.9] - 2026-02-15
- **Padronização de Namespace:** A pasta raiz `/app` foi renomeada para `/sia`. O projeto agora opera como um pacote Python consolidado, permitindo chamadas via `python -m sia.<modulo>` e evitando colisões com bibliotecas globais.
- **Refatoração do `sia/core.py`:** Atualizada a lógica de detecção de caminhos para suportar o novo namespace. Adicionado suporte ao objeto `AppEnv` para incluir o caminho do pacote (`sia_package`) e a pasta de recursos (`res_dir`).
- **Evolução dos Utilitários:**
- `info.py`: Agora valida a integridade do novo namespace e destaca visualmente a raiz do projeto no `sys.path`.
- `dump_code.py`: Atualizado para capturar arquivos `.toml` e ignorar automaticamente a pasta `/var` para dumps mais limpos.
- `list_tools.py`: Implementada lógica inteligente para extrair o *help* de módulos usando o novo padrão `python -m sia...`.
- **Refatoração do `sia/reporter.py` e Exportadores:** - Atualização de todos os *imports* internos para o namespace `sia`.
- Implementação de **Type Hinting** em 100% das funções de suporte (`to_markdown.py`, `to_excel.py`).
- **Documentação de Agente (Skills):** Atualização completa das definições em `.agent/skills/` para refletir a nova arquitetura e os parâmetros obrigatórios da v0.3.9.
- **Suporte a TOML:** Inclusão de arquivos de configuração `.toml` no contexto de análise de IA através do `dump_code.py`.

## [0.3.8] - 2026-02-14
- **Criação do `app/core.py` (Single Source of Truth):** Novo módulo guardião que valida a infraestrutura na inicialização, gerencia os caminhos absolutos (`project_root`, `/var`, `/logs`, `/temp`) e carrega as configurações. Possui "auto-healing" para criar pastas ausentes.
- **Refatoração Profunda do `app.reporter`:**
  - Código limpo: consome a infraestrutura já validada pelo `core.py` em vez de adivinhar caminhos.
  - Inteligência de CLI: Infere automaticamente o formato de saída (Markdown, Excel, TSV) pela extensão do arquivo de saída (`--out`).
  - Flexibilidade de SQL: O parâmetro `--sql` agora aceita tanto a query em string quanto o caminho para um arquivo `.sql`.
  - Configuração via TOML: Conexões de banco (`main` e `attach`) foram movidas da CLI para o arquivo persistente `var/db_config.toml` (usando `tomllib` nativo do Python 3.13).
- **Melhorias Visuais no Markdown (`to_markdown.py`):** Adicionado suporte ao argumento `--title` (renderizado como H2) e inclusão automática da query SQL original em um bloco HTML retrátil (`<details>`).
- **Dashboard de Diagnóstico (`info.py`):** Totalmente reescrito. Agora gera um relatório visual por blocos (`[SISTEMA]`, `[CORE]`, `[EMBED]`), avaliando a saúde das pastas vitais, rotas de importação e presença do motor `uv`.
- **Evolução dos Utilitários Base (`/usr`):**
  - O `setup_python_embedded.bat` agora documenta no próprio terminal a arquitetura do `._pth` e atualizou os "próximos passos" para usar o padrão `uv`.
  - Substituição do script genérico de limpeza pelo novo **`clean_cache.bat`**, que atua recursivamente destruindo `__pycache__` e limpando o `/var/temp`.
- **Organização de Agentes de IA:** Reestruturação do `SKILL.md` em namespaces focados (`sia.main`, `sia.report`, `sia.util`, `setup.python-embedded`) para melhor roteamento cognitivo do IDE.
- **Fix Global:** Centralização do `sys.stdout.reconfigure(encoding='utf-8')` no `core.py` para prevenir falhas de acentuação no terminal do Windows em todos os scripts.

## [0.3.7] - 2026-02-13
- Configuração do gerenciador de pacotes `uv` para orquestrar dependências.
- Criação do `SKILL.md` (`python-embedded`) para ensinar o Agente a usar o ambiente `usr/python` corretamente e não criar venvs isolados.
- Configurações de `launch.json` e `settings.json` para injeção nativa de variáveis de ambiente no terminal do VS Code.

## [0.3.6] - 2026-02-13
- **Decisão:** Retorno ao uso do **Google Antigravity** como IDE principal.
- Reestruturação do módulo `app.reporter` (funcionalidade restaurada).
- Reinício da migração de lógica para o conceito de "cookbooks".

## [0.3.5] - 2026-02-10
- **Mudança Arquitetural Crítica:** Consolidação do ambiente Python. Agora existe apenas uma pasta `usr` centralizada, eliminando múltiplos ambientes embedded espalhados.
- Fim da estrutura de múltiplos microapps com ambientes isolados. Em outras palavras, desisti do conceito da estrutura base de **microapps**.
- Simplificação da estrutura de pastas para facilitar o reconhecimento pelo Agente.
- **Remoção:** O suporte a `tcl_tk` foi removido. O projeto agora é "Text-First". Interfaces gráficas futuras serão bibliotecas externas, que acionam o projeto/biblioteca sia.

## [0.3.4] - 2026-02-01
- Migração temporária do fluxo de trabalho para o **Gemini Web** (fora do IDE).
- Foco no desenvolvimento isolado de microapps devido a conflitos com múltiplos ambientes Python embedded no Antigravity.

## [0.3.3] - 2026-01-13

### Added
- Ferramentas de diagnóstico de ambiente.
- Suporte temporário às ferramentas integradas do Antigravity (devido a instabilidade com a arquitetura anterior).
- Arquivos de configuração `.vscode` iniciais para o Antigravity.

### Changed
- Melhorias no template base dos microapps.

## [0.3.2] - 2026-01-01
### Added
- Estrutura base de **microapps**.
- Definição dos contratos de Entrada/Saída (Input/Output protocols).

