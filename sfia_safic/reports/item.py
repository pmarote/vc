# sfia_safic/reports/item.py
import sqlite3
import time
from pathlib import Path
from ._helpers import executar_e_formatar, iniciar_relatorio

def gerar_rel_item(cursor, out_path):

    iniciar_relatorio(out_path, "Relatório de Itens")

    # =========================================================================
    # 1. AUTODESCOBERTA E ATTACH DO BANCO DE ITENS
    # =========================================================================
    
    cursor.execute("PRAGMA database_list;")
    # Configurações de alta performance para a sessão atual
#    cursor.execute("PRAGMA temp_store = MEMORY;") # Força tabelas temporárias para a RAM
#    cursor.execute("PRAGMA mmap_size = 30000000000;") # Permite mapear até 30GB na memória
#    cursor.execute("PRAGMA cache_size = -2000000;") # Dá 2GB de cache para o SQLite

    db_list = cursor.fetchall()
    sia_path = next((f for seq, name, f in db_list if name == 'main'), None)
    
    if not sia_path:
        print(" [ERRO] Não foi possível determinar o caminho do banco SIA.")
        return

    sia_file = Path(sia_path)
    item_db_name = sia_file.name.replace('sia', 'item')
    item_db_path = sia_file.parent / item_db_name

    cursor.execute(f"ATTACH DATABASE '{item_db_path}' AS db_item;")

    cursor.execute("SELECT name FROM db_item.sqlite_master WHERE type='table' AND name='tb_DAIg';")
    need_build = cursor.fetchone() is None

    # =========================================================================
    # 2. MATERIALIZAÇÃO (CACHE DEFINITIVO) EM ESTÁGIOS PARA ACELERAÇÃO
    # =========================================================================
    if need_build:
        print(f" ⏳ Criando banco de aceleração '{item_db_name}' (Isso pode levar alguns minutos)...")
        start_time = time.time()
        
        # ---------------------------------------------------------
        # ETAPA A: Extração Crua (Sem SUM/AVG e Sem GROUP BY)
        # Joga para a memória temporária (temp.) para não inchar o DB físico
        # ---------------------------------------------------------
        print("    [1/3] Fazendo os JOINs e extraindo dados brutos...")
        sql_raw = """
        SELECT 
            B.tp_oper, B.tp_codSit, B.tp_origem, B.origem,
            EI.cfop AS cfopcv, EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif,
            AI.referencia, AI.cstCsosnIcms, AI.indCstCsosn, AI.indOrigem, AI.cfop, AI.aliqIcms, AI.aliqIcmsSt, AI.unid,
            AI.COD_NCM, AI.CEST, 
            BI.cnpj AS BIcnpj, substr(CHV_DFE, 7, 14) AS CHV_DFE_CNPJ,
            BI.codigo AS BIcodigo, BI.descricao AS BIdescricao,
            CASE WHEN B.origem = 'EfdC100' THEN 'Usar dados dfe_fiscal_EfdC170' ELSE 'Usar dados dfe_fiscal_NfeC170' END AS FONTE,
            I.COD_ITEM, I.UNID AS I_UNID, I.IND_MOV, I.CST_ICMS, I.CFOP AS I_CFOP, I.COD_NAT, I.ALIQ_ICMS AS I_ALIQ_ICMS, 
            I.ALIQ_ST, I.IND_APUR, I.CST_IPI, I.COD_ENQ, I.ALIQ_IPI, I.COD_CTA,

            -- Valores numéricos puros (sem SUM/AVG ainda)
            CASE WHEN EI.cfop < 5000 THEN -AI.valorDaOperacao ELSE AI.valorDaOperacao END AS raw_es_valcon,
            CASE WHEN EI.cfop < 5000 THEN -AI.bcIcmsOpPropria ELSE AI.bcIcmsOpPropria END AS raw_es_bcicms,
            CASE WHEN EI.cfop < 5000 THEN -AI.icmsProprio ELSE AI.icmsProprio END AS raw_es_icms,
            CASE WHEN EI.cfop < 5000 THEN -AI.bcIcmsSt ELSE AI.bcIcmsSt END AS raw_es_bcicmsst,
            CASE WHEN EI.cfop < 5000 THEN -AI.icmsSt ELSE AI.icmsSt END AS raw_es_icmsst,
            
            AI.bcIcmsOpPropria, AI.bcIcmsSt, AI.valorDaOperacao, AI.icmsProprio, AI.icmsSt, AI.qtde,
            I.QTD AS I_QTD, I.VL_ITEM AS I_VL_ITEM, I.VL_DESC AS I_VL_DESC, I.VL_BC_ICMS AS I_VL_BC_ICMS, 
            I.VL_ICMS AS I_VL_ICMS, I.VL_BC_ICMS_ST AS I_VL_BC_ICMS_ST, I.VL_ICMS_ST AS I_VL_ICMS_ST, 
            I.VL_BC_IPI AS I_VL_BC_IPI, I.VL_IPI AS I_VL_IPI,

            AI.aliqEfetOpSemIpi, AI.aliqEfetOpComIpi, AI.mvaCalculado,
            I.aliqEfetOpSemIpi AS I_aliqEfetOpSemIpi, I.aliqEfetOpComIpi AS I_aliqEfetOpComIpi, I.mvaCalculado AS I_mvaCalculado

        FROM DocAtrib_fiscal_DocAtributosItem AS AI
        LEFT OUTER JOIN _fiscal_ItemServicoDeclarado AS BI ON BI.idItemServicoDeclarado = AI.idItemServicoDeclarado
        LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AI.idDocAtributos
        LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN docAtribTudao AS DA_T ON DA_T.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN dfe_fiscal_EfdC170 AS I ON I.idEfdC170 = AI.idRegistroItem AND A.indEmit = 1 AND B.origem = 'EfdC100'
        LEFT OUTER JOIN dfe_fiscal_NfeC170 AS H ON H.idNfeC170 = AI.idRegistroItem AND B.origem = 'NFe'
        LEFT OUTER JOIN cfopEntSai AS CES ON CES.cfop_dfe = CAST(AI.cfop AS INT)
        LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN CES.cfop_efd ELSE CAST(AI.cfop AS INT) END
        -- utilize um WHERE como o abaixo pra ganhar tempo no desenvolvimento
        -- WHERE AI.referencia = '2022-01-01'
        """
        cursor.execute("DROP TABLE IF EXISTS temp.tmp_raw_DAIg;")
        cursor.execute(f"CREATE TEMPORARY TABLE temp.tmp_raw_DAIg AS {sql_raw}")

        # ---------------------------------------------------------
        # ETAPA B: Criar índices na tabela crua para acelerar o agrupamento
        # ---------------------------------------------------------
        print("    [2/3] Criando índices na tabela crua...")
        # Índices nos campos que têm maior diversidade ou relevância no agrupamento geral
        # retirei esses índices abaixo porque eles não funcionam na prática, porque o GROUP BY é monstruoso
#        cursor.execute("CREATE INDEX temp.idx_raw_a ON tmp_raw_DAIg(tp_oper, tp_codSit, tp_origem, origem, cfopcv, dfi, st);")
#        cursor.execute("CREATE INDEX temp.idx_raw_b ON tmp_raw_DAIg(referencia);")
#        cursor.execute("CREATE INDEX temp.idx_raw_c ON tmp_raw_DAIg(BIcnpj);")

        # ---------------------------------------------------------
        # ETAPA C: Agrupar, Somar e Salvar no Banco Definitivo
        # ---------------------------------------------------------
        print("    [3/3] Esmagando os dados (GROUP BY) para o banco definitivo...")
        sql_agg = """
        SELECT 
            tp_oper, tp_codSit, tp_origem, origem, cfopcv, dfi, st, classe, g1, c3, g2, g3, descri_simplif,
            referencia, cstCsosnIcms, indCstCsosn, indOrigem, cfop, aliqIcms, aliqIcmsSt, unid,
            COD_NCM, CEST,
            BIcnpj, CHV_DFE_CNPJ,
            BIcodigo, BIdescricao, FONTE,
            COD_ITEM, I_UNID, IND_MOV, CST_ICMS, I_CFOP, COD_NAT, I_ALIQ_ICMS, ALIQ_ST, IND_APUR, CST_IPI, COD_ENQ, ALIQ_IPI, COD_CTA,

            ROUND(SUM(raw_es_valcon), 2) AS es_valcon,
            ROUND(SUM(raw_es_bcicms), 2) AS es_bcicms,
            ROUND(SUM(raw_es_icms), 2) AS es_icms,
            ROUND(SUM(raw_es_bcicmsst), 2) AS es_bcicmsst,
            ROUND(SUM(raw_es_icmsst), 2) AS es_icmsst,
            
            ROUND(SUM(bcIcmsOpPropria), 2) AS bcIcmsOpPropria,
            ROUND(SUM(bcIcmsSt), 2) AS bcIcmsSt,
            ROUND(SUM(valorDaOperacao), 2) AS valorDaOperacao,
            ROUND(SUM(icmsProprio), 2) AS icmsProprio,
            ROUND(SUM(icmsSt), 2) AS icmsSt,
            ROUND(SUM(qtde), 4) AS qtde,
            
            ROUND(SUM(I_QTD), 4) AS I_QTD,
            ROUND(SUM(I_VL_ITEM), 2) AS I_VL_ITEM,
            ROUND(SUM(I_VL_DESC), 2) AS I_VL_DESC,
            ROUND(SUM(I_VL_BC_ICMS), 2) AS I_VL_BC_ICMS,
            ROUND(SUM(I_VL_ICMS), 2) AS I_VL_ICMS,
            ROUND(SUM(I_VL_BC_ICMS_ST), 2) AS I_VL_BC_ICMS_ST,
            ROUND(SUM(I_VL_ICMS_ST), 2) AS I_VL_ICMS_ST,
            ROUND(SUM(I_VL_BC_IPI), 2) AS I_VL_BC_IPI,
            ROUND(SUM(I_VL_IPI), 2) AS I_VL_IPI,

            ROUND(AVG(aliqEfetOpSemIpi), 4) AS aliqEfetOpSemIpi,
            ROUND(AVG(aliqEfetOpComIpi), 4) AS aliqEfetOpComIpi,
            ROUND(AVG(mvaCalculado), 4) AS mvaCalculado,
            ROUND(AVG(I_aliqEfetOpSemIpi), 4) AS I_aliqEfetOpSemIpi,
            ROUND(AVG(I_aliqEfetOpComIpi), 4) AS I_aliqEfetOpComIpi,
            ROUND(AVG(I_mvaCalculado), 4) AS I_mvaCalculado

        FROM temp.tmp_raw_DAIg
        GROUP BY
            tp_oper, tp_codSit, tp_origem, origem, cfopcv,
            referencia, cstCsosnIcms, indCstCsosn, indOrigem, cfop, aliqIcms, aliqIcmsSt, unid,
            COD_NCM, CEST, BIcnpj, CHV_DFE_CNPJ, BIcodigo, BIdescricao, FONTE,
            COD_ITEM, I_UNID, IND_MOV, CST_ICMS, I_CFOP, COD_NAT, I_ALIQ_ICMS, ALIQ_ST, IND_APUR, CST_IPI, COD_ENQ, ALIQ_IPI, COD_CTA
        """
        # não coloquei dfi, st, classe, g1, c3, g2, g3, descri_simplif NO GROUP BY
        #   porque eles são ligados à cfopcv, só preciso então agrupar esse campo, ganho tempo e memória
        cursor.execute("DROP TABLE IF EXISTS db_item.tb_DAIg;")
        cursor.execute(f"CREATE TABLE db_item.tb_DAIg AS {sql_agg}")
        
        # Limpa a memória temporária
        cursor.execute("DROP TABLE temp.tmp_raw_DAIg;")
        
        # Índices definitivos para os seus relatórios
        print("    [+] Finalizando índices definitivos...")
        cursor.execute("CREATE INDEX db_item.idx_tb_codsit ON tb_DAIg(tp_codSit);")
        cursor.execute("CREATE INDEX db_item.idx_tb_g1 ON tb_DAIg(g1);")
        
        elapsed = time.time() - start_time
        print(f" ✅ Banco '{item_db_name}' construído com sucesso em {elapsed:.2f} segundos!")
    else:
        print(f" ⚡ Cache localizado: '{item_db_name}'! Pulando a materialização.")

    print(" 📊 Extraindo visões analíticas...")

    # =========================================================================
    # 3. EXTRAÇÃO DOS RELATÓRIOS (MANTIDO INTACTO)
    # =========================================================================

    executar_e_formatar(f"""
        SELECT * FROM db_item.tb_DAIg LIMIT 2
    """, cursor, out_path, "Amostra dos Itens (Top 2)")


    executar_e_formatar(f"""
        SELECT 
            tp_codSit, tp_origem, tp_oper,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM db_item.tb_DAIg
        GROUP BY tp_codSit, tp_origem, tp_oper
    """, cursor, out_path, "Resumo por Situação (tp_codSit)")


    executar_e_formatar(f"""
        SELECT 
            g1, 
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM db_item.tb_DAIg
        WHERE tp_codSit = 'válido'
        GROUP BY g1
    """, cursor, out_path, "Resumo por Grupo_n1 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        SELECT 
            tp_origem, g1, 
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM db_item.tb_DAIg
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1
    """, cursor, out_path, "Resumo por Grupo_n2 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        SELECT 
            tp_origem, g1, dfi,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM db_item.tb_DAIg
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, dfi
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n3_1 (Apenas Documentos Válidos)")

    executar_e_formatar(f"""
        SELECT 
            tp_origem, g1, classe, descri_simplif,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM db_item.tb_DAIg
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, classe, descri_simplif
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n3_2 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        SELECT 
            tp_origem, g1, dfi, classe, descri_simplif, aliqIcms,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM db_item.tb_DAIg
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, dfi, classe, descri_simplif, aliqIcms
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n4 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        SELECT 
            tp_origem, g1, dfi, classe, descri_simplif, aliqIcms, indOrigem, cstCsosnIcms,
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM db_item.tb_DAIg
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1, dfi, classe, descri_simplif, aliqIcms, indOrigem, cstCsosnIcms
        ORDER BY tp_origem, g1, es_valcon DESC
    """, cursor, out_path, "Resumo por Grupo_n5 (Apenas Documentos Válidos)")


    executar_e_formatar(f"""
        WITH BaseDados AS (
            SELECT 
                tp_codSit, tp_origem, tp_oper,
                COALESCE(BIcodigo, 'N/I') AS BIcodigo, 
                COALESCE(BIdescricao, 'SEM DESCRIÇÃO') AS BIdescricao,
                ROUND(SUM(es_valcon), 2) as es_valcon, 
                ROUND(SUM(es_bcicms), 2) as es_bcicms, 
                ROUND(SUM(es_icms), 2) as es_icms, 
                ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
                ROUND(SUM(es_icmsst), 2) as es_icmsst,
                ROW_NUMBER() OVER (
                    PARTITION BY tp_codSit, tp_origem, tp_oper 
                    ORDER BY ABS(SUM(es_valcon)) DESC
                ) as ranking
            FROM db_item.tb_DAIg
            GROUP BY tp_codSit, tp_origem, tp_oper, BIcodigo, BIdescricao
        ),
        VisaoFinal AS (
            -- Bloco 1: Os Top 20 itens
            SELECT 
                tp_codSit, tp_origem, tp_oper,
                BIcodigo, BIdescricao,
                es_valcon, es_bcicms, es_icms, es_bcicmsst, es_icmsst
            FROM BaseDados 
            WHERE ranking <= 20
            
            UNION ALL
            
            -- Bloco 2: O resto esmagado na linha 'DEMAIS ITENS'
            SELECT 
                tp_codSit, tp_origem, tp_oper,
                '---' AS BIcodigo, 'DEMAIS ITENS (SOMA)' AS BIdescricao,
                ROUND(SUM(es_valcon), 2) AS es_valcon, 
                ROUND(SUM(es_bcicms), 2) AS es_bcicms, 
                ROUND(SUM(es_icms), 2) AS es_icms, 
                ROUND(SUM(es_bcicmsst), 2) AS es_bcicmsst, 
                ROUND(SUM(es_icmsst), 2) AS es_icmsst
            FROM BaseDados 
            WHERE ranking > 20
            GROUP BY tp_codSit, tp_origem, tp_oper
            HAVING COUNT(*) > 0
        )
        
        -- Agora o SELECT externo pode usar CASE e ABS à vontade no ORDER BY!
        SELECT * FROM VisaoFinal
        ORDER BY 
            tp_codSit, tp_origem, tp_oper, 
            CASE WHEN BIcodigo = '---' THEN 1 ELSE 0 END, 
            ABS(es_valcon) DESC;
    """, cursor, out_path, "Top 20 Itens por Situação, Origem e Operação")
