"""
Relatório Safic Menu Detalhes — top-N por idClassificacao com UNION de demais itens.
Tabela safic_drilldown persistente no banco de dados com relacionamento ZRowId.
"""
import sys
import re
from pathlib import Path
from ._helpers import executar_e_formatar, iniciar_relatorio

# IMPORTANTE: Garanta que tem a função export_excel importada do seu módulo exporter.py
# from exportador.exporter import export_excel
# --- RESOLUÇÃO DE CAMINHOS PARA O EXPORTADOR ---
# Sobe 3 níveis: reports -> sfia_safic -> vc
VC_ROOT = Path(__file__).resolve().parent.parent.parent
EXPORTADOR_DIR = VC_ROOT / "exportador"

# Adiciona a pasta do exportador ao path do Python para permitir o import
if str(EXPORTADOR_DIR) not in sys.path:
    sys.path.insert(0, str(EXPORTADOR_DIR))

try:
    from exporter import export_excel, export_tsv
except ImportError as e:
    print(f"\n[AVISO] Falha ao importar dependências do exportador: {e}")
    print("Dica: Certifique-se de ter rodado os uvs certinhos dentro da pasta sfia_safic e também exportador.")
    export_excel = None
    export_tsv = None

# Template reutilizável para todos os itens de menu (MARKDOWN)
_MENU_TOP_TEMPLATE = """
    WITH BaseDados AS (
        SELECT {campos_adic}
            tp_codSit, tp_oper,
            CASE
                WHEN length(Part) > 120 THEN substr(Part, 1, 30) || '<br>' || substr(Part, 31, 30) || '<br>' || substr(Part, 61, 30) || '<br>' || substr(Part, 91, 30) || '<br>' || substr(Part, 121)
                WHEN length(Part) > 90 THEN substr(Part, 1, 30) || '<br>' || substr(Part, 31, 30) || '<br>' || substr(Part, 61, 30) || '<br>' || substr(Part, 91)
                WHEN length(Part) > 60 THEN substr(Part, 1, 30) || '<br>' || substr(Part, 31, 30) || '<br>' || substr(Part, 61)
                WHEN length(Part) > 30 THEN substr(Part, 1, 30) || '<br>' || substr(Part, 31)
                ELSE Part
            END AS Part,
            ChNrOrigem, ChNrCfops, ChNrCodSit,
            count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(dif_icmsstSP) AS dif_icmsstSP,
            sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD,
            sum(vl_docDFe) AS vl_docDFe, sum(vl_docEFD) AS vl_docEFD,
            CASE
                WHEN length(DFeDescris) > 300 THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91, 30) || '<br>' || substr(DFeDescris, 121, 30) || '<br>' || substr(DFeDescris, 151, 30) || '<br>' || substr(DFeDescris, 181, 30) || '<br>' || substr(DFeDescris, 211, 30) || '<br>' || substr(DFeDescris, 241, 30) || '<br>' || substr(DFeDescris, 271, 30) || '<br>' || substr(DFeDescris, 301, 18) || '(...CORTADO)' 
                WHEN length(DFeDescris) > 270 THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91, 30) || '<br>' || substr(DFeDescris, 121, 30) || '<br>' || substr(DFeDescris, 151, 30) || '<br>' || substr(DFeDescris, 181, 30) || '<br>' || substr(DFeDescris, 211, 30) || '<br>' || substr(DFeDescris, 241, 30) || '<br>' || substr(DFeDescris, 271)
                WHEN length(DFeDescris) > 240 THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91, 30) || '<br>' || substr(DFeDescris, 121, 30) || '<br>' || substr(DFeDescris, 151, 30) || '<br>' || substr(DFeDescris, 181, 30) || '<br>' || substr(DFeDescris, 211, 30) || '<br>' || substr(DFeDescris, 241)
                WHEN length(DFeDescris) > 210 THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91, 30) || '<br>' || substr(DFeDescris, 121, 30) || '<br>' || substr(DFeDescris, 151, 30) || '<br>' || substr(DFeDescris, 181, 30) || '<br>' || substr(DFeDescris, 211)
                WHEN length(DFeDescris) > 180 THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91, 30) || '<br>' || substr(DFeDescris, 121, 30) || '<br>' || substr(DFeDescris, 151, 30) || '<br>' || substr(DFeDescris, 181)
                WHEN length(DFeDescris) > 150 THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91, 30) || '<br>' || substr(DFeDescris, 121, 30) || '<br>' || substr(DFeDescris, 151)
                WHEN length(DFeDescris) > 120 THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91, 30) || '<br>' || substr(DFeDescris, 121)
                WHEN length(DFeDescris) > 90  THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61, 30) || '<br>' || substr(DFeDescris, 91)
                WHEN length(DFeDescris) > 60  THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31, 30) || '<br>' || substr(DFeDescris, 61)
                WHEN length(DFeDescris) > 30  THEN substr(DFeDescris, 1, 30) || '<br>' || substr(DFeDescris, 31)
                ELSE DFeDescris
            END AS AmostraDFeDescris,
            CASE
                WHEN length(obs) > 400 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121, 40) || '<br>' || substr(obs, 161, 40) || '<br>' || substr(obs, 201, 40) || '<br>' || substr(obs, 241, 40) || '<br>' || substr(obs, 281, 40) || '<br>' || substr(obs, 321, 40) || '<br>' || substr(obs, 361, 40) || '<br>' || substr(obs, 401, 28) || '(...CORTADO)' 
                WHEN length(obs) > 360 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121, 40) || '<br>' || substr(obs, 161, 40) || '<br>' || substr(obs, 201, 40) || '<br>' || substr(obs, 241, 40) || '<br>' || substr(obs, 281, 40) || '<br>' || substr(obs, 321, 40) || '<br>' || substr(obs, 361)
                WHEN length(obs) > 320 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121, 40) || '<br>' || substr(obs, 161, 40) || '<br>' || substr(obs, 201, 40) || '<br>' || substr(obs, 241, 40) || '<br>' || substr(obs, 281, 40) || '<br>' || substr(obs, 321)
                WHEN length(obs) > 280 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121, 40) || '<br>' || substr(obs, 161, 40) || '<br>' || substr(obs, 201, 40) || '<br>' || substr(obs, 241, 40) || '<br>' || substr(obs, 281)
                WHEN length(obs) > 240 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121, 40) || '<br>' || substr(obs, 161, 40) || '<br>' || substr(obs, 201, 40) || '<br>' || substr(obs, 241)
                WHEN length(obs) > 200 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121, 40) || '<br>' || substr(obs, 161, 40) || '<br>' || substr(obs, 201)
                WHEN length(obs) > 160 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121, 40) || '<br>' || substr(obs, 161)
                WHEN length(obs) > 120 THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81, 40) || '<br>' || substr(obs, 121)
                WHEN length(obs) > 80  THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41, 40) || '<br>' || substr(obs, 81)
                WHEN length(obs) > 40  THEN substr(obs, 1, 40) || '<br>' || substr(obs, 41)
                ELSE obs
            END AS AmostraObs,
            ROW_NUMBER() OVER (ORDER BY {order_by}) AS ranking
        FROM chaveNroTudao WHERE ChNrClassifs LIKE '%{classif}%' GROUP BY {campos_adic} tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops, ChNrCodSit
    )
    SELECT {campos_adic} substr(tp_codSit, 1, 6) AS codSit, tp_oper AS op, Part, ChNrOrigem, replace(ChNrCfops, '-', '<br>') AS Cfops, ChNrCodSit AS CdSt, qtd,
      dif_vl_doc, dif_icms, dif_icmsstSP, vl_icmsDFe AS icmsDFe, vl_icmsEFD AS icmsEFD,
      vl_icmsstSP_DFe AS icmsstDFeSP, vl_icmsstSP_EFD AS icmsstEFDSP, vl_docDFe, vl_docEFD, AmostraDFeDescris, AmostraObs
    FROM BaseDados WHERE ranking <= {top_n}
    UNION ALL
    SELECT {campos_adic} '---' AS tp_codSit, '---' AS tp_oper, 'DEMAIS ITENS (SOMA)' AS Part, '---' AS ChNrOrigem, '---' AS ChNrCfops, '---' AS CdSt, SUM(qtd) AS qtd,
      SUM(dif_vl_doc) AS dif_vl_doc, SUM(dif_icms) AS dif_icms, SUM(dif_icmsstSP) AS dif_icmsstSP, SUM(vl_icmsDFe) AS vl_icmsDFe, SUM(vl_icmsEFD) AS vl_icmsEFD,
      SUM(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, SUM(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD, SUM(vl_docDFe) AS vl_docDFe, SUM(vl_docEFD) AS vl_docEFD, AmostraDFeDescris, AmostraObs
    FROM BaseDados WHERE ranking > {top_n} HAVING COUNT(*) > 0;
    """

# Template para a extração detalhada  (Tabela Temporária) com Top 10 faturas por grupo + Demais Notas "Drill-Down"
_DETALHE_SQLITE_TEMPLATE = """
    WITH RankGrupos AS (
        -- 1. Identifica os grupos originais e recria o mesmo Ranking do relatório MD
        SELECT 
            tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops,
            ROW_NUMBER() OVER (ORDER BY {group_order_by}) AS grp_rank
        FROM chaveNroTudao 
        WHERE ChNrClassifs LIKE '%{classif}%' 
        GROUP BY tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops
    ),
    Filtrados AS (
        -- 2. Cruza a tabela principal apenas com os grupos que passaram no Top N
        SELECT T.*, T.rowid AS ZRowId, G.grp_rank
        FROM chaveNroTudao T
        INNER JOIN RankGrupos G 
            ON T.tp_codSit = G.tp_codSit 
           AND T.tp_oper = G.tp_oper 
           AND T.Part = G.Part 
           AND T.ChNrOrigem = G.ChNrOrigem 
           AND T.ChNrCfops = G.ChNrCfops
        WHERE G.grp_rank <= {top_n}
    ),
    RankNotas AS (
        -- 3. Cria um Ranking secundário: qual é a maior/mais importante nota DENTRO de cada grupo
        SELECT 
            *,
            ROW_NUMBER() OVER (PARTITION BY grp_rank ORDER BY {doc_order_by}) AS nota_rank
        FROM Filtrados
    )
    -- 4A. Extrair as faturas individuais (Top N Notas)
    SELECT 
        '{classif}' AS Classificacao,
        grp_rank AS Ranking_Grupo,
        nota_rank AS Ranking_Nota,
        ZRowId,
        tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops,
        numero AS Numero_Documento,
        dif_vl_doc, dif_icms, dif_icmsstSP, 
        vl_icmsDFe, vl_icmsEFD, vl_icmsstSP_DFe, vl_icmsstSP_EFD, 
        vl_docDFe, vl_docEFD
    FROM RankNotas
    WHERE nota_rank <= {limite_notas}

    UNION ALL

    -- 4B. Esmagar o "Farelo" (Notas que ficaram abaixo do limite de 10)
    SELECT 
        '{classif}' AS Classificacao,
        grp_rank AS Ranking_Grupo,
        999999 AS Ranking_Nota,
        NULL AS ZRowId,
        tp_codSit, tp_oper, 
        'DEMAIS NOTAS (' || COUNT(numero) || ')' AS Part, 
        ChNrOrigem, ChNrCfops,
        COUNT(numero) || ' docs' AS Numero_Documento,
        SUM(dif_vl_doc), SUM(dif_icms), SUM(dif_icmsstSP), 
        SUM(vl_icmsDFe), SUM(vl_icmsEFD), SUM(vl_icmsstSP_DFe), SUM(vl_icmsstSP_EFD), 
        SUM(vl_docDFe), SUM(vl_docEFD)
    FROM RankNotas
    WHERE nota_rank > {limite_notas}
    GROUP BY grp_rank, tp_codSit, tp_oper, ChNrOrigem, ChNrCfops
    """

def _inserir_detalhe_banco(cursor, classif: str, top_n="18", limite_notas=10, group_order_by="sum(vl_docDFe) DESC"):
    """
    Formata a query de Drill-Down e insere os resultados na tabela persistente safic_drilldown.
    """
    doc_order_by = re.sub(r'sum\((.*?)\)', r'ABS(\1)', group_order_by, flags=re.IGNORECASE)
    
    query = _DETALHE_SQLITE_TEMPLATE.format(
        classif=classif,
        top_n=top_n,
        limite_notas=limite_notas,
        group_order_by=group_order_by,
        doc_order_by=doc_order_by
    )
    
    try:
        cursor.execute(f"INSERT INTO safic_drilldown {query}")
    except Exception as e:
        print(f"    [ERRO SQL] Falha ao inserir detalhes de {classif} no banco: {e}")




def _executar_menu_det(cursor, out_path, classif, titulo, top_n="18", order_by="sum(vl_docDFe) DESC", campos_adic=""):
    """Gera o Resumo MD e empilha o Relacionamento na tabela SQLite."""
    # 1. GERA O MARKDOWN (Visão Macro)
    query_md = _MENU_TOP_TEMPLATE.format(
        classif=classif,
        top_n=top_n,
        order_by=order_by,
        campos_adic=campos_adic
    )
    executar_e_formatar(query_md, cursor, out_path, titulo)
    
    # 2. INSERE AS CHAVES NA TABELA (Visão Micro/Drill-down)
    _inserir_detalhe_banco(
        cursor=cursor, 
        classif=classif, 
        top_n=top_n, 
        limite_notas=10, 
        group_order_by=order_by
    )

def gerar_rel_safic_menu_det(cursor, out_path, xls_dir: Path, debug=False):
    iniciar_relatorio(out_path, "Análises do Safic - Detalhes", debug=debug)

    # =========================================================================
    # PREPARAÇÃO: Criar tabela PERSISTENTE (safic_drilldown)
    # =========================================================================
    print(" ➔ Preparando tabela unificada e persistente de drill-down...")
    
    # Limpa a tabela caso o auditor esteja a rodar o script novamente na mesma base
    cursor.execute("DROP TABLE IF EXISTS safic_drilldown;")
    
    # Criação da tabela com o ZRowId (Para suportar o relacionamento final)
    cursor.execute("""
        CREATE TABLE safic_drilldown (
            Classificacao TEXT,
            Ranking_Grupo INTEGER,
            Ranking_Nota INTEGER,
            ZRowId INTEGER,
            tp_codSit TEXT,
            tp_oper TEXT,
            Part TEXT,
            ChNrOrigem TEXT,
            ChNrCfops TEXT,
            Numero_Documento TEXT,
            dif_vl_doc REAL,
            dif_icms REAL,
            dif_icmsstSP REAL,
            vl_icmsDFe REAL,
            vl_icmsEFD REAL,
            vl_icmsstSP_DFe REAL,
            vl_icmsstSP_EFD REAL,
            vl_docDFe REAL,
            vl_docEFD REAL
        );
    """)

    # --- INÍCIO DA EXECUÇÃO DOS MENUS ---
    _executar_menu_det(cursor, out_path, "[1]", "[1] Documentos escriturados cancelados")

    # Menus estáticos exclusivos: [2] e [9]
    executar_e_formatar("""
        SELECT tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops, count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(vl_docDFe) AS vl_docDFe, sum(vl_docEFD) AS vl_docEFD,
        sum(dif_icmsstSP) AS dif_icmsstSP, sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD
        FROM (SELECT * FROM chaveNroTudao WHERE ChNrClassifs LIKE '%[2]%' ORDER BY numero) GROUP BY tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops ORDER BY dif_icms
    """, cursor, out_path, "[2] E 1.13 - documentos escriturados em duplicidade")

    executar_e_formatar("""
        SELECT tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops, count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(dif_icmsstSP) AS dif_icmsstSP, sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD
        FROM (SELECT * FROM chaveNroTudao WHERE ChNrClassifs LIKE '%[9]%' ORDER BY numero) GROUP BY tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops ORDER BY dif_icms
    """, cursor, out_path, "[9] E 1.17 - operações realizadas com fornecedores com a inscrição suspensa, inapta, baixada ou nula no cadastro de contribuintes")

    # Demais menus via template
    _executar_menu_det(cursor, out_path, "[10]",  "[10] E 1.9 - crédito indevido (antecipado): escrituração antes da data de entrada", order_by="sum(dif_icms)")
    _executar_menu_det(cursor, out_path, "[12]",  "[12] E 1.14 - crédito de ICMS operação própria maior que o destacado no documento fiscal", order_by="sum(dif_icms)")
    _executar_menu_det(cursor, out_path, "[13]",  "[13] S 1.4 - débito a menor: débitos de ICMS OP escriturados a menor que no destaque do documento fiscal", order_by="sum(dif_icms) DESC")
    _executar_menu_det(cursor, out_path, "[14]",  "[14] E 1.20 - documentos de entrada não escriturados")
    _executar_menu_det(cursor, out_path, "[15]",  "[15] S 1.1 - inconsistência na escrituração: saídas não escrituradas")
    _executar_menu_det(cursor, out_path, "[16]",  "[16] S 1.1 - E 1.6 - simulação de entrada: documentos CANCELADOS escriturados como Válidos, mas são entradas SEM crédito")
    _executar_menu_det(cursor, out_path, "[18]",  "[18] S 1.14 - documentos fiscais cancelados escriturados como regulares")
    _executar_menu_det(cursor, out_path, "[20]",  "[20] NFes, CTes, NFCes e CFe SATs CANCELADOS destinados ao contribuinte auditado")
    _executar_menu_det(cursor, out_path, "[21]",  "[21] NFes, CTes, NFCes e CFe SATs sem EFD entregue no período")
    _executar_menu_det(cursor, out_path, "[24]",  "[24] E 1.8 - simulação de entrada: documento fiscal de saída escriturado como entrada sem crédito")
    _executar_menu_det(cursor, out_path, "[25]",  "[25] Operações de entrada com ST")
    _executar_menu_det(cursor, out_path, "[26]",  "[26] Operações de saída com ST")
    _executar_menu_det(cursor, out_path, "[35]",  "[35] CIAP 1.2 - saída de bens do ativo imobilizado")
    _executar_menu_det(cursor, out_path, "[36]",  "[36] CIAP 1.3 - apropriação de crédito de ativo imobilizado")
    _executar_menu_det(cursor, out_path, "[37]",  "[37] E 3.3 - análise de operações com materiais de uso e consumo")
    _executar_menu_det(cursor, out_path, "[38]",  "[38] ES 1.3 - análise de operações com armazéns gerais")
    _executar_menu_det(cursor, out_path, "[39]",  "[39] E 2.6 - análise de crédito de fornecedores enquadrados no Regime de apuração do Simples Nacional")
    _executar_menu_det(cursor, out_path, "[40]",  "[40] operações com a ZFM e as ALC")
    _executar_menu_det(cursor, out_path, "[41]",  "[41] operações com energia elétrica")
    _executar_menu_det(cursor, out_path, "[42]",  "[42] operações de aquisição de transporte")
    _executar_menu_det(cursor, out_path, "[43]",  "[43] operações de serv. de comunicação")
    _executar_menu_det(cursor, out_path, "[46]",  "[46] ES 1.1 - análise de operações com industrialização")
    _executar_menu_det(cursor, out_path, "[48]",  "[48] E 1.17 - operações realizadas com fornecedores com a inscrição suspensa...")
    _executar_menu_det(cursor, out_path, "[53]",  "[53] 9.3 l) margem de lucro ou preço de varejo inferior ao previsto na legislação nas operações de substituição tributária")
    _executar_menu_det(cursor, out_path, "[54]",  "[54] item 39.4: análise de saídas interestaduais com ST item 39.9: análise de situação cadastral do adquirente de saídas interestaduais com ST")
    _executar_menu_det(cursor, out_path, "[56]",  "[56] S 1.9 - operações com destinatários inscritos no cadastro de contribuintes, com situação cadastral inativa")
    _executar_menu_det(cursor, out_path, "[62]",  "[62] S 1.8 - operações com destinatários incluídos no cadastro de inidôneos")
    _executar_menu_det(cursor, out_path, "[63]",  "[63] S 1.8 - operações com destinatários incluídos no cadastro de inidôneos")
    _executar_menu_det(cursor, out_path, "[64]",  "[64] E 1.18 - crédito de operações próprias com substituição tributária")
    _executar_menu_det(cursor, out_path, "[65]",  "[65] E 1.4 - simulação de entrada: entrada escriturada, sem crédito, a partir de documento eletrônico sem relação com o contribuinte auditado")
    _executar_menu_det(cursor, out_path, "[67]",  "[67] S 2.6 - operações com destinatários localizados no Estado, mas não inscritos no cadastro de contribuintes")
    _executar_menu_det(cursor, out_path, "[69]",  "[69] E 1.16 - crédito indevido: entrada escriturada com CFOP que geralmente não aceita crédito", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    _executar_menu_det(cursor, out_path, "[70]",  "[70] CIAP 1.1 - entrada de bens para o ativo imobilizado")
    _executar_menu_det(cursor, out_path, "[71]",  "[71] E 3.1 - análise de entradas interestaduais de produtos importados, com alíquota do imposto superior a 4%", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    _executar_menu_det(cursor, out_path, "[72]",  "[72] E 3.2 - análise de crédito em operações com devolução de mercadorias")
    _executar_menu_det(cursor, out_path, "[73]",  "[73] ES 1.4 - análise de operações com CFOP 1949 / 2949 / 3949 / 5949 / 6949 / 7949")
    _executar_menu_det(cursor, out_path, "[77]",  "[77] S 2.5 - operações interestaduais com alíquota de 4%")
    _executar_menu_det(cursor, out_path, "[82]",  "[82] ES 1.6 - análise de operações envolvendo demonstração")
    _executar_menu_det(cursor, out_path, "[85]",  "[85] S 2.7 - operações de remessas para a Zona Franca de Manaus (ZFM) e Área de Livre Comércio (ALC)")
    _executar_menu_det(cursor, out_path, "[90]",  "[90] E 3.4 - análise de operações de devolução de mercadorias de maior valor")
    _executar_menu_det(cursor, out_path, "[98]",  "[98] E 1.5 - crédito indevido: documentos CANCELADOS escriturados COM crédito")
    _executar_menu_det(cursor, out_path, "[99]",  "[99] E 1.7 - crédito indevido: documento fiscal de saída escriturado como entrada com crédito", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    _executar_menu_det(cursor, out_path, "[100]", "[100] E 1.15 - crédito de ICMS ST maior que o destacado no documento fiscal", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    _executar_menu_det(cursor, out_path, "[103]", "[103] NFes e CTes sem relação com o contribuinte")
    _executar_menu_det(cursor, out_path, "[104]", "[104] S 1.3 - débito a menor: saídas regulares escrituradas como canceladas ou denegadas", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    _executar_menu_det(cursor, out_path, "[106]", "[106] S 1.10 - documentos eletrônicos emitidos com sequência numérica com intervalos")
    _executar_menu_det(cursor, out_path, "[107]", "[107] S 1.6 - nota fiscal complementar emitido após a referência da nota fiscal normal")
    _executar_menu_det(cursor, out_path, "[108]", "[108] S 1.11 - nota fiscal cancelada após o prazo de 24h da emissão")
    _executar_menu_det(cursor, out_path, "[109]", "[109] E 2.5 - operações de entrada escrituradas com crédito de ICMS OP")
    _executar_menu_det(cursor, out_path, "[110]", "[110] E 1.14 operações de entrada de crédito de ativo imobilizado e uso e consumo escrituradas com crédito")
    _executar_menu_det(cursor, out_path, "[111]", "[111] AP 1.4 - verificação do Difal nas operações de entrada interestaduais com uso e consumo e ativo imobilizado")
    _executar_menu_det(cursor, out_path, "[114]", "[114] NFes de emissão própria escrituradas com crédito")
    _executar_menu_det(cursor, out_path, "[115]", "[115] NFes de emissão de terceiro escrituradas com crédito")
    _executar_menu_det(cursor, out_path, "[117]", "[117] E 1.12 - simulação de entrada: escrituração, sem crédito, de documento com manifestação do destinatário negando a operação")
    _executar_menu_det(cursor, out_path, "[118]", "[118] S 1.16 - operações de saída escrituradas, com débito, de documento com manifestação do destinatário negando a operação")
    _executar_menu_det(cursor, out_path, "[119]", "[119] S 1.17 - operações de saída escrituradas, sem débito, de documento com manifestação do destinatário negando a operação")
    _executar_menu_det(cursor, out_path, "[280]", "[280] S 1.21 - operações internas de saída escrituradas por adquirente diverso da nota fiscal")
    _executar_menu_det(cursor, out_path, "[284]", "[284] S 1.23 - operações internas de saída para contribuinte sem escrituração na EFD do participante")
    _executar_menu_det(cursor, out_path, "[285]", "[285] S 1.24 - operações interestaduais de saída para contribuinte sem escrituração na EFD do participante")
    _executar_menu_det(cursor, out_path, "[367]", "[367] E 2.2 - análise de alíquotas de operações internas")
    _executar_menu_det(cursor, out_path, "[368]", "[368] E 2.3 - análise de alíquotas de operações interestaduais")
    _executar_menu_det(cursor, out_path, "[370]", "[370] E 2.9 - Crédito de CT-e vinculado a NF-e de saída com mercadoria isenta/não tributada")
    _executar_menu_det(cursor, out_path, "[371]", "[371] E 4.0 - análise de devoluções com lig. de ítem emissão própria")
    _executar_menu_det(cursor, out_path, "[372]", "[372] 4.0 - análise de devoluções com lig. de ítem emissão terceiros")
    _executar_menu_det(cursor, out_path, "[374]", "[374] E 4.2 - análise de devoluções sem lig. de ítem emissão terceiros")
    _executar_menu_det(cursor, out_path, "[375]", "[375] E 2.2 - análise de alíquotas de operações internas", campos_adic="DFeAliqs, EfdAliqs, ")
    _executar_menu_det(cursor, out_path, "[376]", "[376] E 2.4 - análise de alíquota em operações de transporte", campos_adic="DFeAliqs, EfdAliqs, ")

    # =========================================================================
    # FINALIZAÇÃO: Extração do Relacionamento Completo para o Excel
    # =========================================================================
    if export_excel:
        dir_destino = Path(out_path).parent
        nome_ficheiro = "safic_menu_detalhes_completo.xlsx"
        caminho_xlsx = xls_dir / nome_ficheiro
        
        print(f" ➔ Gerando Excel Unificado de Detalhamento em {caminho_xlsx}...")
        try:
            # Note: Usamos 'rowid' nativo do SQLite (que é em minúsculas por padrão no DB)
            cursor.execute("""
                SELECT
                  SD.Classificacao AS Clas, SD.Ranking_Grupo AS RankClas, SD.Ranking_Nota AS RankDoc,
                  SD.ZRowId, SD.Part, SD.Numero_Documento AS Doc,
                  SD.dif_vl_doc, SD.dif_icms, SD.dif_icmsstSP,
                  SD.vl_icmsDFe, SD.vl_icmsEFD, SD.vl_icmsstSP_DFe, SD.vl_icmsstSP_EFD,
                  SD.vl_docDFe, SD.vl_docEFD,
                  '[ChaveNroTudao]' AS tZ, Z.*
                FROM safic_drilldown AS SD
                LEFT OUTER JOIN chaveNroTudao AS Z ON Z.rowid = SD.ZRowId 
                ORDER BY 
                    CAST(REPLACE(REPLACE(SD.Classificacao, '[', ''), ']', '') AS INTEGER) ASC, 
                    SD.Ranking_Grupo ASC, 
                    SD.Ranking_Nota ASC
            """)
            linhas_exportadas = export_excel(cursor, caminho_xlsx)
            print(f"    [EXCEL OK] Exportou {linhas_exportadas} linhas com sucesso!")
        except Exception as e:
            print(f"    [ERRO EXCEL] Falha ao exportar excel unificado: {e}")
            
    # IMPORTANTE: A tabela 'safic_drilldown' não é apagada no final, 
    # ficando preservada fisicamente no banco de dados para o utilizador!