"""
Relatório Safic Menu — resumo por classificação (idClassificacao).
"""
from ._helpers import executar_e_formatar, iniciar_relatorio


def gerar_rel_safic_menu(cursor, out_path):
    iniciar_relatorio(out_path, "Análises do Safic")
    where = "1 = 1"

    executar_e_formatar(f"""
        WITH DadosBase AS (
            SELECT A.idClassificacao, B.vlTotalDoc, B.vlIcmsProprio, B.vlIcmsSt
            FROM docatrib_fiscal_DocClassificado AS A
            LEFT JOIN docatrib_fiscal_DocAtributos AS B ON B.idDocAtributos = A.idDocAtributos
        ),
        CalculoPorMenu AS (
            SELECT DB.idClassificacao,
                CASE
                    WHEN length(PCD.descricao) <= 60 THEN PCD.descricao
                    WHEN length(PCD.descricao) <= 120 THEN substr(PCD.descricao, 1, 60)  || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 61)
                    WHEN length(PCD.descricao) <= 180 THEN substr(PCD.descricao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 121)
                    WHEN length(PCD.descricao) <= 240 THEN substr(PCD.descricao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 121, 60) || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 181)
                    ELSE substr(PCD.descricao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 121, 60) || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 181, 60) || '<br>&nbsp;&nbsp;' || substr(PCD.descricao, 241)
                END AS descMenu,
                CASE
                    WHEN length(C.descricao) <= 60 THEN C.descricao
                    WHEN length(C.descricao) <= 120 THEN substr(C.descricao, 1, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descricao, 61)
                    WHEN length(C.descricao) <= 180 THEN substr(C.descricao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(C.descricao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descricao, 121)
                    WHEN length(C.descricao) <= 240 THEN substr(C.descricao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(C.descricao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descricao, 121, 60) || '<br>&nbsp;&nbsp;' || substr(C.descricao, 181)
                    ELSE substr(C.descricao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(C.descricao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descricao, 121, 60) || '<br>&nbsp;&nbsp;' || substr(C.descricao, 181, 60) || '<br>&nbsp;&nbsp;' || substr(C.descricao, 241)
                END AS descricao,
                CASE
                    WHEN length(C.descrParaAgregacao) <= 60 THEN C.descrParaAgregacao
                    WHEN length(C.descrParaAgregacao) <= 120 THEN substr(C.descrParaAgregacao, 1, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 61)
                    WHEN length(C.descrParaAgregacao) <= 180 THEN substr(C.descrParaAgregacao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 121)
                    WHEN length(C.descrParaAgregacao) <= 240 THEN substr(C.descrParaAgregacao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 121, 60) || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 181)
                    ELSE substr(C.descrParaAgregacao, 1, 60)   || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 61, 60)  || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 121, 60) || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 181, 60) || '<br>&nbsp;&nbsp;' || substr(C.descrParaAgregacao, 241)
                END AS descrParaAgregacao,
                COUNT(DB.idClassificacao)   AS qtdidClassificacao, SUM(DB.vlTotalDoc) AS vlTotalDoc, SUM(DB.vlIcmsProprio) AS vlIcmsProprio, SUM(DB.vlIcmsSt) AS vlIcmsSt
            FROM DadosBase AS DB
            LEFT JOIN _fiscal_Classificacao AS C ON C.idClassificacao = DB.idClassificacao
            LEFT JOIN _fiscal_ParamConsultaDocClassificacao AS PCDC ON PCDC.idClassificacao = DB.idClassificacao
            LEFT JOIN _fiscal_ParamConsultaDoc AS PCD ON PCD.idParamConsultaDoc = PCDC.idParamConsultaDoc
            WHERE {where} GROUP BY DB.idClassificacao, PCD.descricao
        )
        SELECT idClassificacao AS IdClassif, group_concat(descMenu, ' <br> ') AS itens_menu, descricao, descrParaAgregacao, qtdidClassificacao AS qtd, vlTotalDoc, vlIcmsProprio AS vlIcms, vlIcmsSt FROM CalculoPorMenu GROUP BY idClassificacao;
    """, cursor, out_path, "Resumão de Menu Safic")
