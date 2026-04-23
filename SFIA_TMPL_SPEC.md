# 📝 Especificação Conceitual: Templates Dinâmicos
**Versão:** 0.3 | **Status:** Alpha | **Ecossistema:** VC / sfia | **Formato Nome:** `*.tmpl.md`

## 1. Visão Geral (O que é)
Um `*.tmpl.md` é um **documento-fonte de auditoria**, composto por texto livre em Markdown, frontmatter obrigatório de contexto, variáveis interpoláveis, blocos SQL executáveis e blocos Python executáveis.

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
4. **Visualização:** O artefato final é lido e estilizado por `md-viewer-pm.html` (que entende Mermaid, callouts, etc.).

```
[auditor edita]          [motor executa]          [viewer exibe]
auditoria.tmpl.md  →→→    auditoria.md    →→→   md-viewer-pm.html
     ↑                                                  ↓
  fonte viva                                    leitura + anotação
  (editável)                                     (Ctrl+S → HTML)
```

### Nomenclatura e Convenção de Arquivos

| Arquivo | Papel |
| :--- | :--- |
| `*.tmpl.md` | Documento-fonte. Editado pelo auditor. Contém queries e variáveis. Fica na raiz do work_dir |
| `*.md` | Saída materializada. Gerado pelo motor. Fica em `_mds/`. |

A regra é simples: **remove-se `.tmpl`** do nome para obter o arquivo de saída.
O auditor edita o `.tmpl.md`. O sfia cria o `.md`.

---

## 4 Anatomia do Template

---

### 4.1. Frontmatter Obrigatório
O documento deve declarar rigorosamente suas dependências no topo via YAML. Isso garante que o template não seja "mágico" e tenha contexto rastreável.

```yaml
---
type: "sfia-template"
main_db: "sia.sqlite"
attach_dbs:
  osf: "osf.sqlite"
  oper: "oper_base.sqlite"
  item: "item_base.sqlite"
(...)
---
```

#### Campos obrigatórios

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `type` | string | Sempre `"sfia-template"`. Documentos sem este valor são ignorados pelo motor. |
| `main_db` | string | Nome físico do banco principal, dentro de `_dbs/`. |
| `attach_dbs` | dicionário  (chave-valor) | Bancos secundários, dentro de `_dbs/`, a serem anexados via `ATTACH`. Pode ser dicionário vazio `{}`. A chave é o alias, o valor é o nome do arquivo do banco de dados. |

<a id="pmti551"></a>
#### Campos opcionais (variáveis documentais)

Qualquer campo adicional no frontmatter se torna uma **variável documental**
disponível para interpolação com `{{ nome_do_campo }}` em qualquer parte do documento.

```yaml
---
type: "sfia-template"
main_db: "sia.sqlite"
attach_dbs:
  osf: "osf.sqlite"
  oper: "oper_base.sqlite"
  item: "item_base.sqlite"
osf: "13005678267"
contribuinte: "XPTO INDUSTRIA E COMERCIO LTDA"
ano_base: 2023
periodo: "01/2021 a 12/2023"
---
```

---

### 4.2. Interpolação de Variáveis

A injeção de valores no texto segue o padrão universal de templates textuais (Jinja/Liquid): `{{ nome_da_variavel }}`, podendo ser
* **Variáveis Documentais:** Declaradas estaticamente no YAML (ex: `{{ contribuinte }}`).
* **Conteúdos Computados:** Gerados em tempo de execução quando do processamento do template, conforme mais adiante explicado.

Exemplo:
```markdown
Trata-se de auditoria da empresa **{{ contribuinte }}**,
OSF nº {{ osf }}, referente ao exercício de {{ ano_base }}.
```

---

### 4.3. Blocos de Código (code fences) de Materialização de Evidências (`sql sfia`)

O fence ` ```sql sfia` (...) ` ``` ` delimita um SELECT de uma consulta SQL que será **executada e substituída**
por uma tabela Markdown no arquivo de saída.

```sql sfia
SELECT max(nome) AS Empresa, max(cnpj) AS CNPJ, max(ie) AS IE
FROM (
  SELECT nome, cnpj, ie
  FROM _fiscal_participantedeclarado
  WHERE idParticipanteDeclarado = 1
);
```

**No arquivo de saída**, o bloco acima é substituído por:

```markdown
| Empresa | CNPJ | IE |
| :--- | :--- | :--- |
| XPTO INDUSTRIA E COMERCIO LTDA | 43123789000134 | 796123567110 |
```

O fence ` ```sql sfia` (...) ` ``` ` pode ter variáveis interpoladas `{{ nome_da_variavel }}`. Exemplo:
```sql sfia
SELECT A.numOsf, A.dataDeCriacao, A.loginUsuario, A.cnpj, A.ie, A.razao, A.formaDeAcionamento
FROM _dbo_auditoria AS A
WHERE numOsf = {{ num_osf }}
```

> Ou seja, quando o parser processar o template, toda vez que encontrar um bloco ` ```sql sfia` (...) ` ``` `, preliminarmente vai processar e resolver todas as variáveis interpoladas `{{ nome_da_variavel }}` presentes no bloco, somente depois vai processar o bloco.

> Embora não seja comum iniciar um bloco com duas palavras, o motivo da escolha de ` ```sql sfia` é a indicação positiva para editores e visualizadores de Markdown, garantindo o syntax highlighting nativa do sql, sem poluir a renderização final.

---

### 4.4. Blocos de Código (code fences) de Programação (`python sfia`)

A inspiração do formato é a mesma de ` ```sql sfia` (...) ` ``` `, mas aqui é ` ```python sfia` (...) ` ``` `.

Blocos Python em fence ` ```python sfia` (...) ` ``` ` executam, com limitações de segurança, códigos em python. O bloco é substituído pela saída do print(). Se não houver print(), o bloco desaparece do documento. Se houver erro, a mensagem de erro completa é inserida no lugar do bloco.

> Novamente, embora não seja comum iniciar um bloco com duas palavras, o motivo da escolha de ` ```python sfia` também é a indicação positiva para editores e visualizadores de Markdown, garantindo o syntax highlighting nativa do python, sem poluir a renderização final.

> Da mesma forma ao explicado no item anterior, blocos ` ```sql sfia` (...) ` ``` ` podem ter variáveis interpoladas `{{ nome_da_variavel }}`.
 
Ou seja, são executados da mesma forma que o comando python exec(conteudo_do_fence), como no exemplo abaixo (lembrando que nesse exemplo a variável `ano_base` foi [definida no YAML frontmatter](#pmti551)):
```python sfia
a = 10
b = 5
dtaini = str({{ ano_base }}) + "-01-01"
if (a > 8):
    print(f"variável `a` é maior que oito e a soma com `b` é {(a + b)}, sendo que a data de início é {dtaini}")
```

**No arquivo de saída**, o bloco acima é substituído por:

```markdown
variável `a` é maior que oito e a soma com `b` é 15, sendo que a data de início é 2023-01-01
```

O `template_engine.py` utiliza diretrizes de segurança, como:
```python
globals = {"__builtins__": SAFE_BUILTINS}
locals = runtime_context
```
com um conjunto pequeno de builtins, por exemplo:
- abs, min, max, sum, len, round
- str, int, float, bool
- list, dict, tuple, set
- e os helpers do motor, conforme descrição mais adiante.

> Sabemos que os comandos python eval() ou exec() são perigosos. Assim, **este projeto não é destinado ao público em geral**.
> Os profissionais usuários devem ser orientados a trabalhar com segurança, evitando apagar arquivos ou alterar sistemas.
> Assim, a execução Python deste projeto deve ser considerada recurso para **ambiente confiável, operado por usuário treinado**. O uso de SAFE_BUILTINS reduz a superfície, mas não constitui sandbox robusta.

---

### 4.5 Interpolação de conteúdos computados

Conforme já apresentado, a injeção de valores no texto segue o padrão universal de templates textuais (Jinja/Liquid): `{{ nome_da_variavel }}`, podendo ser:
* **Variáveis Documentais:** Declaradas estaticamente no YAML (ex: `{{ contribuinte }}`).
* **Conteúdos Computados:** Gerados em tempo de execução quando do processamento do template, conforme agora aqui explicado.

Nesse sentido, foi criado o inline `{{ py: expr }}`, que equivale ao comando `python eval(expr)`, ou seja, substitui o conteúdo pelo resultado da expressão.

É a versão inline do fence multilinhas ` ```python sfia` (...) ` ``` `, que equivale ao comando `python exec( (...) )`. 

> O `:` como separador foi utilizado porque já é uma convenção conhecida (Django templates, Twig, YAML, etc).
> Foi pensando inicialmente em incluir o ` `` (backtick)`, mas não houve necessidade. O Jinja/Liquid tem essa convenção: tudo dentro de `{{ }}` **é** uma expressão. Não há necessidade de delimitador extra (backtick) porque o `{{` já sinaliza "aqui começa uma expressão". O `py: expr` é o prefixo que indica o tipo, acompanhado de argumentos, ou seja, um objeto com múltiplos termos, em conjunto. Por fim, o `}}` sinaliza "aqui termina a expressão"

Está disponível também, além da Expressão Python `{{ py: expr }}`, a expressão SQL `{{ sql: SELECT ... }}`

Da mesma forma que o fence ` ```sql sfia` (...) ` ``` ` substitui o SELECT pela tabela resultado em Markdown, este projeto de templates disponibiliza também o inline `{{ sql: expr }}`, que substitui o SELECT **apenas pelo conteúdo do primeiro campo da primeira linha**, que também pode ser interpolado diretamente no fluxo do texto usando a sintaxe de código computado inline, como no exemplo a seguir:
```markdown
Trata-se de auditoria da empresa {{ sql: SELECT max(nome) FROM _fiscal_participantedeclarado WHERE idParticipanteDeclarado = 1 }},
CNPJ {{ sql: SELECT max(cnpj) FROM _fiscal_participantedeclarado WHERE idParticipanteDeclarado = 1 }},
cujo período de apuração se inicia em {{ sql: SELECT min(referencia) FROM _imp_ReferenciasSelecionadasNaImportacao }}.
```
No caso do exemplo acima, o resultado no arquivo de saída seria:
```markdown
Trata-se de auditoria da empresa XPTO INDUSTRIA E COMERCIO LTDA,
CNPJ 43123789000134,
cujo período de apuração se inicia em 2021-01-01.
```
> **Regra de segurança:** se a consulta sql inline retornar mais de uma linha ou
> mais de uma coluna, o motor substitui pelo valor `[resultado ambíguo]`
> e registra um aviso no log de execução.

Em suma, embora haja vários termos `{{ ... ... ... }}` nos conteúdos computados, são todos considerados como **um único objeto** — uma expressão com tipo declarado no prefixo. Nesse sentido:
```
{{ nome_variavel }}    ← string do contexto
{{ sql: SELECT ... }}  ← expressão SQL
{{ py: expr }}         ← expressão Python
{{ py: sfia.get_history_query("Valores conforme GIAs (Operação Própria)") }}  ← função injetada pelo engine do parser, próximo tópico 
```

---

### 4.6 Interpolação de funções injetadas pelo engine do parser

Também estão disponibilizadas funções criadas por template_engine.py, como `sfia.get_history_query`:

Exemplo: `{{ py: sfia.get_history_query("Valores conforme GIAs (Operação Própria)") }}`

A função `sfia.get_history_query`, definida no backend, se conecta ao banco de log `_dbs/query_history.sqlite` , faz o `SELECT sql_query FROM history WHERE TITLE = 'Valores conforme GIAs (Operação Própria)' ORDER BY timestamp DESC LIMIT 1`, ou seja, retorna o **texto do SELECT** executado naquela consulta. Isso resolve um problema real: o auditor não precisa lembrar ou copiar o texto do SQL SELECT, ele busca uma referência (o título que foi apresentado) do texto do SQL SELECT que gerou a tabela que lhe interessa e pode, assim, trabalhar sobre esse texto do SQL SELECT original, usando por exemplo, WITH (select_original) ... SELECT (...).

Assim, ele referencia pelo nome semântico algo que o sistema já gerou antes.

Considerando que, como já apresentado, os fences ` ```sql sfia` (...) ` ``` ` e ` ```python sfia` (...) ` ``` ` podem ter variáveis interpoladas `{{ nome_da_variavel }}`, podem também ter conteúdos computados `{{ py: expr }}` e `{{ sql: SELECT ... }}`, como no exemplo a seguir:
```sql sfia
SELECT *
FROM
({{ py: sql.history_query(title="Valores conforme GIAs (Operação Própria)") }});
```

> Se `sql.history_query(title="...")` não encontrar o título no histórico, substitui por `[Erro]: [Histórico não encontrado: title=‘título’] */`

---

## 5. Namespace Python — Estrutura e Acesso

O namespace Python é um dicionário compartilhado dentro do documento, criado uma vez pelo motor no início da compilação e resetado a cada novo documento.

---

### 5.1. Como funciona tecnicamente

Quando o `template_engine.py` executa blocos `python sfia` ou avalia expressões `{{ py: ... }}`, passa sempre o mesmo dicionário como contexto de execução:

```python
# Criado uma vez por documento
self.py_namespace = {
    "__builtins__": SAFE_BUILTINS,
    "sfia": sfia_object,   # objeto de acesso ao sistema
}

# A cada bloco python sfia:
exec(codigo_do_bloco, self.py_namespace)

# A cada {{ py: expr }}:
resultado = eval(expr, self.py_namespace)
```

Variáveis criadas num bloco `python sfia` ficam no `self.py_namespace` e são visíveis por todos os blocos e expressões seguintes do mesmo documento.

---

### 5.2. O objeto `sfia` — acesso ao sistema

O motor injeta automaticamente um objeto `sfia` no namespace. Ele encapsula tudo que pertence ao sistema, evitando colisão com variáveis criadas pelo auditor.

```python
# Variáveis do YAML frontmatter
sfia.contribuinte      # → "XPTO INDUSTRIA E COMERCIO LTDA"
sfia.anobase           # → 2023
sfia.osf               # → "13005678267"

# Conexão com o banco de dados
sfia.conn              # conexão SQLite ativa
sfia.cursor            # cursor SQLite ativo

# Funções helper do motor
sfia.sql.history(title="...")   # busca query no histórico
```

Implementado com `SimpleNamespace` do Python:

```python
from types import SimpleNamespace
sfia_object = SimpleNamespace(**self.context)
sfia_object.conn   = self.conn
sfia_object.cursor = self.cursor
sfia_object.sql    = sql_helpers
```

---

### 5.3. Separação clara: sistema vs. auditor

> Atenção! Todos os blocos demonstrados nesta seção 5.3 são do tipo `python`, não são do tipo `python sia`, ou seja, *são exemplos técnicos da estrutura interna do python*, não são para serem usados nos templates. Os exemplos para templates estão na seção 5.4 !

O namespace Python do documento é um único dicionário. O motor divide esse dicionário em duas zonas lógicas:

**Zona do sistema — prefixo `sfia.`**

Tudo que o motor injeta fica dentro do objeto `sfia`, acessado com ponto:

```python
sfia.contribuinte          # variável do YAML frontmatter
sfia.anobase               # variável do YAML frontmatter
sfia.conn                  # conexão SQLite ativa
sfia.cursor                # cursor SQLite ativo
sfia.sql.history(title="") # função helper do motor
```

**Zona do auditor — namespace raiz, sem prefixo**

Tudo que o auditor cria nos blocos `python sfia` fica diretamente no dicionário raiz:

```python
total_autuado = 1_500_000.00   # criado pelo auditor
percentual_icms = 270_000.00   # criado pelo auditor
```

As duas zonas nunca colidem porque o auditor não pode criar uma variável chamada `sfia` — o motor protege essa chave.

---

* Como o Python trata internamente as variáveis do auditor

Quando o motor executa:

```python
exec(codigo_do_bloco, self.py_namespace)
```

o `self.py_namespace` é o dicionário que serve como `globals` para aquele `exec`. Então quando o bloco Python faz:

```python
total_autuado = 1_500_000.00
percentual_icms = total_autuado * 0.18
```

o Python internamente faz o equivalente a:

```python
self.py_namespace["total_autuado"] = 1_500_000.00
self.py_namespace["percentual_icms"] = 270_000.00
```

São literalmente entradas novas no dicionário `self.py_namespace`. É por isso que o bloco seguinte enxerga essas variáveis — elas já estão no dicionário quando o próximo `exec` ou `eval` roda.

Para acessar depois, o motor simplesmente lê o mesmo dicionário:

```python
# O motor acessa assim internamente:
self.py_namespace["total_autuado"]   # → 1500000.0
self.py_namespace["percentual_icms"] # → 270000.0

# O auditor acessa assim nos blocos seguintes:
total_autuado    # Python busca no dicionário automaticamente
percentual_icms  # idem
```

E quando o auditor escreve `{{ py: f"R$ {total_autuado:,.2f}" }}`, o motor chama:

```python
eval('f"R$ {total_autuado:,.2f}"', self.py_namespace)
# Python encontra total_autuado no dicionário → "R$ 1.500.000,00"
```

O dicionário `self.py_namespace` é o fio condutor de tudo — variáveis do sistema, variáveis do auditor, funções helper. A única diferença é que as do sistema ficam encapsuladas dentro do objeto `sfia`, e as do auditor ficam soltas na raiz do dicionário.

---

### 5.4. Exemplos práticos para uso nos templates

```python sfia
# Lê variáveis do sistema
periodo = f"{{ anobase }}-01-01 a {{ anobase }}-12-31"

# Cria variável própria no namespace raiz
total_autuado = 1_500_000.00
percentual_icms = total_autuado * 0.18
contribuinte = "XPTO Ltda"
```

Acima, esse bloco `python sfia` não será visível no markdown gerado. Nos textos markdown, exemplos a seguir de como é possível reproduzir variáveis de duas formas:
* Período = {{ py: periodo + ' teste' }}
* Período = {{ periodo }}

Resultado:
* Período = 2024-01-01 a 2024-12-31 teste
* Período = 2024-01-01 a 2024-12-31

Exemplos com blocos e expressões seguintes do mesmo documento:

```python sfia
# total_autuado e percentual_icms já existem no namespace
print(f"ICMS estimado: R$ {percentual_icms:,.2f}")
```
Resultado: ICMS estimado: R$ 270,000.00

```markdown
Contribuinte: {{ contribuinte }}
Total autuado: {{ py: f"R$ {total_autuado:,.2f}" }}
ICMS estimado: {{ py: f"R$ {percentual_icms:,.2f}" }}
```

Resultado:
```markdown
Contribuinte: XPTO Ltda
Total autuado: R$ 1,500,000.00
ICMS estimado: R$ 270,000.00
```

---

### 5.5. Regras de segurança do namespace

- O auditor **não pode** criar uma variável chamada `sfia` — o motor ignora qualquer tentativa de sobrescrever o objeto `sfia` no namespace.
- Expressões `{{ py: ... }}` **não podem** criar ou alterar variáveis — são somente leitura (avaliadas com `eval`, não `exec`). Qualquer lógica de estado deve estar em blocos `python sfia`.
- O namespace é **resetado** a cada novo documento compilado. Variáveis de um `.tmpl.md` não vazam para o próximo template processado.

## 6. Resumo Geral

### Especificações Técnicas (SFIA)

* Code Fences (Blocos de Código):
   * Bloco SQL: `sql sfia`
   * Bloco Python: `python sfia`

* Expressões Inline:
   * Interpolação de variáveis: `{{ nome_variavel }}`
   * Leitura escalar via SQL: `{{ sql: ... }}`
   * Leitura/cálculo via Python: `{{ py: ... }}`

> As expressões inline são usadas **APENAS** para leitura, interpolação e cálculo de valores.
> Elas **NÃO PODEM**:
> - executar comandos com efeito colateral;
> - alterar valores já existentes;
> - criar novas variáveis no namespace Python;
> - gerar tabelas em Markdown;
modificar quanto à criação de tabelas e índices no SQLite, contexto, estado ou fluxo do documento.
>
> Em outras palavras: inline serve somente para **avaliar** e **retornar** um valor.
> Qualquer lógica de execução, criação ou alteração de estado deve ocorrer **exclusivamente** em blocos `python sfia` ou, futuramente, somente quanto à criação de tabelas e índices no SQLite, via sql.exec previsto para v0.4.

* Namespace Python:
   * Compartilhado dentro do mesmo documento.
   * Resetado sempre que se inicia um novo documento.

* Processamento:
   * Fluxo único (linear), na ordem de aparição.
   * Sem recursividade: se o resultado de `{{ py: ... }}` ou `{{ sql: ... }}` contiver outro `{{ ... }}`, o conteúdo gerado **não** é reprocessado.

### Ordem de Processamento do Backend Motor `template_engine.py`

1. **Frontmatter**
2. **Banco principal e attaches**
3. **Corpo processado em fluxo** (na ordem em que aparece):
     * **Fences** (` ```sql sfia ` e ` ```python sfia `):
         * Resolvem inlines internos `{{ ... }}` antes da execução.
         * Bloco sql sfia: substituído pela tabela Markdown resultante.
         * Bloco python sfia: substituído pela saída do print(). Se não houver print(), o bloco desaparece do documento. Se houver erro, a mensagem de erro é inserida no lugar do bloco.
    * **Trechos de texto**:
        * Resolvem inlines internos `{{ ... }}` antes da gravação.
        

## 7. Frontend: o que o Viewer `md-viewer-pm.html` Faz (e Não Faz)

O viewer atual `md-viewer-pm.html` renderiza o `.md` de saída com fidelidade — suporta
frontmatter, callouts, task lists, Mermaid e emojis.

Ele **não** executa nenhuma das funcionalidades apresentadas acima. Ou seja:

| Capacidade | FrontEnd - `md-viewer-pm.html` | Backend - Motor `template_engine.py` `*.tmpl.md` |
| :--- | :---: | :---: |
| Renderizar tabelas Markdown | ✅ | ❌ |
| Renderizar callouts / Mermaid | ✅ | ❌ |
| Conectar a bancos SQLite | ❌ | ✅ |
| Interpolar variáveis `{{ nome_da_variavel }}` | ❌ | ✅ |
| Resolver ` ```sql sfia` (...) ` ``` ` e ` ```python sfia` (...) ` ``` ` | ❌ | ✅ |
| Executar `{{ py: expr }}` e `{{ sql: SELECT ... }}` | ❌ | ✅ |

> Especificação pertence ao projeto **VC — Vibe Coding Microapps**