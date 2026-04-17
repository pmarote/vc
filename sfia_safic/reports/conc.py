"""
Relatório de Conciliação — DocAtributos, NFe, CTe, SAT.
"""
from ._helpers import executar_e_formatar, iniciar_relatorio


def gerar_rel_conc(cursor, out_path, limite=5, debug=False):
    iniciar_relatorio(out_path, "Relatórios de Conciliação", debug=debug)

    executar_e_formatar("""
        SELECT
           CASE WHEN    (abs(round(sum(SqA.vl_docDFe) - sum(SqA.vl_docEFD), 2)) > 1000 OR
                        abs(round(sum(SqA.vl_icmsDFe) - sum(SqA.vl_icmsEFD), 2)) > 100 OR
                        abs(round(sum(SqA.vl_icmsstSP_DFe) - sum(SqA.vl_icmsstSP_EFD), 2)) > 100)
                        AND SqA.tp_codSit = 'válido' AND SqA.indEmit = 0
           THEN '##DIF##' ELSE '' END AS status,
           SqA.tp_codSit, SqA.tp_oper, SqA.indEmit, SqA.indOper, count(SqA.tp_codSit) AS qtd,
           round(sum(SqA.vl_docDFe) - sum(SqA.vl_docEFD), 2) AS dif_docEFD, round(sum(SqA.vl_icmsDFe) - sum(SqA.vl_icmsEFD), 2) AS dif_icmsEFD,
           round(sum(SqA.vl_icmsstSP_DFe) - sum(SqA.vl_icmsstSP_EFD), 2) AS dif_icmsstSP_EFD, sum(SqA.vl_docDFe) AS vl_docDFe, sum(SqA.vl_docEFD) AS vl_docEFD,
           sum(SqA.vl_icmsDFe) AS vl_icmsDFe, sum(SqA.vl_icmsEFD) AS vl_icmsEFD, sum(SqA.vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(SqA.vl_icmsstSP_EFD) AS vl_icmsstSP_EFD,
           sum(SqA.vl_icmsstUFs_DFe) AS vl_icmsstUFs_DFe, sum(SqA.vl_icmsstUFs_EFD) AS vl_icmsstUFs_EFD
           FROM
        (SELECT
          Compl.tp_codSit, A.indEmit, A.indOper, B.tp_origem,
          CASE WHEN A.indEmit = 0 THEN CASE WHEN A.indOper = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN A.indOper = 0 THEN 'ET' ELSE 'D' END END AS tp_oper,
          CASE WHEN B.tp_origem = 'DFe' THEN A.vlTotalDoc ELSE 0 END AS vl_docDFe, CASE WHEN B.tp_origem = 'EFD' THEN A.vlTotalDoc ELSE 0 END AS vl_docEFD,
          CASE WHEN B.tp_origem = 'DFe' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsDFe, CASE WHEN B.tp_origem = 'EFD' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsEFD,
          CASE WHEN B.tp_origem = 'DFe' AND Compl.uf = 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstSP_DFe, CASE WHEN B.tp_origem = 'EFD' AND Compl.uf = 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstSP_EFD,
          CASE WHEN B.tp_origem = 'DFe' AND Compl.uf <> 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstUFs_DFe, CASE WHEN B.tp_origem = 'EFD' AND Compl.uf <> 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstUFs_EFD
          FROM DocAtrib_fiscal_DocAtributos AS A LEFT OUTER JOIN idDocAtributos_compl AS Compl ON Compl.idDocAtributos = A.idDocAtributos LEFT OUTER JOIN regOrig AS B ON B.idRegistroDeOrigem = A.idRegistroDeOrigem
        UNION ALL
        SELECT
          Compl.tp_codSit, A.indEmit, A.indOper, B.tp_origem, CASE WHEN A.indOper = 0 THEN '_SEMREF_ET' ELSE '_SEMREF_D' END AS tp_oper,
          CASE WHEN B.tp_origem = 'DFe' THEN A.vlTotalDoc ELSE 0 END AS vl_docDFe, CASE WHEN B.tp_origem = 'EFD' THEN A.vlTotalDoc ELSE 0 END AS vl_docEFD,
          CASE WHEN B.tp_origem = 'DFe' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsDFe, CASE WHEN B.tp_origem = 'EFD' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsEFD,
          CASE WHEN B.tp_origem = 'DFe' AND Compl.uf = 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstSP_DFe, CASE WHEN B.tp_origem = 'EFD' AND Compl.uf = 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstSP_EFD,
          CASE WHEN B.tp_origem = 'DFe' AND Compl.uf <> 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstUFs_DFe, CASE WHEN B.tp_origem = 'EFD' AND Compl.uf <> 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstUFs_EFD
          FROM DocAtrib_fiscal_DocAtributos AS A LEFT OUTER JOIN idDocAtributos_compl AS Compl ON Compl.idDocAtributos = A.idDocAtributos LEFT OUTER JOIN regOrig AS B ON B.idRegistroDeOrigem = A.idRegistroDeOrigem
          WHERE Compl.tp_codSit = 'válido' AND A.indEmit = 1 AND A.referencia = '0001-01-01'
        UNION ALL
        SELECT
          Compl.tp_codSit, A.indEmit, A.indOper, B.tp_origem, CASE WHEN A.indOper = 0 THEN '_REF_ET' ELSE '_REF_D' END AS tp_oper,
          CASE WHEN B.tp_origem = 'DFe' THEN A.vlTotalDoc ELSE 0 END AS vl_docDFe, CASE WHEN B.tp_origem = 'EFD' THEN A.vlTotalDoc ELSE 0 END AS vl_docEFD,
          CASE WHEN B.tp_origem = 'DFe' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsDFe, CASE WHEN B.tp_origem = 'EFD' THEN A.vlIcmsProprio ELSE 0 END AS vl_icmsEFD,
          CASE WHEN B.tp_origem = 'DFe' AND Compl.uf = 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstSP_DFe, CASE WHEN B.tp_origem = 'EFD' AND Compl.uf = 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstSP_EFD,
          CASE WHEN B.tp_origem = 'DFe' AND Compl.uf <> 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstUFs_DFe, CASE WHEN B.tp_origem = 'EFD' AND Compl.uf <> 'SP' THEN A.vlIcmsSt ELSE 0 END AS vl_icmsstUFs_EFD
          FROM DocAtrib_fiscal_DocAtributos AS A LEFT OUTER JOIN idDocAtributos_compl AS Compl ON Compl.idDocAtributos = A.idDocAtributos LEFT OUTER JOIN regOrig AS B ON B.idRegistroDeOrigem = A.idRegistroDeOrigem
          WHERE Compl.tp_codSit = 'válido' AND A.indEmit = 1 AND A.referencia <> '0001-01-01'
        ) AS SqA GROUP BY SqA.tp_codSit, SqA.tp_oper;
    """, cursor, out_path, "DocAtributos_Conc")

    executar_e_formatar(f"""
        SELECT
          '[EfdNfe]' AS tA, A.*, '[EfdC100]' AS tB, B.idEfdC100 AS B_idEfdC100,
            CASE WHEN B.COD_SIT IN (2, 3, 4, 5) THEN CAST(B.COD_SIT AS VARCHAR) ELSE '<>2-3-4-5' END AS Efd_COD_SIT,
            CASE WHEN B.IND_EMIT = 0 THEN CASE WHEN B.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN B.IND_OPER = 0 THEN 'ET' ELSE 'D' END END AS Efd_TP_OPER,
            B.NUM_DOC AS B_NUM_DOC, B.CHV_NFE AS B_CHV_NFE, B.DT_DOC AS B_DT_DOC, B.VL_DOC AS Efd_VL_DOC, B.VL_ICMS AS Efd_VL_ICMS, B.VL_ICMS_ST AS Efd_VL_ICMS_ST,
          '[NfeC100]' AS tC, C.idNFeC100 AS C_idNFeC100,
            CASE WHEN C.COD_SIT IN (2, 3, 4, 5) THEN CAST(C.COD_SIT AS VARCHAR) ELSE '<>2-3-4-5' END AS Nfe_COD_SIT,
            CASE WHEN C.IND_EMIT = 0 THEN CASE WHEN C.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN C.IND_OPER = 1 THEN 'ET' ELSE 'D' END END AS Nfe_TP_OPER,
            C.NUM_DOC AS C_NUM_DOC, C.CHV_NFE AS C_CHV_NFE, C.DT_DOC AS C_DT_DOC, C.VL_DOC AS Nfe_VL_DOC, C.VL_ICMS AS Nfe_VL_ICMS, C.VL_ICMS_ST AS Nfe_VL_ICMS_ST
        FROM _fiscal_EfdNfe AS A LEFT OUTER JOIN dfe_fiscal_EfdC100 AS B ON B.idEfdC100 = A.idEfdC100 LEFT OUTER JOIN dfe_fiscal_NfeC100 AS C ON C.idNfeC100 = A.idNfeC100 LIMIT {limite}
    """, cursor, out_path, f"ConciliacaoEfdNFe - Conciliação do Safic (amostra com LIMIT = {limite})")

    executar_e_formatar(f"""
        SELECT
          '[EfdCte]' AS tA, A.*, '[EfdD100]' AS tB, B.idEfdD100,
            CASE WHEN B.COD_SIT IN (2, 3, 4, 5) THEN CAST(B.COD_SIT AS VARCHAR) ELSE '<>2-3-4-5' END AS Efd_COD_SIT,
            CASE WHEN B.IND_EMIT = 0 THEN CASE WHEN B.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN B.IND_OPER = 0 THEN 'ET' ELSE 'D' END END AS Efd_TP_OPER,
            B.NUM_DOC AS B_NUM_DOC, B.CHV_CTE AS B_CHV_CTE, B.DT_DOC AS B_DT_DOC, B.VL_DOC AS Efd_VL_DOC, B.VL_ICMS AS Efd_VL_ICMS,
          '[NfeC200]' AS tC, C.idNFeC200,
            CASE WHEN C.codSit IN (2, 3, 4, 5) THEN CAST(C.codSit AS VARCHAR) ELSE '<>2-3-4-5' END AS Cte_COD_SIT,
            CASE WHEN C.indEmit = 0 THEN CASE WHEN C.indOper = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN C.indOper = 1 THEN 'ET' ELSE 'D' END END AS Cte_TP_OPER,
            C.nCT AS C_nCT, C.Id AS C_Id, C.dhEmi AS C_dhEmi, I.vTPrest AS Cte_vTPrest, CAST(K.vICMS AS REAL) AS Cte_vICMS
        FROM _fiscal_EfdCte AS A LEFT OUTER JOIN dfe_fiscal_EfdD100 AS B ON B.idEfdD100 = A.idEfdD100 LEFT OUTER JOIN dfe_fiscal_NfeC200 AS C ON C.idNfeC200 = A.idNfeC200 LEFT OUTER JOIN dfe_fiscal_NfeC209 AS I ON I.idNfeC200 = A.idNfeC200 LEFT OUTER JOIN dfe_fiscal_NfeC211 AS K ON K.idNfeC200 = A.idNfeC200 LIMIT {limite}
    """, cursor, out_path, f"ConciliacaoEfdCTe (amostra com LIMIT = {limite})")

    executar_e_formatar(f"""
        SELECT '[EfdSat]' AS tA, A.*, '[EfdC800]' AS tB, B.*, '[Sat100]' AS tC1, C1.*, '[Sat100]' AS tC2, C2.*
        FROM _fiscal_EfdSat AS A LEFT OUTER JOIN dfe_fiscal_EfdC800 AS B ON B.idEfdC800 = A.idEfdC800 LEFT OUTER JOIN dfe_fiscal_Sat100 AS C1 ON C1.idSat100 = A.idSat100 LEFT OUTER JOIN dfe_fiscal_Sat104 AS C2 ON C2.idSat100 = A.idSat100 LIMIT {limite}
    """, cursor, out_path, f"ConciliacaoEfdSat (amostra com LIMIT = {limite})")
