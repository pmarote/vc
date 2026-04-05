# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [0.4.4] - 2026-04
- versão em desenvolvimento

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

