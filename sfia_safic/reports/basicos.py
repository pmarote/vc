"""
Relatório de Dados Básicos — GIAs, SPEDs, Conta Fiscal, etc.
"""
from ._helpers import executar_e_formatar, iniciar_relatorio


def gerar_rel_basicos(cursor, out_path, debug=False):
    iniciar_relatorio(out_path, "Relatório de Dados Básicos", debug=debug)
    where = "1 = 1"

    cursor.execute("SELECT min(referencia) AS dtamin, max(referencia) AS dtamax FROM _imp_ReferenciasSelecionadasNaImportacao;")
    row_dts = cursor.fetchone()
    dtamin = row_dts[0] if row_dts and row_dts[0] else ""
    dtamax = row_dts[1] if row_dts and row_dts[1] else ""

    executar_e_formatar("""
        SELECT max(nome) AS Empresa, max(cnpj) AS CNPJ, max(ie) AS IE FROM
        (SELECT nome, cnpj, ie FROM _fiscal_participantedeclarado WHERE idParticipanteDeclarado = 1);
    """, cursor, out_path, "Dados do contribuinte")

    executar_e_formatar("SELECT A.* FROM _fiscal_historicodeie AS A;", cursor, out_path, "Historico:")
    executar_e_formatar("SELECT A.* FROM _dbo_Versao AS A;", cursor, out_path, "Versão do dbo:")

#    executar_e_formatar(f"""
#        SELECT A.numOsf, A.dataDeCriacao, A.loginUsuario, A.cnpj, A.ie, A.razao, A.formaDeAcionamento
#        FROM _dbo_auditoria AS A WHERE numOsf = {num_osf};
#    """, cursor, out_path, "Dados da Auditoria:")

    executar_e_formatar("""
        SELECT 'ArqsEFDs' AS tipo, count(idEfd0000) AS Qtd, min(DT_INI) AS min_DT_INI, max(DT_FIN) AS max_DT_FIN, NOME, CNPJ, IE FROM _fiscal_EFD0000 AS A
        UNION ALL SELECT 'ArqsNFes' AS tipo, count(idNFe0000) AS Qtd, min(DT_INI) AS min_DT_INI, max(DT_FIN) AS max_DT_FIN, '' AS NOME, CNPJ, '' AS IE FROM _fiscal_NFe0000 AS B
        UNION ALL SELECT 'ArqsNFCes' AS tipo, count(idNFCe0000) AS Qtd, min(DT_INI) AS min_DT_INI, max(DT_FIN) AS max_DT_FIN, '' AS NOME, CNPJ, '' AS IE FROM _fiscal_NFCe0000 AS C
        UNION ALL SELECT 'ArqsSats' AS tipo, count(idSat0000) AS Qtd, min(DT_INI) AS min_DT_INI, max(DT_FIN) AS max_DT_FIN, '' AS NOME, CNPJ, '' AS IE FROM _fiscal_Sat0000 AS D
        UNION ALL SELECT 'ArqsCteOss' AS tipo, count(idCteOs0000) AS Qtd, min(DT_INI) AS min_DT_INI, max(DT_FIN) AS max_DT_FIN, '' AS NOME, CNPJ, '' AS IE FROM _fiscal_CteOs0000 AS E
        UNION ALL SELECT 'ArqsEvts' AS tipo, count(idEvt0000) AS Qtd, min(DT_INI) AS min_DT_INI, max(DT_FIN) AS max_DT_FIN, '' AS NOME, CNPJ, '' AS IE FROM _fiscal_Evt0000 AS F
        UNION ALL SELECT 'ArqsFcis' AS tipo, count(idFci0000) AS Qtd, min(DT_INI) AS min_DT_INI, max(DT_FIN) AS max_DT_FIN, '' AS NOME, CNPJ, '' AS IE FROM _fiscal_Fci0000 AS G;
    """, cursor, out_path, "Arqs_baixados e suas referencias")

    with open(out_path, "a", encoding="utf-8") as f:
        f.write(f"## Com base nos parâmetros de importação de dados do Safic, foi definido:\n")
        f.write(f"### Data inicial(dtamin): '_{dtamin}_' - Data final(dtamax): '_{dtamax}_'\n\n")

    executar_e_formatar("""
        SELECT '_imp_ReferenciasSelecionadasNaImportacao' AS tipo, count(referencia) AS Qtd, min(referencia) AS min_referencia, max(referencia) AS max_referencia FROM _imp_ReferenciasSelecionadasNaImportacao AS A
        UNION ALL SELECT '_procFisc_ReferenciaDaOsf' AS tipo, count(referencia) AS Qtd, min(referencia) AS min_referencia, max(referencia) AS max_referencia FROM _procFisc_ReferenciaDaOsf AS B
    """, cursor, out_path, "Parâmetros de Importação")

    executar_e_formatar("""
        WITH UltimaDeclaracao AS (
            SELECT cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia, MAX(dataDeEntrega) AS dataDeEntrega
            FROM _fiscal_ApuracaoDeIcmsPelaGia GROUP BY cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia
        )
        SELECT SUBSTR(B.dataDeReferencia, 1, 4) || SUBSTR(B.dataDeReferencia, 6, 2) AS aaaamm,
            B.campo51SaidasComDebito AS c51, B.campo56EntradasComCredito AS c56, ROUND(B.campo51SaidasComDebito - B.campo56EntradasComCredito, 2) AS sdoOper,
            B.campo52OutrosDebitos AS c52, B.campo53EstornoDeCreditos AS c53, B.campo57OutrosCreditos AS c57, B.campo58EstornoDeDebitos AS c58,
            ROUND(B.campo52OutrosDebitos + B.campo53EstornoDeCreditos - B.campo57OutrosCreditos - B.campo58EstornoDeDebitos, 2) AS sdoNOper,
            B.campo55TotalDeDebitos AS c55, B.campo60SubtotalDeCreditos AS c60, B.campo61SaldoCredorDoPeriodoAnterior AS c61,
            B.campo62TotalDeCreditos AS c62, B.campo63SaldoDevedor AS c63, B.campo64Deducoes AS c64, B.campo65ImpostoARecolher AS c65, B.campo66SaldoCredorATransportar AS c66
        FROM UltimaDeclaracao AS sqA
        LEFT OUTER JOIN _fiscal_ApuracaoDeIcmsPelaGia AS B ON B.cnpj = sqA.cnpj AND B.ie = sqA.ie AND B.idTipoDeOperacaoNaGia = sqA.idTipoDeOperacaoNaGia AND B.dataDeReferencia = sqA.dataDeReferencia AND B.dataDeEntrega = sqA.dataDeEntrega
        WHERE B.idTipoDeOperacaoNaGia = 0 ORDER BY aaaamm;
    """, cursor, out_path, "Valores conforme GIAs (Operação Própria)")

    executar_e_formatar("""
        SELECT SUBSTR(A.referencia, 1, 4) || SUBSTR(A.referencia, 6, 2) AS aaaamm,
            A.VL_TOT_DEBITOS AS c51, A.VL_TOT_CREDITOS AS c56, ROUND(A.VL_TOT_DEBITOS - A.VL_TOT_CREDITOS, 2) AS sdoOper,
            (A.VL_AJ_DEBITOS + A.VL_TOT_AJ_DEBITOS) AS c52, A.VL_ESTORNOS_CRED AS c53, (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS) AS c57, A.VL_ESTORNOS_DEB AS c58,
            ROUND((A.VL_AJ_DEBITOS + A.VL_TOT_AJ_DEBITOS + A.VL_ESTORNOS_CRED) - (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS + A.VL_ESTORNOS_DEB), 2) AS sdoNOper,
            ROUND(A.VL_TOT_DEBITOS + (A.VL_AJ_DEBITOS + A.VL_TOT_AJ_DEBITOS) + A.VL_ESTORNOS_CRED, 2) AS c55,
            ROUND(A.VL_TOT_CREDITOS + (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS) + A.VL_ESTORNOS_DEB, 2) AS c60,
            A.VL_SLD_CREDOR_ANT AS c61, ROUND(A.VL_TOT_CREDITOS + (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS) + A.VL_ESTORNOS_DEB + A.VL_SLD_CREDOR_ANT, 2) AS c62, A.VL_SLD_APURADO AS c63, A.DEB_ESP AS c64, A.VL_ICMS_RECOLHER AS c65, A.VL_SLD_CREDOR_TRANSPORTAR AS c66, A.VL_TOT_DED
        FROM _fiscal_ApuracaoDeIcmsPelaEfd AS A ORDER BY aaaamm;
    """, cursor, out_path, "Valores conforme SPEDs (Operação Própria)")

    executar_e_formatar("""
        WITH DadosGIA AS (
            SELECT SUBSTR(B.dataDeReferencia, 1, 4) || SUBSTR(B.dataDeReferencia, 6, 2) AS aaaamm,
                B.campo51SaidasComDebito AS c51, B.campo56EntradasComCredito AS c56, ROUND(B.campo51SaidasComDebito - B.campo56EntradasComCredito, 2) AS sdoOper,
                B.campo52OutrosDebitos AS c52, B.campo53EstornoDeCreditos AS c53, B.campo57OutrosCreditos AS c57, B.campo58EstornoDeDebitos AS c58,
                ROUND(B.campo52OutrosDebitos + B.campo53EstornoDeCreditos - B.campo57OutrosCreditos - B.campo58EstornoDeDebitos, 2) AS sdoNOper,
                B.campo55TotalDeDebitos AS c55, B.campo60SubtotalDeCreditos AS c60, B.campo61SaldoCredorDoPeriodoAnterior AS c61,
                B.campo62TotalDeCreditos AS c62, B.campo63SaldoDevedor AS c63, B.campo64Deducoes AS c64, B.campo65ImpostoARecolher AS c65, B.campo66SaldoCredorATransportar AS c66
            FROM (SELECT cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia, MAX(dataDeEntrega) AS dataDeEntrega FROM _fiscal_ApuracaoDeIcmsPelaGia GROUP BY cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia) AS sqA
            LEFT JOIN _fiscal_ApuracaoDeIcmsPelaGia AS B ON B.cnpj = sqA.cnpj AND B.dataDeReferencia = sqA.dataDeReferencia AND B.dataDeEntrega = sqA.dataDeEntrega AND B.idTipoDeOperacaoNaGia = sqA.idTipoDeOperacaoNaGia
            WHERE B.idTipoDeOperacaoNaGia = 0
        ),
        DadosEFD AS (
            SELECT SUBSTR(A.referencia, 1, 4) || SUBSTR(A.referencia, 6, 2) AS aaaamm,
                A.VL_TOT_DEBITOS AS c51, A.VL_TOT_CREDITOS AS c56, ROUND(A.VL_TOT_DEBITOS - A.VL_TOT_CREDITOS, 2) AS sdoOper,
                (A.VL_AJ_DEBITOS + A.VL_TOT_AJ_DEBITOS) AS c52, A.VL_ESTORNOS_CRED AS c53, (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS) AS c57, A.VL_ESTORNOS_DEB AS c58,
                ROUND((A.VL_AJ_DEBITOS + A.VL_TOT_AJ_DEBITOS + A.VL_ESTORNOS_CRED) - (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS + A.VL_ESTORNOS_DEB), 2) AS sdoNOper,
                ROUND(A.VL_TOT_DEBITOS + (A.VL_AJ_DEBITOS + A.VL_TOT_AJ_DEBITOS) + A.VL_ESTORNOS_CRED, 2) AS c55,
                ROUND(A.VL_TOT_CREDITOS + (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS) + A.VL_ESTORNOS_DEB, 2) AS c60,
                A.VL_SLD_CREDOR_ANT AS c61, ROUND(A.VL_TOT_CREDITOS + (A.VL_AJ_CREDITOS + A.VL_TOT_AJ_CREDITOS) + A.VL_ESTORNOS_DEB + A.VL_SLD_CREDOR_ANT, 2) AS c62, A.VL_SLD_APURADO AS c63, A.DEB_ESP AS c64, A.VL_ICMS_RECOLHER AS c65, A.VL_SLD_CREDOR_TRANSPORTAR AS c66
            FROM _fiscal_ApuracaoDeIcmsPelaEfd AS A
        )
        SELECT G.aaaamm, ROUND(COALESCE(G.c51,0) - COALESCE(E.c51,0), 2) AS dif_c51, ROUND(COALESCE(G.c56,0) - COALESCE(E.c56,0), 2) AS dif_c56, ROUND(COALESCE(G.sdoOper,0) - COALESCE(E.sdoOper,0), 2) AS dif_sdoOper,
            ROUND(COALESCE(G.c52,0) - COALESCE(E.c52,0), 2) AS dif_c52, ROUND(COALESCE(G.c53,0) - COALESCE(E.c53,0), 2) AS dif_c53, ROUND(COALESCE(G.c57,0) - COALESCE(E.c57,0), 2) AS dif_c57, ROUND(COALESCE(G.c58,0) - COALESCE(E.c58,0), 2) AS dif_c58, ROUND(COALESCE(G.sdoNOper,0) - COALESCE(E.sdoNOper,0), 2) AS dif_sdoNOper,
            ROUND(COALESCE(G.c55,0) - COALESCE(E.c55,0), 2) AS dif_c55, ROUND(COALESCE(G.c60,0) - COALESCE(E.c60,0), 2) AS dif_c60, ROUND(COALESCE(G.c61,0) - COALESCE(E.c61,0), 2) AS dif_c61, ROUND(COALESCE(G.c62,0) - COALESCE(E.c62,0), 2) AS dif_c62, ROUND(COALESCE(G.c63,0) - COALESCE(E.c63,0), 2) AS dif_c63, ROUND(COALESCE(G.c64,0) - COALESCE(E.c64,0), 2) AS dif_c64, ROUND(COALESCE(G.c65,0) - COALESCE(E.c65,0), 2) AS dif_c65, ROUND(COALESCE(G.c66,0) - COALESCE(E.c66,0), 2) AS dif_c66
        FROM DadosGIA AS G LEFT JOIN DadosEFD AS E ON G.aaaamm = E.aaaamm ORDER BY G.aaaamm;
    """, cursor, out_path, "Diferenças entre GIAs e EFDs (Operação Própria)")

    executar_e_formatar("""
        WITH UltimaDeclaracao AS (
            SELECT cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia, MAX(dataDeEntrega) AS dataDeEntrega
            FROM _fiscal_ApuracaoDeIcmsPelaGia GROUP BY cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia
        )
        SELECT SUBSTR(B.dataDeReferencia, 1, 4) || SUBSTR(B.dataDeReferencia, 6, 2) AS aaaamm,
            B.campo51SaidasComDebito AS c51, B.campo56EntradasComCredito AS c56, ROUND(B.campo51SaidasComDebito - B.campo56EntradasComCredito, 2) AS sdoOper,
            B.campo52OutrosDebitos AS c52, B.campo53EstornoDeCreditos AS c53, B.campo57OutrosCreditos AS c57, B.campo58EstornoDeDebitos AS c58,
            ROUND(B.campo52OutrosDebitos + B.campo53EstornoDeCreditos - B.campo57OutrosCreditos - B.campo58EstornoDeDebitos, 2) AS sdoNOper,
            B.campo55TotalDeDebitos AS c55, B.campo60SubtotalDeCreditos AS c60, B.campo61SaldoCredorDoPeriodoAnterior AS c61,
            B.campo62TotalDeCreditos AS c62, B.campo63SaldoDevedor AS c63, B.campo64Deducoes AS c64, B.campo65ImpostoARecolher AS c65, B.campo66SaldoCredorATransportar AS c66
        FROM UltimaDeclaracao AS sqA
        LEFT OUTER JOIN _fiscal_ApuracaoDeIcmsPelaGia AS B ON B.cnpj = sqA.cnpj AND B.ie = sqA.ie AND B.idTipoDeOperacaoNaGia = sqA.idTipoDeOperacaoNaGia AND B.dataDeReferencia = sqA.dataDeReferencia AND B.dataDeEntrega = sqA.dataDeEntrega
        WHERE B.idTipoDeOperacaoNaGia = 1 ORDER BY aaaamm;
    """, cursor, out_path, "Valores conforme GIAs ST")

    executar_e_formatar("""
        SELECT SUBSTR(A.referencia, 1, 4) || SUBSTR(A.referencia, 6, 2) AS aaaamm,
            A.VL_RETENÇAO_ST AS c51, A.VL_OUT_CRED_ST AS c56, ROUND(A.VL_RETENÇAO_ST - A.VL_OUT_CRED_ST, 2) AS sdoOper,
            (A.VL_AJ_DEBITOS_ST) AS c52, 0 AS c53, (A.VL_AJ_CREDITOS_ST) AS c57, 0 AS c58, ROUND((A.VL_AJ_DEBITOS_ST) - (A.VL_AJ_CREDITOS_ST), 2) AS sdoNOper,
            ROUND(A.VL_RETENÇAO_ST + (A.VL_AJ_DEBITOS_ST), 2) AS c55, ROUND(A.VL_OUT_CRED_ST + (A.VL_AJ_CREDITOS_ST), 2) AS c60,
            A.VL_SLD_CRED_ANT_ST AS c61, ROUND(A.VL_OUT_CRED_ST + (A.VL_AJ_CREDITOS_ST) + A.VL_SLD_CRED_ANT_ST, 2) AS c62, A.VL_SLD_DEV_ANT_ST AS c63, A.DEB_ESP_ST AS c64, A.VL_ICMS_RECOL_ST AS c65, A.VL_SLD_CRED_ST_TRANSPORTAR AS c66
        FROM _fiscal_ApuracaoDeIcmsPelaEfd AS A ORDER BY aaaamm;
    """, cursor, out_path, "Valores ST conforme SPEDs")

    executar_e_formatar("""
        WITH DadosGIA_ST AS (
            SELECT SUBSTR(B.dataDeReferencia, 1, 4) || SUBSTR(B.dataDeReferencia, 6, 2) AS aaaamm,
                B.campo51SaidasComDebito AS c51, B.campo56EntradasComCredito AS c56, ROUND(B.campo51SaidasComDebito - B.campo56EntradasComCredito, 2) AS sdoOper,
                B.campo52OutrosDebitos AS c52, B.campo53EstornoDeCreditos AS c53, B.campo57OutrosCreditos AS c57, B.campo58EstornoDeDebitos AS c58,
                ROUND(B.campo52OutrosDebitos + B.campo53EstornoDeCreditos - B.campo57OutrosCreditos - B.campo58EstornoDeDebitos, 2) AS sdoNOper,
                B.campo55TotalDeDebitos AS c55, B.campo60SubtotalDeCreditos AS c60, B.campo61SaldoCredorDoPeriodoAnterior AS c61,
                B.campo62TotalDeCreditos AS c62, B.campo63SaldoDevedor AS c63, B.campo64Deducoes AS c64, B.campo65ImpostoARecolher AS c65, B.campo66SaldoCredorATransportar AS c66
            FROM (SELECT cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia, MAX(dataDeEntrega) AS dataDeEntrega FROM _fiscal_ApuracaoDeIcmsPelaGia GROUP BY cnpj, ie, idTipoDeOperacaoNaGia, dataDeReferencia) AS sqA
            LEFT JOIN _fiscal_ApuracaoDeIcmsPelaGia AS B ON B.cnpj = sqA.cnpj AND B.ie = sqA.ie AND B.idTipoDeOperacaoNaGia = sqA.idTipoDeOperacaoNaGia AND B.dataDeReferencia = sqA.dataDeReferencia AND B.dataDeEntrega = sqA.dataDeEntrega
            WHERE B.idTipoDeOperacaoNaGia = 1
        ),
        DadosEFD_ST AS (
            SELECT SUBSTR(A.referencia, 1, 4) || SUBSTR(A.referencia, 6, 2) AS aaaamm,
                A.VL_RETENÇAO_ST AS c51, A.VL_OUT_CRED_ST AS c56, ROUND(A.VL_RETENÇAO_ST - A.VL_OUT_CRED_ST, 2) AS sdoOper,
                (A.VL_AJ_DEBITOS_ST) AS c52, 0 AS c53, (A.VL_AJ_CREDITOS_ST) AS c57, 0 AS c58, ROUND((A.VL_AJ_DEBITOS_ST) - (A.VL_AJ_CREDITOS_ST), 2) AS sdoNOper,
                ROUND(A.VL_RETENÇAO_ST + (A.VL_AJ_DEBITOS_ST), 2) AS c55, ROUND(A.VL_OUT_CRED_ST + (A.VL_AJ_CREDITOS_ST), 2) AS c60,
                A.VL_SLD_CRED_ANT_ST AS c61, ROUND(A.VL_OUT_CRED_ST + (A.VL_AJ_CREDITOS_ST) + A.VL_SLD_CRED_ANT_ST, 2) AS c62, A.VL_SLD_DEV_ANT_ST AS c63, A.DEB_ESP_ST AS c64, A.VL_ICMS_RECOL_ST AS c65, A.VL_SLD_CRED_ST_TRANSPORTAR AS c66
            FROM _fiscal_ApuracaoDeIcmsPelaEfd AS A
        )
        SELECT G.aaaamm, ROUND(COALESCE(G.c51,0) - COALESCE(E.c51,0), 2) AS dif_c51, ROUND(COALESCE(G.c56,0) - COALESCE(E.c56,0), 2) AS dif_c56, ROUND(COALESCE(G.sdoOper,0) - COALESCE(E.sdoOper,0), 2) AS dif_sdoOper,
            ROUND(COALESCE(G.c52,0) - COALESCE(E.c52,0), 2) AS dif_c52, ROUND(COALESCE(G.c53,0) - COALESCE(E.c53,0), 2) AS dif_c53, ROUND(COALESCE(G.c57,0) - COALESCE(E.c57,0), 2) AS dif_c57, ROUND(COALESCE(G.c58,0) - COALESCE(E.c58,0), 2) AS dif_c58, ROUND(COALESCE(G.sdoNOper,0) - COALESCE(E.sdoNOper,0), 2) AS dif_sdoNOper,
            ROUND(COALESCE(G.c55,0) - COALESCE(E.c55,0), 2) AS dif_c55, ROUND(COALESCE(G.c60,0) - COALESCE(E.c60,0), 2) AS dif_c60, ROUND(COALESCE(G.c61,0) - COALESCE(E.c61,0), 2) AS dif_c61, ROUND(COALESCE(G.c62,0) - COALESCE(E.c62,0), 2) AS dif_c62, ROUND(COALESCE(G.c63,0) - COALESCE(E.c63,0), 2) AS dif_c63, ROUND(COALESCE(G.c64,0) - COALESCE(E.c64,0), 2) AS dif_c64, ROUND(COALESCE(G.c65,0) - COALESCE(E.c65,0), 2) AS dif_c65, ROUND(COALESCE(G.c66,0) - COALESCE(E.c66,0), 2) AS dif_c66
        FROM DadosGIA_ST AS G LEFT JOIN DadosEFD_ST AS E ON G.aaaamm = E.aaaamm ORDER BY G.aaaamm;
    """, cursor, out_path, "Diferenças entre GIAs ST e valores STs das EFDs")

    executar_e_formatar("""
        SELECT A.referencia, A.entregaDifalFcp, A.VL_TOT_DEBITOS_DIFAL, A.VL_TOT_CREDITOS_DIFAL, round(A.VL_TOT_DEBITOS_DIFAL - A.VL_TOT_CREDITOS_DIFAL, 2) AS sdoOperDifal,
        A.VL_OUT_DEB_DIFAL, A.VL_OUT_CRED_DIFAL, A.VL_SLD_CRED_ANT_DIFAL, A.VL_SLD_DEV_ANT_DIFAL,
        A.VL_DEDUCOES_DIFAL, A.VL_RECOL_DIFAL, A.VL_SLD_CRED_TRANSPORTAR_DIFAL, A.DEB_ESP_DIFAL
        FROM _fiscal_ApuracaoDeIcmsPelaEfd AS A
    """, cursor, out_path, "Difal")

    executar_e_formatar("""
        SELECT A.referencia, A.entregaDifalFcp, A.VL_TOT_DEB_FCP, A.VL_TOT_CRED_FCP, round(A.VL_TOT_DEB_FCP - A.VL_TOT_CRED_FCP, 2) AS sdoOperFCP,
        A.VL_OUT_DEB_FCP, A.VL_OUT_CRED_FCP, A.VL_SLD_CRED_ANT_FCP, A.VL_SLD_DEV_ANT_FCP,
        A.VL_DEDUCOES_FCP, A.VL_RECOL_FCP, A.VL_SLD_CRED_TRANSPORTAR_FCP, A.DEB_ESP_FCP
        FROM _fiscal_ApuracaoDeIcmsPelaEfd AS A
    """, cursor, out_path, "FCP")

    executar_e_formatar(f"""
        SELECT A.descricaoDoTipoDeDeclaracaoNoDw AS TpDeclaracao, substr(A.dataDeReferencia, 1, 4) || substr(A.dataDeReferencia, 6, 2) AS aaaamm,
        A.codigoTransferenciaDeSaldoNoDw AS codigo, A.descricaoDoCredito, A.descricaoDaSituacaoDaDeclaracaoNoDw AS descricaoSituacao,
        A.descricaoDaTransferenciaDeSaldoNoDw AS TransferenciaSaldo, A.valor65, A.valorArrecadado AS Arrecadado, A.valorDebitoVencido AS Vencido,
        A.valorLancamentoEspecial AS LanctoEspecial, A.valorTotalArrecadadoVencido AS TotArrecadadoVencido
        FROM _fiscal_CfIcms AS A WHERE {where} ORDER BY A.descricaoDoTipoDeDeclaracaoNoDw DESC, A.dataDeReferencia;
    """, cursor, out_path, "Conta Fiscal do ICMS")

    executar_e_formatar("""
        SELECT substr(referencia, 1, 7) AS ref,
          SUM(CASE WHEN CAST(cfop AS INT) < 5000 THEN valorDaOperacao ELSE 0 END) AS e_valcon,
          SUM(CASE WHEN CAST(cfop AS INT) < 5000 THEN icmsProprio ELSE 0 END) AS e_icms,
          SUM(CASE WHEN CAST(cfop AS INT) > 5000 THEN valorDaOperacao ELSE 0 END) AS s_valcon,
          SUM(CASE WHEN CAST(cfop AS INT) > 5000 THEN icmsProprio ELSE 0 END) AS s_icms
        FROM DocAtrib_fiscal_DocAtributosDeApuracao AS AA GROUP BY ref;
    """, cursor, out_path, "Totais para Fins de Relatório de OF")
