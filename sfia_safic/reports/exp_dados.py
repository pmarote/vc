"""
Relatório de Exportação de Dados — amostras de tabelas e views úteis.
"""
from ._helpers import executar_e_formatar, iniciar_relatorio


def gerar_rel_exp_dados(cursor, out_path, limite=2):
    iniciar_relatorio(out_path, "Amostras de Exportações de Dados Úteis")

    executar_e_formatar(f"SELECT * FROM chaveNroTudao LIMIT {limite}", cursor, out_path, "Tabela sia.chaveNroTudao")

    executar_e_formatar(f"""
        SELECT '[DocAtrib_fiscal_DocAtributos]' AS tA, A.*, '[idDocAtributos_compl]' AS tB, B.*, '[docAtribTudao]' AS tDA_T, DA_T.*
        FROM DocAtrib_fiscal_DocAtributos AS A LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos LEFT OUTER JOIN docAtribTudao AS DA_T ON DA_T.idDocAtributos = A.idDocAtributos LIMIT {limite}
    """, cursor, out_path, "Tabela DocAtributos_e_compls")

    executar_e_formatar(f"""
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
        LIMIT {limite}
    """, cursor, out_path, "Tabela DocAtributosDeApuracao_e_compls")

    executar_e_formatar(f"""
        SELECT  EI.cfop AS cfopcv,
          CASE WHEN EI.cfop < 5000 THEN -AI.valorDaOperacao ELSE AI.valorDaOperacao END AS es_valcon,
          CASE WHEN EI.cfop < 5000 THEN -AI.bcIcmsOpPropria ELSE AI.bcIcmsOpPropria END AS es_bcicms,
          CASE WHEN EI.cfop < 5000 THEN -AI.icmsProprio ELSE AI.icmsProprio END AS es_icms,
          CASE WHEN EI.cfop < 5000 THEN -AI.bcIcmsSt ELSE AI.bcIcmsSt END AS es_bcicmsst,
          CASE WHEN EI.cfop < 5000 THEN -AI.icmsSt ELSE AI.icmsSt END AS es_icmsst,
          EI.dfi, EI.st, EI.classe, EI.g1, EI.c3, EI.g2, EI.g3, EI.descri_simplif,
        '[DocAtrib_fiscal_DocAtributosItem]' AS tAI, AI.*, '[_fiscal_ItemServicoDeclarado]' AS tBI, BI.*,
        CASE WHEN B.origem = 'EfdC100' THEN I.NUM_ITEM ELSE H.NUM_ITEM END AS NUM_ITEM,
        CASE WHEN B.origem = 'EfdC100' THEN 'Usar dados dfe_fiscal_EfdC170' ELSE 'Usar dados dfe_fiscal_NfeC170' END AS FONTE,
        '[dfe_fiscal_EfdC170]' AS tI, I.*, '[dfe_fiscal_NfeC170]' AS tH, H.*, '[DocAtrib_fiscal_DocAtributos]' AS tA, A.*, '[idDocAtributos_compl]' AS tB, B.*, '[docAtribTudao]' AS tDA_T, DA_T.*
        FROM  DocAtrib_fiscal_DocAtributosItem AS AI
        LEFT OUTER JOIN _fiscal_ItemServicoDeclarado AS BI ON BI.idItemServicoDeclarado = AI.idItemServicoDeclarado
        LEFT OUTER JOIN DocAtrib_fiscal_DocAtributos AS A ON A.idDocAtributos = AI.idDocAtributos
        LEFT OUTER JOIN idDocAtributos_compl AS B ON B.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN docAtribTudao AS DA_T ON DA_T.idDocAtributos = A.idDocAtributos
        LEFT OUTER JOIN dfe_fiscal_EfdC170 AS I ON I.idEfdC170 = AI.idRegistroItem AND A.indEmit = 1 AND B.origem = 'EfdC100'
        LEFT OUTER JOIN dfe_fiscal_NfeC170 AS H ON H.idNfeC170 = AI.idRegistroItem AND B.origem = 'NFe'
        LEFT OUTER JOIN cfopEntSai AS CES ON CES.cfop_dfe = CAST(AI.cfop AS INT)
        LEFT OUTER JOIN cfopd AS EI ON EI.cfop = CASE WHEN B.tp_origem = 'DFe' AND A.indEmit = 1 THEN CES.cfop_efd ELSE CAST(AI.cfop AS INT) END
        LIMIT {limite}
    """, cursor, out_path, "Tabela DocAtributosItem_e_compls")

    executar_e_formatar(f"""
        SELECT '[NfeC100]' AS tA, A.CHV_NFE,
          CASE WHEN A.IND_EMIT = 0 THEN CASE WHEN A.IND_OPER = 0 THEN 'EP' ELSE 'S' END ELSE CASE WHEN A.IND_OPER = 1 THEN 'ET' ELSE 'D' END END AS tp_oper,
          CASE WHEN A.COD_SIT = 2 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 3 THEN 'cancelado' ELSE CASE WHEN A.COD_SIT = 4 THEN 'denegado' ELSE CASE WHEN A.COD_SIT = 5 THEN 'inutilizado' ELSE 'válido' END END END END AS tp_codSit,
        '[chaveNroTudao]' AS tZ, Z.*, '[NfeC170]' AS tB, B.*, '[NfeC170InfProd]' AS tC, C.*, '[NfeC170IpiNaoTrib]' AS tD, D.*, '[NfeC170IpiTrib]' AS tE, E.*, '[NfeC170Resumo]' AS tF, F.*,
        '[NfeC170Tributos]' AS tG, G.*, '[NfeC176]' AS tH, H.*, '[NfeC182]' AS tI, I.*, '[NfeC183]' AS tJ, J.*
           FROM dfe_fiscal_NfeC170 AS B
           LEFT OUTER JOIN dfe_fiscal_NfeC100 AS A ON A.idNfeC100 = B.idNfeC100
           LEFT OUTER JOIN main.ChaveNroTudao AS Z ON Z.chave = A.CHV_NFE
           LEFT OUTER JOIN dfe_fiscal_NfeC101 AS C101 ON C101.idNfeC100 = A.idNfeC100
           LEFT OUTER JOIN dfe_fiscal_NfeC102 AS D102 ON D102.idNfeC100 = A.idNfeC100
           LEFT OUTER JOIN dfe_fiscal_NfeC170InfProd AS C ON C.idNFeC170 = B.idNFeC170
           LEFT OUTER JOIN dfe_fiscal_NfeC170IpiNaoTrib AS D ON D.idNFeC170 = B.idNFeC170
           LEFT OUTER JOIN dfe_fiscal_NfeC170IpiTrib AS E ON E.idNFeC170 = B.idNFeC170
           LEFT OUTER JOIN dfe_fiscal_NfeC170Resumo AS F ON F.idNFeC170 = B.idNFeC170
           LEFT OUTER JOIN dfe_fiscal_NfeC170Tributos AS G ON G.idNFeC170 = B.idNFeC170
           LEFT OUTER JOIN dfe_fiscal_NfeC176 AS H ON H.idNFeC170 = B.idNFeC170
           LEFT OUTER JOIN dfe_fiscal_NfeC182 AS I ON I.idNFeC170 = B.idNFeC170
           LEFT OUTER JOIN dfe_fiscal_NfeC183 AS J ON J.idNFeC182 = I.idNFeC182 LIMIT {limite}
    """, cursor, out_path, "Tabela Tudo de NFes Itens NFeC170 e subtabelas, correlacionando ChaveNroTudao")

    tabelas_views = [
        ("NfeC100_NfeC100Detalhe_NfeC101_NfeC102_NfeC110_NfeC112_NfeC115_NfeC116_NfeC127_NfeC130_NfeC140", "View osf.NfeC100_NfeC100Detalhe..."),
        ("NfeC100_PodeDuplicar_NfeC100Detalhe_NfeC101_NfeC102_NfeC103_NfeC104_NfeC106_NfeC110_NfeC112_NfeC115_NfeC116_NfeC119_NfeC127_NfeC130_NfeC140_NfeC141_NfeC160", "View osf.NfeC100_PodeDuplicar..."),
        ("NFes_Itens_C100_C170_C176_C182_C183", "View osf.NFes_Itens_C100_C170_C176_C182_C183"),
        ("Evt100_e_subeventos", "View osf.Evt100_e_subeventos"),
        ("Evt189_NFeReferenciada", "View osf.Evt189_NFeReferenciada"),
        ("Evt190_ZFM", "View osf.Evt190_ZFM"),
        ("Evt191_192_EFD_Part", "View osf.Evt191_192_EFD_Part"),
        ("CTes_PodeDuplicar_NFeC200_e_demais", "View osf.CTes_PodeDuplicar_NFeC200_e_demais"),
        ("Efd0200_Efd0205_ItemServicoDeclarado", "View osf.Efd0200_Efd0205_ItemServicoDeclarado"),
        ("EfdC100_EfdC100Detalhe_Efd0150", "View osf.EfdC100_EfdC100Detalhe_Efd0150"),
        ("EfdC100_EfdC100Detalhe_Efd0150_EfdC110_EfdC190_EfdC195_EfdC197", "View osf.EfdC100_EfdC100Detalhe_Efd0150_EfdC110..."),
        ("EfdC100_EfdC100Detalhe_Efd0150_EfdC190", "View osf.EfdC100_EfdC100Detalhe_Efd0150_EfdC190"),
        ("EfdC170_Efd0200_Efd0190_EfdC100_EfdC100Detalhe_Efd0150", "View osf.EfdC170_Efd0200_Efd0190_EfdC100_EfdC100Detalhe_Efd0150"),
        ("EfdD100_EfdD100Detalhe_EfdD190", "View osf.EfdD100_EfdD100Detalhe_EfdD190"),
        ("EfdE110_EfdE111_EfdE111Descr_EfdE112_EfdE112Descr_EfdE113_EfdE115_EfdE115Descr_EfdE116_EfdE116Descr", "View osf.EfdE110..."),
        ("EfdG110_EfdG125_EfdG126", "View osf.EfdG110_EfdG125_EfdG126"),
        ("EfdG110_EfdG125_EfdG126_EfdG130_EfdG140", "View osf.EfdG110_EfdG125_EfdG126_EfdG130_EfdG140"),
        ("EfdH010_ItemServicoDeclarado_EfdH005_EfdH010Descr_EfdH010Posse_EfdH010Prop", "View osf.EfdH010_ItemServicoDeclarado..."),
    ]

    for tabela, titulo in tabelas_views:
        executar_e_formatar(f"SELECT * FROM {tabela} LIMIT {limite}", cursor, out_path, titulo)
