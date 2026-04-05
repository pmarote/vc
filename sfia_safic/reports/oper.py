"""
Relatório Operações
"""
from ._helpers import executar_e_formatar, iniciar_relatorio

def gerar_rel_oper(cursor, out_path):

    sql_base = f"""
        SELECT  EI.cfop AS cfopcv,
          CASE WHEN EI.cfop < 5000 THEN -AA.valorDaOperacao ELSE AA.valorDaOperacao END AS es_valcon,
          CASE WHEN EI.cfop < 5000 THEN -AA.bcIcmsOpPropria ELSE AA.bcIcmsOpPropria END AS es_bcicms,
          CASE WHEN EI.cfop < 5000 THEN -AA.icmsProprio ELSE AA.icmsProprio END AS es_icms,
          CASE WHEN EI.cfop < 5000 THEN -AA.bcIcmsSt ELSE AA.bcIcmsSt END AS es_bcicmsst,
          CASE WHEN EI.cfop < 5000 THEN -AA.icmsSt ELSE AA.icmsSt END AS es_icmsst,
          EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif,
        '[DocAtrib_fiscal_DocAtributosDeApuracao]' AS tAA, AA.*, '[DocAtrib_fiscal_DocAtributos]' AS tA, A.*, '[idDocAtributos_compl]' AS tB, B.*, '[docAtribTudao]' AS tDA_T, DA_T.*
        FROM  DocAtrib_fiscal_DocAtributosDeApuracao AS AA
        LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AA.idDocAtributos
        LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN docAtribTudao AS DA_T ON DA_T.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN cfopEntSai AS CES ON CES.cfop_dfe = CAST(AA.cfop AS INT)
        LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN CES.cfop_efd ELSE CAST(AA.cfop AS INT) END
    """

    iniciar_relatorio(out_path, "Relatório de Operações")
    where = "1 = 1"

    executar_e_formatar(f"""
        {sql_base} LIMIT 2
    """, cursor, out_path, "Amostra das Operações (Top 2)")

    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, tp_oper, tp_codSit, 
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        GROUP BY tp_origem, tp_oper, tp_codSit
    """, cursor, out_path, "Resumo por Situação")


    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, g1, 
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1
    """, cursor, out_path, "Resumo por Grupo (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, g1, g2,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, g2
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n2_1 (Apenas Documentos Válidos)")

    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, g1, dfi,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, dfi
    """, cursor, out_path, "Resumo por Grupo_n2_2 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, g1, classe, descri_simplif,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, classe, descri_simplif
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n3 (Apenas Documentos Válidos)")

    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, g1, dfi, classe, descri_simplif,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, dfi, classe, descri_simplif
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n3_2 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, g1, dfi, classe, descri_simplif, aliqIcms,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, dfi, classe, descri_simplif, aliqIcms
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n4 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, g1, dfi, classe, descri_simplif, aliqIcms, indOrigem, cstCsosnIcms,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, dfi, classe, descri_simplif, aliqIcms, indOrigem, cstCsosnIcms
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n5 (Apenas Documentos Válidos)")

    # =========================================================================
    # NOVAS VISÕES ESTRATÉGICAS por Vibe Code
    # =========================================================================

    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, tp_oper, cnpj_part, nome_part,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms
        FROM Base
        WHERE tp_codSit = 'válido' AND cnpj_part IS NOT NULL AND cnpj_part != ''
        GROUP BY tp_origem, tp_oper, cnpj_part, nome_part
        ORDER BY tp_origem, tp_oper, es_valcon DESC
        LIMIT 50
    """, cursor, out_path, "Curva ABC - Top 50 Participantes (Valores Válidos)")

    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, tp_oper, uf_part,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_icms), 2) as es_icms,
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM Base
        WHERE tp_codSit = 'válido' AND uf_part IS NOT NULL AND uf_part != ''
        GROUP BY tp_origem, tp_oper, uf_part
        ORDER BY tp_origem, tp_oper, es_valcon DESC
    """, cursor, out_path, "Visão Geográfica - Concentração por UF (Valores Válidos)")

    executar_e_formatar(f"""
        WITH Base AS ({sql_base})
        SELECT 
            tp_origem, tp_oper, substr(dtEmissao, 1, 7) as mes_ano,
            COUNT(1) as qtd_documentos,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_icms), 2) as es_icms
        FROM Base
        WHERE tp_codSit = 'válido' AND dtEmissao != '0001-01-01'
        GROUP BY tp_origem, tp_oper, mes_ano
        ORDER BY tp_origem, tp_oper, mes_ano
    """, cursor, out_path, "Evolução Temporal - Faturamento e Crédito por Mês (Valores Válidos)")