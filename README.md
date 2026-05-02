# 🚀 VC - Vibe Coding Microapps

Coleção de Microapps elaborados em vibe coding. O termo **VC** reflete a filosofia de **Vibe Coding**.

VC não é um bloco monolítico, mas ferramentas independentes que compartilham uma vizinhança e bibliotecas centrais fortificadas.

## 📋 Visão Geral
O **SIA** e depois o **sfia**, agora partes deste vc, é um sistema modular de auditoria fiscal projetado para automatizar o ciclo de vida dos dados de auditoria, desde a ingestão de bases brutas até a geração de relatórios sofisticados e auditáveis. O foco está na **produtividade, transparência e reprodutibilidade**, operando sem dependências globais no sistema.

## 📌 Objetivo
Transformar bancos SQLite brutos em relatórios consistentes e auditáveis usando apenas **Python + Markdown + SQL**.

## Principal funcionalidade: auditoria - sistema sfia

- sfia é um sistema de auditoria.
- Foi desenvolvido com foco em produtividade, relatórios SQL dinâmicos, anotações de auditoria in-loco (em Markdown e HTML) e automação de cadernos documentais (*Literate Programming* através da sintaxe `SFIA_TMPL_SPEC`).
- Usa microapps do VC para exploração, consulta rápida, exportação ad-hoc e leitura/anotação de artefatos. Opera sobre o *work_dir* ativo gravado no contexto, dentro dos conceitos sfia, com pasta de trabalho inicializada rigorosamente. As subpastas internas incluem `_dbs` (bancos SQLite e históricos), `_tmpl` (templates brutos), `_mds` (arquivos markdown materiais materiais gerados pelo sistema e pelo compilador) e `_xls` (arquivos Excel de suporte).

## Características do VC

- **Isolamento dos Microapps:** Cada pasta tem o seu próprio arquivo `pyproject.toml`, assim como cada pasta tem seu próprio `.venv`. Por isso, *utilizamos o `uv` de forma independente dentro de cada pasta*, através de scripts .bat em `core/Scripts`, especialmente `vc.bat`, conforme explicado na seção [Terminal de Trabalho (`terminal.bat`)](#pmtitttb).

Historicamente, o projeto **VC** evoluiu de scripts isolados(anteriormente sob nome `sia`) para uma arquitetura enxuta, padronizada com o gerenciador `uv`, utilizando bancos de dados SQLite e renderização Markdown nativa.

O isolamento de microapps é usado basicamente para economizar tokens em IA, focando em cada uma das funcionalidades de forma objetiva, conectando-se sempre à espinha dorsal do `core/lib`.

---

## 🛠️ Microapps Disponíveis

### 1. [core] - Central de Comando, Launchpad Web e Bibliotecas Globais
Atua como o cérebro do projeto.
* Fornece um Launchpad interativo com servidor web leve FastAPI.
* **Painel de Ferramentas Dinâmico:** Exibe os comandos do sistema em cards executáveis direto pelo navegador.
* Abriga as bibliotecas globais (`core/lib/vccore.py` e `to_markdown.py`), garantindo que todos os microapps falem a mesma linguagem visual de logs e caminhos.

### 2. [sfia_safic] - Tratamento SAFIC e Relatórios 
Motor de construção da base consolidada (SIA) a partir da extração OSF. 
* Constrói relatórios analíticos dinâmicos (`report`, `report_oper`, `report_item`).
* Compila **Templates Dinâmicos (`*.tmpl.md`)** como documento-fonte de auditoria (Markdown + SQL Intercalado).
* Armazena histórico completo de trilha de auditoria SQL (`query_history.sqlite`).

### 3. [sfia_credAcCust] - Relatórios e-CredAc Custeio
Automatiza a transformação de extratos de Custeio (exportados via PowerBI para Excel) em um banco de dados relacional SQLite.

### 4. [importador_safic] - Ingestão de Dados (Windows)
Ferramentas de ETL baseadas em Windows para conectar ao SQL Server local e converter arquivos pesados `.mdf` (Safic) para SQLite com merge inteligente.

### 5. [utils] - Caixa de Ferramentas CLI
Utilitários ágeis para manutenção e extração, incluindo:
* **sqlite2md.py**: Exportador universal de consultas SQLite diretas para tabelas Markdown elegantes.
* **sqlite_dump.py**: Extração de metadados de esquemas de banco de dados.
* **mapeador_sqlite.py**: Inferência de Chaves Primárias e Estrangeiras (PK/FK).
* **aiim.py**: Automação Selenium/Playwright (esboço) para scraping do portal da SEFAZ.
* **pmcloud.py**: Sincronizador de arquivos conectado à nuvem privada via API PHP.

### 6. [exportador] - Extração Flexível
Permite extrair resultados de consultas SQL complexas para múltiplos formatos (Excel, TSV e Markdown). Suporta uso do comando `ATTACH DATABASE` para cruzamento multibase.

---

<a id="pmtitttb"></a>
## Terminal de Trabalho (`terminal.bat`)
O arquivo `terminal.bat` na raiz atua como o "interruptor" de ignição do ambiente. Ele aciona a Central de Comando.

> Em outras palavras, **a forma de iniciar o VC é através de `terminal.bat`**

Internamente, funciona da seguinte forma:
- `terminal.bat` faz um call em `core/Scripts/vc_env.bat`, que descobre inteligentemente a raiz do projeto e configura variáveis primordiais (`PATH`, `PYTHONPATH` e `VC_ROOT`).
    - É perfeitamente possível abrir uma nova janela isolada invocando apenas `vc_env.bat`, mecanismo que o Launchpad utiliza para hidratar janelas nativas do Windows sob demanda.
- Tudo depois é orquestrado através de scripts `.bat` em `core/Scripts` (`vc`, `vcclean`, `wm`, etc.).
- De acordo com a filosofia do projeto, o utilitário `vc.bat` utiliza `uv run` sempre, nunca `python` direto.
- O `vc.bat` possui um motor robusto de passagem de parâmetros que permite enviar *N* argumentos (sem limites) para a execução do microapp isolado (`"%VC_ROOT%\%MICROAPP%"`).
- O contexto atual (pasta em uso) é sempre guiado silenciosamente pelo arquivo global `var/sfia_config.toml`.

## 🚀 Como Iniciar

1. Clone o repositório.
2. Execute o arquivo (duplo click) `terminal.bat` na raiz.
3. Coloque o arquivo de dados original (`osf.sqlite`) sozinho em uma pasta vazia. Essa pasta, por padrão, terá o nome `sfia`.
4. Inicialize a auditoria e explore a interface de ajuda altamente descritiva em cada etapa:
   ```bash
   # 1. Lista microapps e pastas disponíveis
   vcdir
   # 2. Veja as instruções coloridas e orientações de fluxo do sistema
   vc sfia_safic main.py -h
   # 3. Inicialize a pasta (ela precisa estar rigorosamente apenas com o osf.sqlite)
   vc sfia_safic main.py init --dir C:(...)\sfia
   # 4. Construa a malha analítica
   vc sfia_safic main.py build
   # 5. Gere todos os relatórios pré disponíveis. Leia tudo o que vai sendo aparecendo no terminal.
   vc sfia_safic main.py report
   vc sfia_safic main.py report_oper
   vc sfia_safic main.py report_item
   # 6. Abra o Launchpad Web e divirta-se
   vcw
   ```
5. O **terminal** principal ficará dedicado ao servidor web do Launchpad. Ele está acessível em [http://127.0.0.1:5678](http://127.0.0.1:5678).
6. Explore o Launchpad. Através da aba **Ferramentas do Sistema**, você pode clicar nos Cards para abrir janelas do Windows e executar utilitários e editores (WinMerge, CudaText, DB Browser) fornecendo os parâmetros num clique.
7. O último passo é o processamento de templates textuais de auditoria (`*.tmpl.md`). Eles sempre estarão na raiz da pasta `sfia`. Vá editando os templates via Editor do Launchpad, verifique as instruções e salve com `Ctrl+S` para autocompilar:
   ```bash
   # 7. Digite wm, dbb, ct, mp e explore WinMerge, DBBrowser, CudaText, Markpad(Editor .md). Eles também podem ser executados com o nome do arquivo desejado para trabalho digitando-se o nome do mesmo em seguida.
   wm
   dbb
   ct
   mp
   # 8. O último passo é o o processamento de templates textuais de auditoria (*.tmpl.md). Eles sempre estarão em work_dir/_tmpl. Vá editando os templates, verifique as instruções, é um mundo sem fim. Acompanhe essa pasta `sfia` pelo Windows Explorer e vá mudando seus arquivos no que for necessário
   vc sfia_safic main.py template
   # 9. Para maior produtividade, com o servidor web (vcw) rodando em uma janela, deixe o Hot-Reload rodando em outra janela:
   vcth
   # Toda vez que você salvar um arquivo *.tmpl.md na pasta _tmpl, o vcth o compilará e o abrirá automaticamente no seu navegador. Os artefatos finais vão para a pasta _mds.
   ```

---
**Versão Atual:** Ver [CHANGELOG.md](CHANGELOG.md) ou [SKILL.md](SKILL.md) | **Filosofia:** Vibe Coding 🌊