"""
Relatório Operações
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

def gerar_rel_oper(cursor, out_path, debug=False):

    iniciar_relatorio(out_path, "Relatório de Operações", debug=debug)

    # Define o caminho do novo banco de dados analítico na pasta --dir
    dir_out = Path(out_path).parent
    db_oper_path = dir_out / "oper_base.sqlite"
    
    print(" ➔ Criando visualização temporária no disco...")

    # Anexa o novo banco de dados (se o arquivo não existir, o SQLite cria na hora)
    cursor.execute(f"ATTACH DATABASE '{db_oper_path}' AS oper_db;")
    
    # Limpa a tabela caso o auditor esteja rodando o script pela segunda vez na mesma pasta
    cursor.execute("DROP TABLE IF EXISTS oper_db.oper_base;")

    # Cria a tabela diretamente dentro do novo arquivo .sqlite!
    cursor.execute("""
        CREATE TABLE oper_db.oper_base AS
        SELECT  EI.cfop AS cfopcv,
          CASE WHEN EI.cfop < 5000 THEN -AA.valorDaOperacao ELSE AA.valorDaOperacao END AS es_valcon,
          -- Classes de BC ICMS reduzidas
          CASE 
            WHEN AA.valorDaOperacao = 0 THEN 'ValCon=0'
            WHEN AA.bcIcmsOpPropria = 0 THEN 'BCIcms=0'
            WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) > 1 THEN '>100'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) > 0.995 THEN 'BCIcms=ValCon'
			WHEN ((AA.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) > 0.995 THEN 'BCIcms=ValConSemIpi'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) BETWEEN 0.222 AND 0.223 THEN 'BCIcms(4%)=ValCon'
			WHEN ((AA.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) BETWEEN 0.222 AND 0.223 THEN 'BCIcms(4%)=ValConSemIpi'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) BETWEEN 0.388 AND 0.389 THEN 'BCIcms(7%)=ValCon'
			WHEN ((AA.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) BETWEEN 0.388 AND 0.389 THEN 'BCIcms(7%)=ValConSemIpi'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) BETWEEN 0.666 AND 0.667 THEN 'BCIcms(12%)=ValCon'
			WHEN ((AA.bcIcmsOpPropria + DA_T.VL_IPI) / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) BETWEEN 0.666 AND 0.667 THEN 'BCIcms(12%)=ValConSemIpi'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.90 THEN '90>99'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.80 THEN '80>89'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.70 THEN '70>79'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.60 THEN '60>69'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.50 THEN '50>59'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.40 THEN '40>49'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.30 THEN '30>39'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.20 THEN '20>29'
			WHEN (AA.bcIcmsOpPropria / NULLIF(AA.valorDaOperacao - AA.icmsSt, 0)) >= 0.10 THEN '10>19'
			ELSE '<10' 
          END AS redBCICMS,
          CASE WHEN EI.cfop < 5000 THEN -AA.bcIcmsOpPropria ELSE AA.bcIcmsOpPropria END AS es_bcicms,
          -- Classes de tipos de UFs e suas alíquotas típicas
          CASE 
		    WHEN DA_T.uf IN ('MG', 'PR', 'RJ', 'SC', 'RS') THEN 'UF12'
		    WHEN DA_T.uf IN ('ES', 'MS', 'MT', 'GO', 'DF', 'BA', 'AL', 'SE', 'PE', 'PB', 'RN', 'CE', 'PI', 'MA', 'TO', 'PA', 'AM', 'AP', 'RR', 'RO', 'AC') THEN 'UF7'
		    ELSE DA_T.uf
		  END AS tp_uf,
		  -- Classes de Alíquota ICMS Proprio
          CASE 
            WHEN AA.icmsProprio = 0 OR AA.bcIcmsOpPropria = 0 THEN '0'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.011 THEN '<1'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.021 THEN '1<2'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.039 THEN '2<4'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.041 THEN '4'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.069 THEN '4<7'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.071 THEN '7'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.119 THEN '7<12'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.121 THEN '12'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.132 THEN '12<13,3'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.134 THEN '13,3'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.179 THEN '13,3<18'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.181 THEN '18'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.249 THEN '18<25'
            WHEN (AA.icmsProprio / NULLIF(AA.bcIcmsOpPropria, 0)) < 0.251 THEN '25'
            ELSE '>25'
          END AS clAliqIcms,
          CASE WHEN EI.cfop < 5000 THEN -AA.icmsProprio ELSE AA.icmsProprio END AS es_icms,
          CASE 
            WHEN AA.bcIcmsOpPropria = 0 OR AA.bcIcmsSt = 0 THEN 0
            ELSE round(AA.bcIcmsSt / bcIcmsOpPropria * 100, 0)
          END AS IvaSt,
          CASE WHEN EI.cfop < 5000 THEN -AA.bcIcmsSt ELSE AA.bcIcmsSt END AS es_bcicmsst,
          -- Classes de Alíquota ICMS ST
          CASE 
            WHEN AA.icmsSt = 0 OR AA.bcIcmsSt = 0 THEN '0'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.011 THEN '<1'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.039 THEN '1<4'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.041 THEN '4'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.069 THEN '4<7'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.071 THEN '7'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.119 THEN '7<12'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.121 THEN '12'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.132 THEN '12<13,3'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.134 THEN '13,3'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.179 THEN '13,3<18'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.181 THEN '18'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 0)) < 0.249 THEN '18<25'
            WHEN (AA.icmsSt / NULLIF(AA.bcIcmsSt, 00)) < 0.251 THEN '25'
            ELSE '>25'
          END AS clAliqIcmsSt,
          CASE WHEN EI.cfop < 5000 THEN -AA.icmsSt ELSE AA.icmsSt END AS es_icmsst,
          EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif,
        '[DocAtrib_fiscal_DocAtributosDeApuracao]' AS tAA,
        AA.referencia, AA.cstCsosnIcms, AA.indCstCsosn, AA.indOrigem, AA.cfop AS AAcfop, AA.aliqIcms AS aliqIcms,
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
        FROM  DocAtrib_fiscal_DocAtributosDeApuracao AS AA
        LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AA.idDocAtributos
        LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN docAtribTudao AS DA_T ON DA_T.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN ChaveNroTudao AS Z ON Z.chave = DA_T.chave
        LEFT OUTER JOIN cfopEntSai AS CES ON CES.cfop_dfe = CAST(AA.cfop AS INT)
        LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN CES.cfop_efd ELSE CAST(AA.cfop AS INT) END
    """)

    # 3. Geração dos Relatórios (Leitura direta e instantânea da tabela temporária)
    executar_e_formatar("""
        SELECT * FROM oper_db.oper_base LIMIT 2
    """, cursor, out_path, "Amostra das Operações (Top 2)")

    executar_e_formatar("""
        SELECT 
            tp_origem, tp_oper, tp_codSit, 
            ROUND(SUM(es_valcon), 2) as es_valcon, 
            ROUND(SUM(es_bcicms), 2) as es_bcicms, 
            ROUND(SUM(es_icms), 2) as es_icms, 
            ROUND(SUM(es_bcicmsst), 2) as es_bcicmsst, 
            ROUND(SUM(es_icmsst), 2) as es_icmsst
        FROM oper_db.oper_base
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
        FROM oper_db.oper_base
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
            FROM oper_db.oper_base
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
            FROM oper_db.oper_base
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

    # =========================================================================
    # --- EXPORTAÇÃO DOS ARQUIVOS FÍSICOS (.XLSX e .TXT) ---
    # =========================================================================
    if export_excel and export_tsv:
        dir_out = Path(out_path).parent # Pasta de destino baseada no parametro --dir
        
        # 1. Exportar XLSX (Amostra 10k)
        xlsx_path = dir_out / "oper_base.xlsx"
        print(f" ➔ Exportando amostra para Excel (1.000 linhas) em {xlsx_path.name}...")
        cursor.execute("SELECT * FROM oper_db.oper_base LIMIT 1000")
        linhas_xlsx = export_excel(cursor, xlsx_path)
        print(f"    [OK] {linhas_xlsx} linhas exportadas.")

        # 2. Exportar TXT Completo
        txt_path = dir_out / "oper_base.txt"
        print(f" ➔ Na versão anterior, era exportado base completa para TXT (separado por tabulação) em {txt_path.name}...")
        print(f"    [OK] Agora não faço mais isso, eu simplesmente deixo um sqlite pronto em {dir_out}/oper_base.sqlite com a tabela oper_base...")
        # cursor.execute("SELECT * FROM oper_db.oper_base")
        # linhas_txt = export_tsv(cursor, txt_path)
        # print(f"    [OK] {linhas_txt} linhas exportadas.")

    # Não é estritamente necessário dar DROP pois o SQLite limpa ao fechar, 
    # mas é boa prática para libertar o ficheiro temporário de sistema o quanto antes.
    # cursor.execute("DROP TABLE IF EXISTS temp._tmp_oper_base;")