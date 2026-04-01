import sqlite3
from pathlib import Path
from to_markdown import export_markdown

# =============================================================================
# FUNÇÕES AUXILIARES
# =============================================================================

def executar_e_formatar(query, cursor, out_path, title):
    """Executa a query e faz o append do resultado formatado no arquivo MD."""
    try:
        cursor.execute(query)
        export_markdown(
            cursor=cursor, 
            out_path=out_path, 
            sql_query=query, 
            title=title, 
            mode="a" 
        )
    except Exception as e:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"## {title}\n\n**Erro na consulta:** `{e}`\n\n")

def iniciar_relatorio(out_path, titulo):
    """Cria o arquivo do relatório com o título e o link para o menu."""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n\n")
        f.write("#### Link para o menu de relatórios: [Menu de relatórios](menu_relatorios.md)\n\n")

# =============================================================================
# 1. RELATÓRIO DE DADOS BÁSICOS
# =============================================================================
def gerar_rel_basicos(cursor, out_path):
    iniciar_relatorio(out_path, "Relatório de Dados Básicos - e-CredAc Custeio")

    # Busca dinamicamente todas as tabelas existentes no banco de dados
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    tabelas = [row[0] for row in cursor.fetchall()]

    if not tabelas:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write("> ⚠️ **Nenhuma tabela encontrada no banco de dados.**\n\n")
        return

    # Tabelas que devem ser listadas por completo, sem LIMIT
    tabelas_sem_limite = [
        "Arquivos_transmitidos", 
        "Pedidos_eCredAc", 
        "Resumo_lancamentos_complementar", 
        "tgUFesp"
    ]

    for tabela in tabelas:
        if tabela in tabelas_sem_limite:
            query = f'SELECT * FROM "{tabela}";'
            titulo = f"Lista de linhas da Tabela: `{tabela}`"
        else:
            query = f'SELECT * FROM "{tabela}" LIMIT 5;'
            titulo = f"Amostra da Tabela: `{tabela}`"
            
        executar_e_formatar(query, cursor, out_path, titulo)

# =============================================================================
# 2. ESTUDOS BÁSICOS DE CUSTEIO
# =============================================================================
def gerar_rel_est_custeio(cursor, out_path):
    iniciar_relatorio(out_path, "Estudos Básicos de Custeio (Agrupamentos e Curvas ABC)")

    # Template SQL para Amostra com Aglutinação de Demais Itens
    TEMPLATE_AGRUPAMENTO_TOPN = """
    WITH BaseDados AS (
        SELECT 
            IFNULL("{campo}", '(Vazio)') AS "{campo}",
            COUNT(*) AS Qtd_Ocorrencias,
            SUM("Quantidade de Item") AS Sum_Qtd_Item,
            SUM("Valor Total da Operação") AS Sum_Valor_Tot_Oper,
            SUM("Valor do ICMS Debitado") AS Sum_Valor_ICMS_Deb,
            SUM("Valor do Custo - Item") AS Sum_Valor_Custo_Item,
            SUM("Valor do ICMS (Insumos)") AS Sum_Valor_ICMS_Insumos,
            SUM("Valor do Crédito Acumulado Gerado") AS Sum_Credito_Acum_Gerado,
            ROW_NUMBER() OVER (ORDER BY {order_by}) AS ranking
        FROM Fichas_3_Custeio 
        GROUP BY "{campo}"
    )
    SELECT 
        "{campo}", Qtd_Ocorrencias, Sum_Qtd_Item, Sum_Valor_Tot_Oper, 
        Sum_Valor_ICMS_Deb, Sum_Valor_Custo_Item, Sum_Valor_ICMS_Insumos, Sum_Credito_Acum_Gerado
    FROM BaseDados WHERE ranking <= {top_n}
    UNION ALL
    SELECT 
        '--- DEMAIS ITENS (SOMA) ---' AS "{campo}", SUM(Qtd_Ocorrencias), SUM(Sum_Qtd_Item), 
        SUM(Sum_Valor_Tot_Oper), SUM(Sum_Valor_ICMS_Deb), SUM(Sum_Valor_Custo_Item), 
        SUM(Sum_Valor_ICMS_Insumos), SUM(Sum_Credito_Acum_Gerado)
    FROM BaseDados WHERE ranking > {top_n} HAVING COUNT(*) > 0;
    """

    # Template SQL para Listar Todos (Sem Limite)
    TEMPLATE_AGRUPAMENTO_TODOS = """
    SELECT 
        IFNULL("{campo}", '(Vazio)') AS "{campo}",
        COUNT(*) AS Qtd_Ocorrencias,
        SUM("Quantidade de Item") AS Sum_Qtd_Item,
        SUM("Valor Total da Operação") AS Sum_Valor_Tot_Oper,
        SUM("Valor do ICMS Debitado") AS Sum_Valor_ICMS_Deb,
        SUM("Valor do Custo - Item") AS Sum_Valor_Custo_Item,
        SUM("Valor do ICMS (Insumos)") AS Sum_Valor_ICMS_Insumos,
        SUM("Valor do Crédito Acumulado Gerado") AS Sum_Credito_Acum_Gerado
    FROM Fichas_3_Custeio 
    GROUP BY "{campo}"
    ORDER BY {order_by};
    """

    def executar_agrupamento(campo, titulo, top_n="15", mostrar_todos=False):
        order_by = 'SUM("Valor do Crédito Acumulado Gerado") DESC, SUM("Valor Total da Operação") DESC'
        
        if mostrar_todos:
            query = TEMPLATE_AGRUPAMENTO_TODOS.replace("{campo}", campo).replace("{order_by}", order_by)
        else:
            query = TEMPLATE_AGRUPAMENTO_TOPN.replace("{campo}", campo).replace("{top_n}", top_n).replace("{order_by}", order_by)
            
        executar_e_formatar(query, cursor, out_path, titulo)

    # Execução sucessiva (Indicando 'mostrar_todos=True' onde você pediu que não houvesse amostra/limite)
    executar_agrupamento("Tipo do Documento", "1. Agrupamento por Tipo do Documento", mostrar_todos=True)
    executar_agrupamento("Número CNPJ Participante", "2. Agrupamento por Número CNPJ Participante")
    executar_agrupamento("Código CFOP", "3. Agrupamento por Código CFOP", mostrar_todos=True)
    executar_agrupamento("Descrição Lançamento", "4. Agrupamento por Descrição Lançamento", mostrar_todos=True)
    executar_agrupamento("Código Lançamento", "5. Agrupamento por Código Lançamento", mostrar_todos=True)
    executar_agrupamento("Descrição Item", "6. Agrupamento por Descrição Item")


# =============================================================================
# 3. CONFRONTOS CUSTEIO VS GIA
# =============================================================================
def gerar_rel_confrontos(cursor, out_path):
    iniciar_relatorio(out_path, "Confrontos de Arquivos - Custeio")

    # Confronto 1: GIA x Fichas_3
    # Utilizamos uma CTE "Chaves" para garantir que teremos a linha mesmo se o Mês/CFOP 
    # existir só na GIA ou só no Custeio.
    query_confronto = """
    WITH Chaves AS (
        SELECT "Mês Referência", "Código CFOP" FROM Comparacao_Arquivos_GIA
        UNION
        SELECT "Mês Referência", "Código CFOP" FROM Fichas_3_Custeio
    ),
    AgrupGIA AS (
        SELECT 
            "Mês Referência", 
            "Código CFOP",
            SUM("Valor Contabil - GIA") AS sum_GIA_Valor_Contabil,
            SUM("ICMS - GIA") AS sum_GIA_ICMS
        FROM Comparacao_Arquivos_GIA
        GROUP BY "Mês Referência", "Código CFOP"
    ),
    AgrupCusteio AS (
        SELECT 
            "Mês Referência", 
            "Código CFOP",
            SUM("Quantidade de Item") AS sum_Qtd_Item,
            SUM("Valor Total da Operação") AS sum_Valor_Tot_Oper,
            SUM("Valor do ICMS Debitado") AS sum_Valor_ICMS_Deb,
            SUM("Valor do Custo - Item") AS sum_Valor_Custo_Item,
            SUM("Valor do ICMS (Insumos)") AS sum_Valor_ICMS_Insumos,
            SUM("Valor do Crédito Acumulado Gerado") AS sum_Credito_Acum_Gerado
        FROM Fichas_3_Custeio
        GROUP BY "Mês Referência", "Código CFOP"
    )
    SELECT 
        C."Mês Referência", 
        C."Código CFOP",
        G.sum_GIA_Valor_Contabil,
        G.sum_GIA_ICMS,
        F.sum_Qtd_Item,
        F.sum_Valor_Tot_Oper,
        F.sum_Valor_ICMS_Deb,
        F.sum_Valor_Custo_Item,
        F.sum_Valor_ICMS_Insumos,
        F.sum_Credito_Acum_Gerado
    FROM Chaves C
    LEFT JOIN AgrupGIA G 
        ON IFNULL(C."Mês Referência",'') = IFNULL(G."Mês Referência",'') 
        AND IFNULL(C."Código CFOP",'') = IFNULL(G."Código CFOP",'')
    LEFT JOIN AgrupCusteio F 
        ON IFNULL(C."Mês Referência",'') = IFNULL(F."Mês Referência",'') 
        AND IFNULL(C."Código CFOP",'') = IFNULL(F."Código CFOP",'')
    ORDER BY 
        C."Mês Referência", C."Código CFOP";
    """
    
    titulo = "1. Comparação entre Arquivos GIA e Fichas_3 Custeio (Por Mês e CFOP)"
    executar_e_formatar(query_confronto, cursor, out_path, titulo)


# =============================================================================
# ORQUESTRADOR PRINCIPAL
# =============================================================================
def gerar_relatorios(db_osf: str, db_sia: str, db_siaCredAc: str, target_dir: Path):
    """
    Recebe os caminhos do main.py e gera os arquivos .md na pasta de destino.
    """
    print(f"🗄️ Conectando à base {Path(db_siaCredAc).name} e iniciando relatórios...")
    
    conn = sqlite3.connect(db_siaCredAc)
    cursor = conn.cursor()

    # Chamada sequencial das rotinas
    print(" ➔ Gerando Relatório de Dados Básicos...")
    gerar_rel_basicos(cursor, str(target_dir / "rel_eCredAc_basicos.md"))
    
    print(" ➔ Gerando Estudos Básicos Custeio...")
    gerar_rel_est_custeio(cursor, str(target_dir / "rel_eCredAc_Est_Custeio.md"))

    print(" ➔ Gerando Confrontos Arquivos Custeio...")
    gerar_rel_confrontos(cursor, str(target_dir / "rel_eCredAc_Confrontos.md"))

    conn.close()
    print("✅ Todos os relatórios foram gerados com sucesso e salvos no diretório indicado!")