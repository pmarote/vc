# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.


## [0.5.1] - 2026-04
- versão em desenvolvimento

## [0.5.0] - 2026-04

Esta versão consolida a arquitetura do ecossistema VC, centralizando a inteligência em bibliotecas globais, desacoplando módulos e transformando o terminal e o Launchpad em ferramentas dinâmicas de altíssima produtividade.

### 🧠 Arquitetura VC Core & Bibliotecas Globais
- **Consolidação do `vccore.py`**: Estabelecido como a "Single Source of Truth" (Fonte Única de Verdade). Agora centraliza a descoberta de caminhos (`VC_ROOT`, `VAR_DIR`), o sistema de cores ANSI e o padronizador de logs `vc.log()`, substituindo `print()` em todo o sistema.
- **Desacoplamento do Exportador Markdown**: O antigo `to_markdown.py` foi extraído do `sfia_safic`, purificado de sua lógica de CLI e promovido a biblioteca central em `core/lib/to_markdown.py`. 
- **Fim do `sys.path.insert`**: Com a configuração correta do `PYTHONPATH` gerida pelo `vc_env.bat`, os microapps agora importam as bibliotecas nativamente (ex: `import core.lib.vccore as vc`), eliminando hacks de rotas e melhorando a segurança.

### 💻 CLI, Terminal e Scripts (`core/Scripts`)
- **Autolocalização de Ambiente**: O `vc_env.bat` foi reescrito para descobrir o `VC_ROOT` dinamicamente subindo na árvore de diretórios, resolvendo caminhos absolutos de forma limpa (sem barra no final), o que evita erros de *dupla barra* (`\\`) no Windows.
- **`vc.bat` Sem Limites**: O script de execução principal foi reescrito utilizando laços de repetição (`shift` com `goto:loop`), quebrando a limitação histórica de 9 parâmetros do DOS e permitindo a passagem de infinitos argumentos com preservação de aspas.
- **Otimização do `vcclean.bat`**: Refatorado para ler o caminho base de forma segura, limpando instantaneamente pastas `__pycache__`, `.venv` e arquivos `uv.lock`.

### 🚀 Launchpad Web (Front-end e Hub)
- **Painel de Ferramentas Dinâmico**: O Launchpad (`index.html`) agora lê a pasta `core/Scripts` e converte automaticamente os scripts `.bat` em botões clicáveis.
- **Frontmatter em `.bat`**: Scripts do sistema agora suportam metadados como `:: DESC:` (Descrição) e `:: ARGS:` (Argumentos esperados). Se um script exigir argumentos, o Launchpad renderiza um campo de texto interativo (*input*) dentro do card da ferramenta.
- **Janelas Inteligentes**: Ao executar uma ferramenta pelo Launchpad, o servidor abre um novo console do Windows, hidrata o ambiente (`vc_env.bat`), executa a ação e introduz um `timeout` (30s) elegante com mensagem personalizada antes de fechar a janela, permitindo a leitura de logs.

### 📊 Microapp `sfia_safic` e Utilities
- **Tela de Ajuda Didática (`-h`)**: O `main.py` do Safic agora intercepta o comando `-h` antes do `argparse`, entregando uma interface colorida, didática e contextualizada, avisando se há um workspace ativo e explicando os fluxos com regras de ouro.
- **Independência do Motor de Templates**: O `template_engine.py` foi refatorado para importar o `vctm.export_markdown` diretamente da biblioteca central, cortando totalmente sua dependência estrutural da pasta de relatórios.
- **Novo Utilitário `sqlite2md.py`**: O modo standalone do conversor de Markdown renasceu como uma ferramenta independente na pasta `utils/`, consumindo a biblioteca central de forma limpa.


## [0.4.9] - 2026-04
Esta versão representa um salto significativo na consolidação arquitetural do projeto como um Ecossistema, transformando o antigo `sfiaweb` num `core` unificado e trazendo o poder da interface de linha de comando nativamente para a Web.
*(... restante do changelog mantido intacto ...)*

## [0.4.9] - 2026-04
Esta versão representa um salto significativo na consolidação arquitetural do projeto como um Ecossistema, transformando o antigo `sfiaweb` num `core` unificado e trazendo o poder da interface de linha de comando nativamente para a Web.

### Arquitetura "VC Core" e Bibliotecas
- **Nascimento do `core/`:** A antiga pasta `sfiaweb` evoluiu para `core/`, atuando como cérebro do monorepo. Hospeda o servidor web, o novo orquestrador CLI e bibliotecas compartilhadas.
- **Biblioteca Central (`core/lib/vccore.py`):** Criada para evitar repetição de código. Centraliza caminhos vitais (`ROOT_DIR`, `VAR_DIR`, `USR_DIR`), formatação de logs ANSI, leitura dinâmica da versão a partir do `pyproject.toml` raiz e validação de segurança do ambiente.
- **Novo Orquestrador (`core/main.py`):** Absorveu as funções de `vc_manager.py` e do antigo `sc.py`. Exibe o painel de status no arranque, faz validações críticas (como execução fora do drive C:, com pausa interativa) e verifica a existência das ferramentas portáteis em `usr/`.
- **Sistema de Scripts Injetáveis (`core/Scripts/`):** Os antigos atalhos de `doskey` foram convertidos em ficheiros `.bat` independentes (`vc.bat`, `vcdir.bat`, `vcclean.bat`, `wm.bat`, `vcw.bat`, etc.). Eles são injetados diretamente no `%PATH%` do sistema no arranque, tornando-se comandos globais transparentes.

### Launchpad Web e Ferramentas Nativas
- **Launchpad (Hub):** A interface web (`index.html`) foi reformulada num painel de "Cards" limpo. Cada ferramenta abre na sua própria aba, preservando o fluxo analítico.
- **Terminal Web (WebSockets):** A linha de comandos foi levada ao navegador via `xterm.js` e WebSockets (`/ws/terminal`). Baseado em `asyncio`, recria o *local-echo*, suporta macros nativas (`vc`, `vcdir`, `clear`) e contorna o bloqueio natural de Pipes do Windows com forçamento estrito de UTF-8 (`chcp 65001`).
- **Editor Monaco Integrado (`md-editor-pm.html`):** O motor do VS Code agora roda diretamente no Hub. Trabalha nativamente com a nova pasta `_tmpl/`, suportando o atalho `Ctrl+S` que salva o código, dispara a compilação do `template_engine` em segundo plano e devolve uma notificação visual (*Toast*).
- **Hot Reload Silencioso (Polling):** Fim do `Shift+F5`. Adicionada a rota `/api/mtime` no `server.py` que vigia as datas de modificação dos ficheiros gerados (`_mds/`). O visualizador capta a mudança e recarrega instantaneamente via *Cache Busting*.
- **Estrutura de Ficheiros Estáticos (`/static`):** Criação de gestão estática para logotipos do projeto, eliminando erros de servidor e servindo dinamicamente o `favicon.ico`.

## [0.4.8] - 2026-04
Esta versão consolida a visão do sistema sfia como uma linguagem documental viva. O foco foi a implementação do **SFIA_TMPL_SPEC v0.3**, um motor de templates lineares (Parser Lexical) com namespace Python compartilhado, aproximando a experiência de auditoria do conceito de *Jupyter Notebooks Textuais*, mas com extrema segurança anti-recursividade.

### Motor de Templates (Literate Document)
*  **Novo Parser Linear** (`template_engine.py`): Refatoração massiva abandonando substituição Regex global (`re.sub`) por um Parser Top-to-Bottom. O documento agora é processado em fluxo, permitindo estado vivo.
*  **Sintaxe Unificada v0.3**: - Fences de ação: `sql sfia` e `python sfia` para execução e sintaxe nos editores.
    * Inlines de injeção: `{{ variavel }}`, `{{ py: expr }}` e `{{ sql: expr }}`.
* **Namespace Python**: Variáveis do `sfia_config.toml` (Frontmatter YAML) agora são injetadas nativamente no escopo global do template para uso livre.
* **Anti-Recursividade (Segurança)**: Motor blindado contra injeções. Se uma query do banco de dados retornar um texto com `{{ py: ... }}`, ele será impresso como string bruta, não como comando.
* **Isolamento de Gravação**: O motor agora utiliza o módulo nativo tempfile (`tempfile.mkstemp`) em memória para acionar os formatadores de Markdown originais sem conflito de lock de arquivos no Windows.

### Infraestrutura e Experiência do Desenvolvedor (DX)
* **Novo Utilitário** `shortcuts.py`: Painel de atalhos rápidos de CLI (abre Explorer no work_dir ativo, servidor web, e viewer local).
* **Terminal Blindado** (`terminal.bat`): - Alerta crítico e tela de bloqueio caso o usuário execute o projeto fora do drive `C:`.
    * Alerta visual forte orientando a cópia/recuperação da pasta de ferramentas essenciais (`usr`).
    * Adicionado comando `vcw` para iniciar o servidor web (sfiaweb) em uma nova janela de forma assíncrona, não travando o terminal atual.

## [0.4.7] - 2026-04
Esta versão focou massivamente em produtividade, na consolidação do `sfiaweb` como Estação de Trabalho principal, na implementação de Templates Dinâmicos em Markdown e na refatoração do CLI para maior segurança.

### Arquitetura e Gestão de Ambiente
- **Fechei com Python 3.12:** Não se permite 3.13 ou 3.14, porque todos os `pyproject.toml` estão agora com `requires-python = "==3.12.*"`, que recebe correções de segurança até outubro de 2028. Descobri isso ao mexer com o Linux Mint que, para focar em estabilidade, entende que 3.12 é o ponto de equilíbrio ideal entre recursos novos e estabilidade.

### Novo Recurso: Templates Dinâmicos (Literate Documents)

### Microapp `sfiaweb` (A Nova Estação de Trabalho)
- **Dashboard Tático:** Refatoração do `index.html` com painéis retráteis (Explorador, Relatório Ad-Hoc, Consultas Rápidas), lazy loading e feedback visual dinâmico.
- **Consultas Rápidas (SQL Inline):** Novo endpoint POST `/api/query` em `server.py` executando leitura `read-only` no SQLite e devolvendo JSON para renderização de tabelas instantâneas no front-end.
- **Anotações Inteligentes (Vibe Coding):** Restauração do modo de edição `contenteditable` no `markdown-it.html` com atalho global `Ctrl+S` para download do HTML renderizado e anotado (Standalone HTML).

### Microapp `sfia_safic` (CLI e Core)
- **Templates Dinâmicos (`*.tmpl.md`)** como documento-fonte de auditoria, composto por texto livre em Markdown, frontmatter obrigatório de contexto, variáveis interpoláveis e blocos SQL executáveis. A especificação conceitual dos templates está em [SFIA_TMPL_SPEC.md](SFIA_TMPL_SPEC.md)
- **Novo Fluxo de Inicialização:** Introdução do comando `init --dir <caminho>`. Obriga que a pasta seja limpa e contenha apenas `osf.sqlite` (nova convenção de nomenclatura simplificada, substituindo os numerais longos).
- **Setup Automático:** O `init` copia automaticamente modelos essenciais (`auditoria.tmpl.md` e `TrabPaulo.xlsm`) para a raiz do workspace ativo.
- **Estado Persistente:** O diretório de trabalho é gravado em `var/sfia_config.toml`, abolindo o parâmetro `--dir` das outras execuções (`build`, `report`, `template`).
- **Histórico Persistente (`query_history.sqlite`):** O módulo `to_markdown.py` agora grava secretamente todas as consultas SQL executadas (sucesso, linhas e SQL) em um banco de histórico (Trilha de Auditoria).
- **Proteção Visual:** Função `fmt_br` aprimorada para escapar tags HTML invisíveis acidentais (`<`, `>`) e padronizar o alinhamento financeiro de números inteiros para float (`.00`).

### Utilitários (`utils`)
- **Novo `mapeador_sqlite.py`:** Ferramenta que infere e cruza Chaves Primárias e Estrangeiras no SAFIC com base na posição da coluna (`cid=0`). Possui modo CLI com subcomandos `map` (para gerar o schema consolidado) e `search` (para pesquisar cruzamentos e exibir em Markdown).
- **Evolução do `sqlite_dump.py`:** Adição da flag `--hide-empty` para ocultar documentação de tabelas e views vazias, além de limpeza de quebras de linha nas strings DDL.

### Importador SAFIC (`importador_safic`)
- **Importação Dinâmica Expansiva:** Adição da flag `--all-tables` no comando `merge`. Se ativada, puxa tabelas não cadastradas no `MAPA_TABELAS`, inferindo prefixos contextuais (`DocAtrib_`, `Dfe_`, `_`) com base no nome original do banco de dados.

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

