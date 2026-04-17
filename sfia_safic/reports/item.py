"""
Relatório Itens
"""
import sys
from pathlib import Path
from ._helpers import executar_e_formatar, iniciar_relatorio

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

def gerar_rel_item(cursor, out_path, debug=False):

    iniciar_relatorio(out_path, "Relatório de Itens", debug=debug)

    # Define o caminho do novo banco de dados analítico na pasta --dir
    dir_out = Path(out_path).parent
    db_item_path = dir_out / "item_base.sqlite"
    
    print(" ➔ Criando visualização temporária no disco...")

    # Anexa o novo banco de dados (se o arquivo não existir, o SQLite cria na hora)
    cursor.execute(f"ATTACH DATABASE '{db_item_path}' AS item_db;")
    
    # Limpa a tabela caso o auditor esteja rodando o script pela segunda vez na mesma pasta
    cursor.execute("DROP TABLE IF EXISTS item_db.item_base;")

    cursor.execute("""
        CREATE TABLE item_db.item_base AS
        SELECT  EI.cfop AS cfopcv,
          CASE WHEN EI.cfop < 5000 THEN -AI.valorDaOperacao ELSE AI.valorDaOperacao END AS es_valcon,
          -- Classes de BC ICMS reduzidas
          CASE 
            WHEN AI.valorDaOperacao = 0 THEN 'ValCon=0'
            WHEN AI.bcIcmsOpPropria = 0 THEN 'BCIcms=0'
            WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) > 1 THEN '>100'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) > 0.995 THEN 'BCIcms=ValCon'
			WHEN ((AI.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) > 0.995 THEN 'BCIcms=ValConSemIpi'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) BETWEEN 0.222 AND 0.223 THEN 'BCIcms(4%)=ValCon'
			WHEN ((AI.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) BETWEEN 0.222 AND 0.223 THEN 'BCIcms(4%)=ValConSemIpi'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) BETWEEN 0.388 AND 0.389 THEN 'BCIcms(7%)=ValCon'
			WHEN ((AI.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) BETWEEN 0.388 AND 0.389 THEN 'BCIcms(7%)=ValConSemIpi'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) BETWEEN 0.666 AND 0.667 THEN 'BCIcms(12%)=ValCon'
			WHEN ((AI.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) BETWEEN 0.666 AND 0.667 THEN 'BCIcms(12%)=ValConSemIpi'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.90 THEN '90>99'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.80 THEN '80>89'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.70 THEN '70>79'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.60 THEN '60>69'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.50 THEN '50>59'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.40 THEN '40>49'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.30 THEN '30>39'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.20 THEN '20>29'
			WHEN (AI.bcIcmsOpPropria / NULLIF(AI.valorDaOperacao - AI.icmsSt, 0)) >= 0.10 THEN '10>19'
			ELSE '<10' 
          END AS redBCICMS,
          CASE WHEN EI.cfop < 5000 THEN -AI.bcIcmsOpPropria ELSE AI.bcIcmsOpPropria END AS es_bcicms,
          -- Classes de tipos de UFs e suas alíquotas típicas
          CASE 
		    WHEN DA_T.uf IN ('MG', 'PR', 'RJ', 'SC', 'RS') THEN 'UF12'
		    WHEN DA_T.uf IN ('ES', 'MS', 'MT', 'GO', 'DF', 'BA', 'AL', 'SE', 'PE', 'PB', 'RN', 'CE', 'PI', 'MA', 'TO', 'PA', 'AM', 'AP', 'RR', 'RO', 'AC') THEN 'UF7'
		    ELSE DA_T.uf
		  END AS tp_uf,
		  -- Classes de Alíquota ICMS Proprio
          CASE 
            WHEN AI.icmsProprio = 0 OR AI.bcIcmsOpPropria = 0 THEN '0'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.011 THEN '<1'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.021 THEN '1<2'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.039 THEN '2<4'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.041 THEN '4'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.069 THEN '4<7'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.071 THEN '7'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.119 THEN '7<12'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.121 THEN '12'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.132 THEN '12<13,3'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.134 THEN '13,3'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.179 THEN '13,3<18'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.181 THEN '18'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.249 THEN '18<25'
            WHEN (AI.icmsProprio / NULLIF(AI.bcIcmsOpPropria, 0)) < 0.251 THEN '25'
            ELSE '>25'
          END AS clAliqIcms,
          CASE WHEN EI.cfop < 5000 THEN -AI.icmsProprio ELSE AI.icmsProprio END AS es_icms,
          CASE 
            WHEN AI.bcIcmsOpPropria = 0 OR AI.bcIcmsSt = 0 THEN 0
            ELSE round(AI.bcIcmsSt / bcIcmsOpPropria * 100, 0)
          END AS IvaSt,
          CASE WHEN EI.cfop < 5000 THEN -AI.bcIcmsSt ELSE AI.bcIcmsSt END AS es_bcicmsst,
          -- Classes de Alíquota ICMS ST
          CASE 
            WHEN AI.icmsSt = 0 OR AI.bcIcmsSt = 0 THEN '0'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.011 THEN '<1'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.039 THEN '1<4'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.041 THEN '4'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.069 THEN '4<7'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.071 THEN '7'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.119 THEN '7<12'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.121 THEN '12'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.132 THEN '12<13,3'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.134 THEN '13,3'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.179 THEN '13,3<18'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.181 THEN '18'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 0)) < 0.249 THEN '18<25'
            WHEN (AI.icmsSt / NULLIF(AI.bcIcmsSt, 00)) < 0.251 THEN '25'
            ELSE '>25'
          END AS clAliqIcmsSt,
          CASE WHEN EI.cfop < 5000 THEN -AI.icmsSt ELSE AI.icmsSt END AS es_icmsst,
          EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif,
        '[DocAtrib_fiscal_DocAtributosItem]' AS tAI,
        AI.referencia, AI.cstCsosnIcms, AI.indCstCsosn, AI.indOrigem, AI.cfop AS AIcfop, AI.aliqIcms AS AIaliqIcms, AI.aliqIcmsSt AS AIaliqIcmsSt,
        AI.COD_NCM, AI.CEST, AI.qtde, AI.unid, AI.idItemServicoDeclarado,
        AI.aliqEfetOpSemIpi, AI.aliqEfetOpComIpi, AI.mvaCalculado,
        '[_fiscal_ItemServicoDeclarado]' AS tBI,
        BI.cnpj AS BIcnpj, BI.descricao AS BIdescricao, BI.codigo AS BIcodigo,
        '[DocAtrib_fiscal_DocAtributos]' AS tA,
        A.codSit, A.indOper, A.indEmit, A.ufOrg, A.ufDest, A.dtEmissao, A.dtEntSd, 
        A.vlTotalDoc, A.vlBcIcmsProprio, A.vlIcmsProprio, A.vlBcIcmsSt, A.vlIcmsSt, A.UfIniPrest, A.UfFimPrest,
        '[idDocAtributos_compl]' AS tB,
        B.tp_origem, B.origem, B.tp_oper, B.tp_codSit, B.cnpj_part, B.chave, B.NatOp,
        '[docAtribTudao]' AS tDA_T,
        DA_T.classifs, DA_T.ref	tp_origem, DA_T.origem, DA_T.tp_codSit, DA_T.indEmit, DA_T.indOper,
        DA_T.cfops, DA_T.cfopcvs, DA_T.g1s, DA_T.vlTotalDoc, DA_T.vlBcIcmsProprio, DA_T.vlIcmsProprio, DA_T.vlBcIcmsSt, DA_T.vlIcmsSt,
        DA_T.EfdPartCodSit, DA_T.EfdPartCfops, DA_T.EfdPartVal, DA_T.EfdPartIcms,
        DA_T.descris, DA_T.codncms, DA_T.aliqs, DA_T.chave,
        '[ChaveNroTudao]' AS tZ,
        Z.Part, Z.ChNrClassifs, Z.ChNrRef, Z.ChNrOrigem, Z.ChNrCodSit, Z.ChNrIndEmit, Z.ChNrIndOper, Z.ChNrCfops, Z.ChNrCfopcvs, Z.ChNrG1s,
        Z.DFeAliqs, Z.EfdAliqs, Z.obs
        FROM DocAtrib_fiscal_DocAtributosItem AS AI
        LEFT OUTER JOIN _fiscal_ItemServicoDeclarado AS BI ON BI.idItemServicoDeclarado = AI.idItemServicoDeclarado
        LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AI.idDocAtributos
        LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN docAtribTudao AS DA_T ON DA_T.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN ChaveNroTudao AS Z ON Z.chave = DA_T.chave
        LEFT OUTER JOIN cfopEntSai AS CES ON CES.cfop_dfe = CAST(AI.cfop AS INT)
        LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN CES.cfop_efd ELSE CAST(AI.cfop AS INT) END
    """)

    # 3. Geração dos Relatórios (Leitura direta e instantânea da tabela temporária)
    executar_e_formatar("""
        SELECT * FROM item_db.item_base LIMIT 2
    """, cursor, out_path, "Amostra das Operações (Top 2)")

    executar_e_formatar("""
        SELECT 
            tp_origem, tp_oper, tp_codSit, 
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM item_db.item_base
        GROUP BY tp_origem, tp_oper, tp_codSit
    """, cursor, out_path, "Resumo por Situação")

    executar_e_formatar("""
        SELECT 
            tp_origem, g1, 
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM item_db.item_base
        WHERE tp_codSit = 'válido'
        GROUP BY tp_origem, g1
    """, cursor, out_path, "Resumo por Grupo (Apenas Documentos Válidos)")

    executar_e_formatar("""
        WITH Agrupado AS (
            SELECT 
                tp_origem, g1,
                tp_uf,
                clAliqIcms,
                SUM(es_valcon) as valcon, 
                SUM(es_bcicms) as bcicms, 
                SUM(es_icms) as icms, 
                SUM(es_bcicmsst) as bcicmsst, 
                SUM(es_icmsst) as icmsst
            FROM item_db.item_base
            WHERE tp_codSit = 'válido'
            GROUP BY tp_origem, g1, tp_uf, clAliqIcms
        ),
        Ranked AS (
            SELECT 
                *,
                -- Cria um ranking de importância (por valor absoluto) DENTRO de cada grupo
                ROW_NUMBER() OVER(PARTITION BY tp_origem, g1 ORDER BY ABS(valcon) DESC) as rn
            FROM Agrupado
        )
        SELECT 
            tp_origem, g1, 
            CASE WHEN rn <= 6 THEN tp_uf ELSE 'Diversas' END AS tp_uf, 
            CASE WHEN rn <= 6 THEN clAliqIcms ELSE 'Outras' END AS clAliqIcms,
            ROUND(SUM(valcon), 2) as es_valcon, 
            ROUND(SUM(bcicms), 2) as es_bcicms, 
            ROUND(SUM(icms), 2) as es_icms, 
            ROUND(SUM(bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(icmsst), 2) as es_icmsst
        FROM Ranked
        GROUP BY 
            tp_origem, g1, 
            CASE WHEN rn <= 6 THEN tp_uf ELSE 'Diversas' END,
            CASE WHEN rn <= 6 THEN clAliqIcms ELSE 'Outras' END
        ORDER BY 
            tp_origem ASC, g1 ASC, 
            CASE WHEN rn > 6 THEN 1 ELSE 0 END ASC, -- Garante que a linha 'Outras' fique fixada no rodapé do grupo
            ABS(SUM(valcon)) DESC
    """, cursor, out_path, "Resumo por tp_origem, g1, Top 6 abs(es_valcon) + Outras (Apenas Documentos Válidos), com tp_uf e clAliqIcms")


    executar_e_formatar("""
        WITH Agrupado AS (
            SELECT 
                tp_origem, g1,
                tp_uf,
                clAliqIcms,
                redBCICMS, 
                SUM(es_valcon) as valcon, 
                SUM(es_bcicms) as bcicms, 
                SUM(es_icms) as icms, 
                SUM(es_bcicmsst) as bcicmsst, 
                SUM(es_icmsst) as icmsst
            FROM item_db.item_base
            WHERE tp_codSit = 'válido'
            GROUP BY tp_origem, g1, tp_uf, clAliqIcms, redBCICMS
        ),
        Ranked AS (
            SELECT 
                *,
                -- Cria um ranking de importância (por valor absoluto) DENTRO de cada grupo
                ROW_NUMBER() OVER(PARTITION BY tp_origem, g1 ORDER BY ABS(valcon) DESC) as rn
            FROM Agrupado
        )
        SELECT 
            tp_origem, g1, 
            CASE WHEN rn <= 6 THEN tp_uf ELSE 'Diversas' END AS tp_uf, 
            CASE WHEN rn <= 6 THEN clAliqIcms ELSE 'Diversas' END AS clAliqIcms,
            CASE WHEN rn <= 6 THEN redBCICMS ELSE 'Diversas' END AS redBCICMS,
            ROUND(SUM(valcon), 2) as es_valcon, 
            ROUND(SUM(bcicms), 2) as es_bcicms, 
            ROUND(SUM(icms), 2) as es_icms, 
            ROUND(SUM(bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(icmsst), 2) as es_icmsst
        FROM Ranked
        GROUP BY 
            tp_origem, g1, 
            CASE WHEN rn <= 6 THEN tp_uf ELSE 'Diversas' END,
            CASE WHEN rn <= 6 THEN clAliqIcms ELSE 'Diversas' END,
            CASE WHEN rn <= 6 THEN redBCICMS ELSE 'Diversas' END
        ORDER BY 
            tp_origem ASC, g1 ASC, 
            CASE WHEN rn > 6 THEN 1 ELSE 0 END ASC, -- Garante que a linha 'Outras' fique fixada no rodapé do grupo
            ABS(SUM(valcon)) DESC
    """, cursor, out_path, "Resumo por tp_origem, g1, Top 6 abs(es_valcon) + Outras (Apenas Documentos Válidos), com tp_uf, clAliqIcms e redBCICMS")


    executar_e_formatar("""
        WITH Agrupado AS (
            SELECT 
                tp_origem,
                COD_NCM,
                tp_uf,
                clAliqIcms,
                redBCICMS, 
                SUM(es_valcon) as valcon, 
                SUM(es_bcicms) as bcicms, 
                SUM(es_icms) as icms, 
                SUM(es_bcicmsst) as bcicmsst, 
                SUM(es_icmsst) as icmsst
            FROM item_db.item_base
            WHERE tp_codSit = 'válido' AND g1='1-Receitas'
            GROUP BY tp_origem, COD_NCM, tp_uf, clAliqIcms, redBCICMS
        ),
        Ranked AS (
            SELECT 
                *,
                -- Cria um ranking de importância (por valor absoluto) DENTRO de cada grupo
                ROW_NUMBER() OVER(PARTITION BY tp_origem ORDER BY ABS(valcon) DESC) as rn
            FROM Agrupado
        )
        SELECT 
            tp_origem,
            CASE WHEN rn <= 20 THEN COD_NCM ELSE 'Diversas' END AS COD_NCM, 
            CASE WHEN rn <= 20 THEN tp_uf ELSE 'Diversas' END AS tp_uf, 
            CASE WHEN rn <= 20 THEN clAliqIcms ELSE 'Diversas' END AS clAliqIcms,
            CASE WHEN rn <= 20 THEN redBCICMS ELSE 'Diversas' END AS redBCICMS,
            ROUND(SUM(valcon), 2) as es_valcon, 
            ROUND(SUM(bcicms), 2) as es_bcicms, 
            ROUND(SUM(icms), 2) as es_icms, 
            ROUND(SUM(bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(icmsst), 2) as es_icmsst
        FROM Ranked
        GROUP BY 
            tp_origem,
            CASE WHEN rn <= 20 THEN COD_NCM ELSE 'Diversas' END,
            CASE WHEN rn <= 20 THEN tp_uf ELSE 'Diversas' END,
            CASE WHEN rn <= 20 THEN clAliqIcms ELSE 'Diversas' END,
            CASE WHEN rn <= 20 THEN redBCICMS ELSE 'Diversas' END
        ORDER BY 
            tp_origem ASC, 
            CASE WHEN rn > 20 THEN 1 ELSE 0 END ASC, -- Garante que a linha 'Outras' fique fixada no rodapé do grupo
            ABS(SUM(valcon)) DESC
    """, cursor, out_path, "Resumo por tp_origem, Top 20 abs(es_valcon) + Outras (Apenas Documentos Válidos g1='1-Receitas'), com COD_NCM, tp_uf, clAliqIcms e redBCICMS")

    executar_e_formatar("""
        WITH Agrupado AS (
            SELECT 
                tp_origem,
                COD_NCM,
                tp_uf,
                clAliqIcms,
                redBCICMS, 
                SUM(es_valcon) as valcon, 
                SUM(es_bcicms) as bcicms, 
                SUM(es_icms) as icms, 
                SUM(es_bcicmsst) as bcicmsst, 
                SUM(es_icmsst) as icmsst
            FROM item_db.item_base
            WHERE tp_codSit = 'válido' AND g1='2-Compras Insumos'
            GROUP BY tp_origem, COD_NCM, tp_uf, clAliqIcms, redBCICMS
        ),
        Ranked AS (
            SELECT 
                *,
                -- Cria um ranking de importância (por valor absoluto) DENTRO de cada grupo
                ROW_NUMBER() OVER(PARTITION BY tp_origem ORDER BY ABS(valcon) DESC) as rn
            FROM Agrupado
        )
        SELECT 
            tp_origem,
            CASE WHEN rn <= 20 THEN COD_NCM ELSE 'Diversas' END AS COD_NCM, 
            CASE WHEN rn <= 20 THEN tp_uf ELSE 'Diversas' END AS tp_uf, 
            CASE WHEN rn <= 20 THEN clAliqIcms ELSE 'Diversas' END AS clAliqIcms,
            CASE WHEN rn <= 20 THEN redBCICMS ELSE 'Diversas' END AS redBCICMS,
            ROUND(SUM(valcon), 2) as es_valcon, 
            ROUND(SUM(bcicms), 2) as es_bcicms, 
            ROUND(SUM(icms), 2) as es_icms, 
            ROUND(SUM(bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(icmsst), 2) as es_icmsst
        FROM Ranked
        GROUP BY 
            tp_origem,
            CASE WHEN rn <= 20 THEN COD_NCM ELSE 'Diversas' END,
            CASE WHEN rn <= 20 THEN tp_uf ELSE 'Diversas' END,
            CASE WHEN rn <= 20 THEN clAliqIcms ELSE 'Diversas' END,
            CASE WHEN rn <= 20 THEN redBCICMS ELSE 'Diversas' END
        ORDER BY 
            tp_origem ASC, 
            CASE WHEN rn > 20 THEN 1 ELSE 0 END ASC, -- Garante que a linha 'Outras' fique fixada no rodapé do grupo
            ABS(SUM(valcon)) DESC
    """, cursor, out_path, "Resumo por tp_origem, Top 20 abs(es_valcon) + Outras (Apenas Documentos Válidos g1='2-Compras Insumos'), com COD_NCM, tp_uf, clAliqIcms e redBCICMS")


    executar_e_formatar("""
        WITH Agrupado AS (
            SELECT 
                tp_origem,
                idItemServicoDeclarado, BIdescricao,
                tp_uf,
                clAliqIcms,
                redBCICMS, 
                SUM(es_valcon) as valcon, 
                SUM(es_bcicms) as bcicms, 
                SUM(es_icms) as icms, 
                SUM(es_bcicmsst) as bcicmsst, 
                SUM(es_icmsst) as icmsst
            FROM item_db.item_base
            WHERE tp_codSit = 'válido' AND g1='1-Receitas'
            GROUP BY tp_origem, idItemServicoDeclarado, tp_uf, clAliqIcms, redBCICMS
        ),
        Ranked AS (
            SELECT 
                *,
                -- Cria um ranking de importância (por valor absoluto) DENTRO de cada grupo
                ROW_NUMBER() OVER(PARTITION BY tp_origem ORDER BY ABS(valcon) DESC) as rn
            FROM Agrupado
        )
        SELECT 
            tp_origem,
            CASE WHEN rn <= 30 THEN idItemServicoDeclarado ELSE 'Diversas' END AS idItemServicoDeclarado, 
            CASE WHEN rn <= 30 THEN BIdescricao ELSE 'Diversas' END AS BIdescricao,
            CASE WHEN rn <= 30 THEN tp_uf ELSE 'Diversas' END AS tp_uf, 
            CASE WHEN rn <= 30 THEN clAliqIcms ELSE 'Diversas' END AS clAliqIcms,
            CASE WHEN rn <= 30 THEN redBCICMS ELSE 'Diversas' END AS redBCICMS,
            ROUND(SUM(valcon), 2) as es_valcon, 
            ROUND(SUM(bcicms), 2) as es_bcicms, 
            ROUND(SUM(icms), 2) as es_icms, 
            ROUND(SUM(bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(icmsst), 2) as es_icmsst
        FROM Ranked
        GROUP BY 
            tp_origem,
            CASE WHEN rn <= 30 THEN idItemServicoDeclarado ELSE 'Diversas' END,
            CASE WHEN rn <= 30 THEN tp_uf ELSE 'Diversas' END,
            CASE WHEN rn <= 30 THEN clAliqIcms ELSE 'Diversas' END,
            CASE WHEN rn <= 30 THEN redBCICMS ELSE 'Diversas' END
        ORDER BY 
            tp_origem ASC, 
            CASE WHEN rn > 30 THEN 1 ELSE 0 END ASC, -- Garante que a linha 'Outras' fique fixada no rodapé do grupo
            ABS(SUM(valcon)) DESC
    """, cursor, out_path, "Resumo por tp_origem, Top 30 abs(es_valcon) + Outras (Apenas Documentos Válidos g1='1-Receitas'), com idItemServicoDeclarado, tp_uf, clAliqIcms e redBCICMS")


    executar_e_formatar("""
        WITH Agrupado AS (
            SELECT 
                tp_origem,
                idItemServicoDeclarado, BIdescricao,
                tp_uf,
                clAliqIcms,
                redBCICMS, 
                SUM(es_valcon) as valcon, 
                SUM(es_bcicms) as bcicms, 
                SUM(es_icms) as icms, 
                SUM(es_bcicmsst) as bcicmsst, 
                SUM(es_icmsst) as icmsst
            FROM item_db.item_base
            WHERE tp_codSit = 'válido' AND g1='2-Compras Insumos'
            GROUP BY tp_origem, idItemServicoDeclarado, tp_uf, clAliqIcms, redBCICMS
        ),
        Ranked AS (
            SELECT 
                *,
                -- Cria um ranking de importância (por valor absoluto) DENTRO de cada grupo
                ROW_NUMBER() OVER(PARTITION BY tp_origem ORDER BY ABS(valcon) DESC) as rn
            FROM Agrupado
        )
        SELECT 
            tp_origem,
            CASE WHEN rn <= 30 THEN idItemServicoDeclarado ELSE 'Diversas' END AS idItemServicoDeclarado, 
            CASE WHEN rn <= 30 THEN BIdescricao ELSE 'Diversas' END AS BIdescricao,
            CASE WHEN rn <= 30 THEN tp_uf ELSE 'Diversas' END AS tp_uf, 
            CASE WHEN rn <= 30 THEN clAliqIcms ELSE 'Diversas' END AS clAliqIcms,
            CASE WHEN rn <= 30 THEN redBCICMS ELSE 'Diversas' END AS redBCICMS,
            ROUND(SUM(valcon), 2) as es_valcon, 
            ROUND(SUM(bcicms), 2) as es_bcicms, 
            ROUND(SUM(icms), 2) as es_icms, 
            ROUND(SUM(bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(icmsst), 2) as es_icmsst
        FROM Ranked
        GROUP BY 
            tp_origem,
            CASE WHEN rn <= 30 THEN idItemServicoDeclarado ELSE 'Diversas' END,
            CASE WHEN rn <= 30 THEN tp_uf ELSE 'Diversas' END,
            CASE WHEN rn <= 30 THEN clAliqIcms ELSE 'Diversas' END,
            CASE WHEN rn <= 30 THEN redBCICMS ELSE 'Diversas' END
        ORDER BY 
            tp_origem ASC, 
            CASE WHEN rn > 30 THEN 1 ELSE 0 END ASC, -- Garante que a linha 'Outras' fique fixada no rodapé do grupo
            ABS(SUM(valcon)) DESC
    """, cursor, out_path, "Resumo por tp_origem, Top 30 abs(es_valcon) + Outras (Apenas Documentos Válidos g1='2-Compras Insumos'), com idItemServicoDeclarado, tp_uf, clAliqIcms e redBCICMS")

    # =========================================================================
    # --- EXPORTAÇÃO DOS ARQUIVOS FÍSICOS (.XLSX e .TXT) ---
    # =========================================================================
    if export_excel and export_tsv:
        dir_out = Path(out_path).parent # Pasta de destino baseada no parametro --dir
        
        # 1. Exportar XLSX (Amostra 10k)
        xlsx_path = dir_out / "item_base.xlsx"
        print(f" ➔ Exportando amostra para Excel (1.000 linhas) em {xlsx_path.name}...")
        cursor.execute("SELECT * FROM item_db.item_base LIMIT 1000")
        linhas_xlsx = export_excel(cursor, xlsx_path)
        print(f"    [OK] {linhas_xlsx} linhas exportadas.")

        # 2. Exportar TXT Completo
        txt_path = dir_out / "item_base.txt"
        print(f" ➔ Na versão anterior, era exportado base completa para TXT (separado por tabulação) em {txt_path.name}...")
        print(f"    [OK] Agora não faço mais isso, eu simplesmente deixo um sqlite pronto em {dir_out}/item_base.sqlite com a tabela item_base...")
        # cursor.execute("SELECT * FROM _tmp_item_base")
        # linhas_txt = export_tsv(cursor, txt_path)
        # print(f"    [OK] {linhas_txt} linhas exportadas.")

    # Não é estritamente necessário dar DROP pois o SQLite limpa ao fechar, 
    # mas é boa prática para libertar o ficheiro temporário de sistema o quanto antes.
    # cursor.execute("DROP TABLE IF EXISTS temp._tmp_item_base;")