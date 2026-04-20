# 📝 Especificação Conceitual: Templates Dinâmicos
**Versão:** 0.1 | **Status:** Draft Conceitual | **Ecossistema:** VC / sfia | **Formato Nome:** `*.tmpl.md`

## 1. Visão Geral (O que é)
Um `*.tmpl.md` é um **documento-fonte de auditoria**, composto por texto livre em Markdown, frontmatter obrigatório de contexto, variáveis interpoláveis e blocos SQL executáveis.

São arquivos livres — não pertencem rigidamente ao sistema.
O sistema só precisa saber interpretá-los.

Ele não é uma extensão do visualizador, mas um **novo tipo de artefato do workspace**. A proposta não é ser apenas um formato de relatório, mas sim uma **linguagem documental de auditoria** focada em reprodutibilidade, onde prosa e dados coexistem de forma programática.

A filosofia segue o princípio de transformar bases de dados em evidências auditáveis usando puramente **Python + Markdown + SQL**, operando sob o conceito de *Literate Document* (Documento Literário). O documento deixa de ser texto estático e vira um **artefato executável**.

---

## 2. Parentes Conceituais  e Inspirações

| Referência | O que inspira |
| :--- | :--- |
| **R Markdown / Quarto** | Documento-fonte com blocos executáveis que geram saída inline, mesclar narrativa com código executável que gera tabelas e gráficos in-loco (Literate Programming). Este projeto é essencialmente um *Quarto fiscal baseado em SQLite*. |
| **Jupyter Notebooks** | Células de código intercaladas com prosa. A diferença é que `.tmpl.md` é texto puro, sem formato binário. |
| **Obsidian Dataview** | Notas que consultam dados; separação entre nota-fonte e renderização dinâmica; frontmatter como metadado ativo. |
| **dbt (data build tool)** | A mentalidade de "SQL como cidadão de primeira classe", documentação acoplada a dados e dependências declaradas explicitamente. SQL como fonte principal; documentação acoplada a dados; artefatos reprodutíveis; dependências explícitas declaradas no topo. |
| **Jinja2 / Mustache / Liquid** | Sintaxe `{{ var }}` para interpolação textual. Convenção universal, custo cognitivo mínimo. |
| **Pandoc + YAML frontmatter** | YAML no topo do documento como metadado de execução, não de apresentação. |

---

## 3. A Pipeline de Renderização (Como funciona)
É fundamental separar o documento-fonte do documento materializado. A arquitetura obedece à seguinte ordem temporal:

1. **Autoria:** O auditor escreve o caderno em `auditoria.tmpl.md`.
2. **Compilação (O Robô Python):** Uma camada de backend lê o template, resolve o frontmatter, substitui as variáveis `{{ var }}` e executa os blocos de código SQLite.
3. **Materialização:** O robô gera um artefato puro (ex: `auditoria.md` na pasta `_mds`). A decisão de ocultar ou exibir as queries SQL originais no artefato final é do usuário.
4. **Visualização:** O artefato final é lido e estilizado pelo `markdown-it.html` (que entende Mermaid, callouts, etc., mas é cego para bancos de dados).

---

## 4. Nomenclatura e Convenção de Arquivos

| Arquivo | Papel |
| :--- | :--- |
| `auditoria.tmpl.md` | Documento-fonte. Editado pelo auditor. Contém queries e variáveis. |
| `auditoria.md` | Saída materializada. Gerado pelo motor. Fica em `_mds/`. |

A regra é simples: **remove-se `.tmpl`** do nome para obter o arquivo de saída.
O auditor edita o `.tmpl.md`. O sfia cria o `.md`.

---

## 5 Anatomia do Template

### 5.1. Frontmatter Obrigatório
O documento deve declarar rigorosamente suas dependências no topo via YAML. Isso garante que o template não seja "mágico" e tenha contexto rastreável.

````
```yaml
---
type: "sfia-template"
main_db: "sia13003713267.sqlite"
attach_dbs:
  - "osf13003713267.sqlite"
  - "oper_base.sqlite"
(...)
---
```
````

### Campos obrigatórios

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `type` | string | Sempre `"sfia-template"`. Documentos sem este valor são ignorados pelo motor. |
| `main_db` | string | Nome físico do banco principal, dentro de `_dbs/`. |
| `attach_dbs` | lista | Bancos secundários a serem anexados via `ATTACH`. Pode ser lista vazia `[]`. |

### Campos opcionais (variáveis documentais)

Qualquer campo adicional no frontmatter se torna uma **variável documental**
disponível para interpolação com `{{ nome_do_campo }}` em qualquer parte do documento.

````
```yaml
---
type: "sfia-template"
main_db: "sia13003713267.sqlite"
attach_dbs:
  - "osf13003713267.sqlite"
  - "oper_base.sqlite"
osf: "13003713267"
contribuinte: "CAMESA INDUSTRIA TEXTIL LTDA"
ano_base: 2023
periodo: "01/2021 a 12/2023"
---
```
````


### 5.2. Interpolação de Variáveis
A injeção de valores no texto segue o padrão universal de templates textuais (Jinja/Liquid): `{{ nome_da_variavel }}`.

**Taxonomia de Variáveis:**
* **Variáveis Documentais:** Declaradas estaticamente no YAML (ex: `{{ contribuinte }}`).
* **Variáveis Computadas:** Geradas em tempo de execução pelos blocos `sfia` (ex: `{{ total_autuado }}`). Opcionalmente, pode-se adotar um namespace para clareza (ex: `{{ calc.total_autuado }}`).

Exemplo:
````
```markdown
Trata-se de auditoria da empresa **{{ contribuinte }}**,
OSF nº {{ osf }}, referente ao exercício de {{ ano_base }}.
```
````

### 5.3. Blocos (fences) de Materialização de Evidências (`sfia-sql`)

O fence `sfia-sql` marca uma consulta SQL que será **executada e substituída**
por uma tabela Markdown no arquivo de saída.

````
```sfia-sql
SELECT max(nome) AS Empresa, max(cnpj) AS CNPJ, max(ie) AS IE
FROM (
  SELECT nome, cnpj, ie
  FROM _fiscal_participantedeclarado
  WHERE idParticipanteDeclarado = 1
);
```
````

**No arquivo de saída**, o bloco acima é substituído por:

````
```markdown
| Empresa | CNPJ | IE |
| :--- | :--- | :--- |
| CAMESA INDUSTRIA TEXTIL LTDA | 43672716000814 | 796891627110 |

> 📊 **1 linha** · executado em 4ms
```
````

### 5.4 Blocos (fences) `sfia-sql` — Inline

Quando a consulta retorna **exatamente uma linha com exatamente um campo**,
o resultado pode ser interpolado diretamente no fluxo do texto usando a
sintaxe de código inline:

````
```markdown
Trata-se de auditoria da empresa `sfia-sql SELECT max(nome) FROM _fiscal_participantedeclarado WHERE idParticipanteDeclarado = 1`,
CNPJ `sfia-sql SELECT max(cnpj) FROM _fiscal_participantedeclarado WHERE idParticipanteDeclarado = 1`,
cujo período de apuração se inicia em `sfia-sql SELECT min(referencia) FROM _imp_ReferenciasSelecionadasNaImportacao`.
```
````

**No arquivo de saída:**

````
```markdown
Trata-se de auditoria da empresa CAMESA INDUSTRIA TEXTIL LTDA,
CNPJ 43672716000814,
cujo período de apuração se inicia em 2021-01-01.
```
````

> **Regra de segurança:** se a consulta inline retornar mais de uma linha ou
> mais de uma coluna, o motor substitui pelo valor `[resultado ambíguo]`
> e registra um aviso no log de execução.

### 5.5. Blocos (fences) de Diretivas de Controle (`sfia`)

O fence `sfia` é a camada de **controle de contexto e comportamento** do motor.
Ele não gera saída visível no documento final — atua como instrução para o processador.

A sintaxe interna é YAML.

````
```sfia
sql.limit: "20, 10"
sql.where: "aaaamm LIKE '2023%'"
title: "Análise restrita ao exercício de 2023"
```
````

### Diretivas previstas para v0.2

| Diretiva | Tipo | Efeito |
| :--- | :--- | :--- |
| `sql.limit` | inteiro | Aplica `LIMIT {{ sql.limit }}` a todos os `sfia-sql` seguintes até o próximo fence `sfia` que o redefina ou zere. |
| `sql.where` | string | Injeta cláusula `WHERE` adicional nos `sfia-sql` seguintes que não tenham `WHERE` próprio ou, onde houver where, insere `AND` ou `OR` conforme regras específicas (v0.3) |
| `show_sql` | bool | Se `true`, o SQL é exibido no output (equivalente ao `--debug` de `to_markdown.py`). Padrão: `false`. |
| `title` | string | Define um título H3 que precede a tabela gerada pelo próximo `sfia-sql`. |

### Diretivas reservadas para versões futuras

| Diretiva | Intenção |
| :--- | :--- |
| `sql.exec` | Executa um DDL/DML antes dos blocos seguintes (ex: `CREATE TABLE temp AS ...`). |
| `var.nome` | Define ou sobrescreve uma variável documental sem precisar editar o frontmatter. |
| `py.exec` | Executa um trecho Python seguro no contexto do motor. Requer política de segurança a definir. |
| `output.format` | Define o formato de saída desta seção (`md`, `xlsx`, `html`). |

> **Sobre `py.exec`:** a introdução de execução Python arbitrária requer
> definição cuidadosa de sandbox antes de implementar.
> Fica reservada para discussão futura.

---

## 6. Ciclo de Vida do Documento

```
[auditor edita]          [motor executa]          [viewer exibe]
auditoria.tmpl.md  →→→  auditoria.md  →→→  markdown-it.html
     ↑                                              ↓
  fonte viva                                  leitura + anotação
  (editável)                                  (Ctrl+S → HTML)
```

**Passo a passo do motor:**

1. Ler `auditoria.tmpl.md`
2. Validar frontmatter: `type`, `main_db` presentes?
3. Conectar ao `main_db`; executar `ATTACH` nos `attach_dbs`
4. Resolver variáveis documentais `{{ var }}` no texto
5. Processar fences `sfia` (diretivas de contexto)
6. Executar fences `sfia-sql` bloco → substituir pelo resultado em tabela Markdown
7. Executar `sfia-sql` inline → substituir pelo valor escalar
8. Gravar `_mds/auditoria.md`

---

## 7. Visibilidade do SQL no Output

O comportamento em relação ao SQL no documento de saída é controlado pelo auditor,
seguindo a mesma filosofia do `--debug` já presente em `to_markdown.py`.

| Configuração | Resultado |
| :--- | :--- |
| `show_sql: false` (padrão) | O SQL não aparece no `.md` de saída. Só a tabela. Documento limpo. |
| `show_sql: true` (global, no frontmatter) | O SQL aparece em bloco colapsável `<details>` antes de cada tabela. |
| `show_sql: true` (local, no fence `sfia`) | Aplica somente aos blocos `sfia-sql` seguintes. |

Isso mantém a coerência com o que já existe no sistema e dá ao auditor
controle granular sobre o nível de detalhe técnico exposto no relatório.

---

## 8. Exemplo Completo de Template

````
---
type: "sfia-template"
main_db: "sia13003713267.sqlite"
attach_dbs:
  - "osf13003713267.sqlite"
osf: "13003713267"
contribuinte: "CAMESA INDUSTRIA TEXTIL LTDA"
ano_base: 2023
---

# Relatório de Auditoria — {{ contribuinte }}

OSF nº **{{ osf }}** · Exercício: **{{ ano_base }}**

---

## 1. Dados do Contribuinte

```sfia-sql
SELECT max(nome) AS Empresa, max(cnpj) AS CNPJ, max(ie) AS IE
FROM (SELECT nome, cnpj, ie FROM _fiscal_participantedeclarado
      WHERE idParticipanteDeclarado = 1);
```

## 2. Resumo Econômico

```sfia
title: "Movimentação por Grupo Econômico"
sql.limit: 50
show_sql: false
```

```sfia-sql
SELECT g1,
  sum(valconGia) AS valconGia, sum(valconEfd) AS valconEfd,
  sum(valconDif) AS valconDif,
  sum(icmsGia)   AS icmsGia,   sum(icmsEfd)   AS icmsEfd
FROM madf
GROUP BY g1;
```

## 3. Constatações do Auditor

> [!warning] Ponto de Atenção
> Inserir aqui as constatações sobre os dados acima.

A empresa `sfia-sql SELECT max(nome) FROM _fiscal_participantedeclarado WHERE idParticipanteDeclarado = 1`
apresentou diferenças entre GIA e EFD nos grupos identificados abaixo.

## 4. Principais Discrepâncias (Top 20)

```sfia
title: "chaveNroTudao — Classificações [12] e [13]"
show_sql: true
```

```sfia-sql
SELECT tp_codSit, tp_oper, Part,
  dif_vl_doc, dif_icms, vl_docDFe, vl_docEFD
FROM chaveNroTudao
WHERE ChNrClassifs LIKE '%[12]%'
   OR ChNrClassifs LIKE '%[13]%'
ORDER BY abs(dif_icms) DESC
LIMIT 20;
```

---
*Gerado por sfia · {{ ano_base }}*
````

---

## 9. O que o Viewer `markdown-it.html` Faz (e Não Faz)

O viewer atual renderiza o `.md` de saída com fidelidade — suporta
frontmatter, callouts, task lists, Mermaid e emojis.

Ele **não** executa nenhuma das funcionalidades acima:

| Capacidade | `markdown-it.html` | Motor `*.tmpl.md` |
| :--- | :---: | :---: |
| Renderizar tabelas Markdown | ✅ | — |
| Renderizar callouts / Mermaid | ✅ | — |
| Resolver `{{ var }}` | ❌ | ✅ |
| Executar `sfia-sql` | ❌ | ✅ |
| Processar diretivas `sfia` | ❌ | ✅ |
| Conectar a bancos SQLite | ❌ | ✅ |

O viewer é a **camada de apresentação**.
O motor `*.tmpl.md` é a **camada de execução**, anterior ao viewer.

---

## 10. O que Está Fora do Escopo desta Especificação

Para manter o foco, os itens abaixo são reconhecidos mas **deliberadamente
deixados para versões futuras**:

- Execução Python via `py.exec` (requer sandbox)
- Variáveis computadas inline `{# SQL #}`
- Output multi-formato por seção (`output.format`)
- Edição do `.tmpl.md` dentro do sfiaweb (hoje: editor de texto externo)
- Validação de schema das queries (colunas esperadas vs. retornadas)

---

> Especificação pertence ao projeto **VC — Vibe Coding Microapps**