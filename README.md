# 🚀 VC - Vibe Coding Microapps

Coleção de Microapps elaborados em vibe coding. O termo **VC** reflete a filosofia de **Vibe Coding**.

VC não é um bloco monolítico, mas ferramentas independentes que compartilham uma vizinhança.

## 📋 Visão Geral
O **SIA** e depois o **sfia**, agora partes deste vc, é um sistema modular de auditoria fiscal projetado para automatizar o ciclo de vida dos dados de auditoria, desde a ingestão de bases brutas até a geração de relatórios sofisticados e auditáveis. O foco está na **produtividade, transparência e reprodutibilidade**, operando sem dependências globais no sistema.

## 📌 Objetivo
Transformar bancos SQLite brutos em relatórios consistentes e auditáveis usando apenas **Python + Markdown + SQL**.

## Principal funcionalidade: auditoria - sistema sfia

- sfia é um sistema de auditoria.
- Foi desenvolvido com foco em produtividade, relatórios SQL dinâmicos, anotações de auditoria in-loco (em Markdown e HTML) e automação de cadernos documentais (*Literate Programming*  através da sintaxe `SFIA_TMPL_SPEC`).
- Usa microapps do VC para exploração, consulta rápida, exportação ad-hoc e leitura/anotação de artefatos. Opera sobre o *work_dir* ativo gravado no contexto, dentro dos conceitos sfia, com pasta de trabalho inicializada rigorosamente. As subpastas internas incluem `_dbs` (bancos SQLite e históricos), `_mds` (arquivos markdown materiais e outputs de templates) e `_xls` (arquivos Excel de suporte).

## Características do VC

- **Isolamento dos Microapps:** Cada pasta tem o seu próprio ficheiro `pyproject.toml`, assim como cada pasta tem seu próprio `.venv`. Por isso, utilizamos o `uv` de forma independente dentro de cada pasta. Exemplo:

```bash
cd importador_safic
uv sync
```

Historicamente, o projeto **VC** é uma suíte de ferramentas de auditoria fiscal e processamento de dados estruturada como um monorepo de microapps. Este projeto evoluiu de scripts isolados (anteriormente sob nome `sia`) para uma arquitetura enxuta, padronizada com o gerenciador `uv`, utilizando bancos de dados SQLite e renderização Markdown nativa.

O isolamento de microapps é usado basicamente para economizar tokens em IA, focando em cada uma das funcionalidades de forma objetiva.

---

## 🛠️ Microapps Disponíveis

### 1. [sfiaweb] - Servidor de Relatórios (Dashboard Tático)
Servidor leve FastAPI que atua como **Estação de Trabalho do Auditor**. 
* Lida com o *work_dir* atual, serve o visualizador local de Markdown (`markdown-it.html`).
* Oferece consultas SQL ad-hoc ao vivo (`/api/query`) com renderização tabular imediata e suporte a exportações diretas.
* Suporta edição nativa ao vivo dos relatórios HTML com atalho de salvamento local (`Ctrl+S`).

### 2. [sfia_safic] - Tratamento SAFIC e Relatórios 
Motor de construção da base consolidada (SIA) a partir da extração OSF. 
* Constrói relatórios analíticos (`report`, `report_oper`, `report_item`).
* **Templates Dinâmicos (`*.tmpl.md`)** como documento-fonte de auditoria, composto por texto livre em Markdown, frontmatter obrigatório de contexto, variáveis interpoláveis e blocos SQL executáveis. A especificação conceitual dos templates está em [SFIA_TMPL_SPEC.md](SFIA_TMPL_SPEC.md).
* Armazena histórico completo de trilha de auditoria SQL (`query_history.sqlite`).

### 3. [sfia_credAcCust] - Relatórios e-CredAc Custeio
Automatiza a transformação de extratos de Custeio (exportados via PowerBI para Excel) em um banco de dados relacional SQLite, gerando relatórios Markdown pré-configurados.

### 4. [importador_safic] - Ingestão de Dados (Windows)
Ferramentas de ETL baseadas em Windows para conectar ao SQL Server local, converter arquivos pesados `.mdf` (Safic) para SQLite (`mdf2sqlite.py`) e realizar o *merge* das bases distribuídas com regras dinâmicas de prefixo (`--all-tables`).

### 5. [utils] - Caixa de Ferramentas CLI
Utilitários ágeis para manutenção e visualização:
* **sqlite_dump.py**: Gera relatórios MD com a estrutura física (DDL) e amostras de dados de bancos SQLite (com suporte à omissão de tabelas vazias).
* **mapeador_sqlite.py**: Infere cruzamentos lógicos de Chaves Primárias e Estrangeiras (PK/FK) baseado no posicionamento `cid=0` e permite pesquisar os relacionamentos em terminal (Markdown).
* **aiim.py**: Automação Selenium/Playwright (esboço) para scraping do portal da SEFAZ.
* **pmcloud.py**: Sincronizador de arquivos conectado à sua nuvem privada via API PHP com versionamento e garbage collector.

### 6. [exportador] - Extração Flexível
Permite extrair resultados de consultas SQL complexas para múltiplos formatos (Excel, TSV e Markdown). Suporta uso do comando `ATTACH DATABASE` para cruzamento multibase.

---

## Terminal de Trabalho (`terminal.bat`)
O arquivo `terminal.bat` na raiz configura o ambiente UTF-8 e define atalhos (**doskeys**) para facilitar o uso, como:
* `vc`: Atalho para rodar qualquer microapp (`uv run --directory ...`).
* `vcdump`: Gera o consolidado de código do projeto para contexto de IA.
* `sqlite2md`: Atalho rápido para o utilitário de inspeção de banco de dados.

## 🚀 Como Iniciar

1. Clone o repositório.
2. Execute o arquivo (duplo click) `terminal.bat` na raiz. Leia com atenção as instruções que aparecerão.
3. Coloque o arquivo de dados original (`osf.sqlite`) sozinho em uma pasta vazia. Essa pasta, por padrão, terá o nome `sfia`.
4. Inicialize a auditoria, compile o banco e abra o Dashboard, tudo via **terminal**:
   ```bash
   # 1. Lista microapps disponíveis
   vcdir
   # 2. Executa o primeiro microapp. Comece por sfia_safic. A porta de entrada é sempre main.py. Comece com -h pra entender.
   vc sfia_safic main.py -h
   # 3. Pela ordem, vamos iniciar. Primeiro -h para entender
   vc sfia_safic main.py init -h
   # 4. Conforme instruções, quando se usa o comando `init`, ele pedir --dir, que é a pasta `sfia` com `osf.sqlite`
   vc sfia_safic main.py init --dir C:(...)\\sfia
   # 5. Olhe essa pasta C:(...)\\sfia no Windows Explorer. Ela mudou completamente.
   #    5.1. Todas as mudanças apareceram no terminal quando vc deu o último comando acima. Leia uma a uma e confronte com o Windows Explorer.
   # 6. Construa (ou compile, use o verbo que quiser) o banco de dados. Observe no Windows Explorer a criação do novo db sqlite.
   vc sfia_safic main.py build
   # 7. Gere todos os relatórios pré disponíveis. Leia tudo o que vai sendo aparecendo no terminal.
   vc sfia_safic main.py report
   vc sfia_safic main.py report_oper
   vc sfia_safic main.py report_item
   # 8. Abra o Dashboard e divirta-se no mundo web. Ele está acessível em [http://127.0.0.1:5678](http://127.0.0.1:5678)
   vcw
   ```
5. O **terminal** agora ficou dedicado ao servidor web, que chamei de Dashboard. Ele está acessível em [http://127.0.0.1:5678](http://127.0.0.1:5678):
6. Explore o Dashboard a vontade. Acostume-se a visualizar o Markdown renderizado em `Explorador de Arquivos` e também em `Ferramentas` - `Visualizador MD (ad-hoc)` onde, neste caso, vc tem que arrastar o arquivo Markdown `*.md` do Windows Explorer para seu browser. 
7. Por isso, para continuar, execute o arquivo  (duplo click) `terminal.bat` na raiz para abrir um novo terminal. Releia com atenção as instruções que aparecerão.
   ```bash   
   # 9. Digite wm, dbb, ct, mp e explore WinMerge, DBBrowser, CudaText, Markpad(Editor .md). Eles também podem ser executados com o nome do arquivo desejado para trabalho digitando-se o nome do mesmo em seguida.
   wm
   dbb
   ct
   mp
   # 10. O último passo é o o processamento de templates textuais de auditoria (*.tmpl.md). Eles sempre estarão na rais de `sfia`, pasta C:(...)\\sfia. Vá editando os templates, verifique as instruções, é um mundo sem sim. Acompanhe essa pasta `sfia` pelo Windows Explorer e vá mudando seus arquivos no que for necessário
   vc sfia_safic main.py template
   ```

---
**Versão Atual:** Ver [CHANGELOG.md](CHANGELOG.md) ou [SKILL.md](SKILL.md) | **Filosofia:** Vibe Coding 🌊