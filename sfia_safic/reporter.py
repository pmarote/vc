import sqlite3
import os
import re
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
def gerar_rel_basicos(cursor, out_path, num_osf):
    iniciar_relatorio(out_path, "Relatório de Dados Básicos")
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
    
    executar_e_formatar(f"""
        SELECT A.numOsf, A.dataDeCriacao, A.loginUsuario, A.cnpj, A.ie, A.razao, A.formaDeAcionamento
        FROM _dbo_auditoria AS A WHERE numOsf = {num_osf};
    """, cursor, out_path, "Dados da Auditoria:")

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

    # GIAs e SPEDs Operação Própria
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

    # GIAs e SPEDs ST
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

# =============================================================================
# 2. RELATÓRIO DE ANÁLISES ECONÔMICAS
# =============================================================================
def gerar_rel_an_econ(cursor, out_path):
    iniciar_relatorio(out_path, "Análises Econômicas")

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '1-Receitas' GROUP BY cnpjPart14 ORDER BY es_valconEFD DESC
    """, cursor, out_path, "Receitas")

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '2-Compras Insumos' GROUP BY cnpjPart14 ORDER BY es_valconEFD
    """, cursor, out_path, "Compras Insumos")

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '3-Compras Consumo' GROUP BY cnpjPart14 ORDER BY es_valconEFD
    """, cursor, out_path, "Compras Consumo")

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '4-Ativo' GROUP BY cnpjPart14 ORDER BY es_valconEFD
    """, cursor, out_path, "Ativo")

    executar_e_formatar("""
        SELECT Part, g2, g3 || ' ' || classe || ' ' || descri_simplif AS cfop_tipo,
          SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '5-Entradas/Saídas' AND g2 = '01z - Produção - Outros' GROUP BY cnpjPart14, g2, g3, classe ORDER BY cnpjOrder, cnpjPart14, g2, g3, classe
    """, cursor, out_path, "Entradas/Saídas")

    executar_e_formatar("""
        SELECT Part, g2, g3 || ' ' || classe || ' ' || descri_simplif AS cfop_tipo,
          SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '6-Outros' OR (g1 = '5-Entradas/Saídas' AND g2 <> '01z - Produção - Outros') GROUP BY cnpjPart14, g2, g3, classe ORDER BY cnpjOrder, cnpjPart14, g2, g3, classe
    """, cursor, out_path, "Outros")

# =============================================================================
# 3. RELATÓRIO DE CONCILIAÇÃO
# =============================================================================
def gerar_rel_conc(cursor, out_path, limite=5):
    iniciar_relatorio(out_path, "Relatórios de Conciliação")
    
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

# =============================================================================
# 4. RELATÓRIO DE EXPORTAÇÃO DE DADOS
# =============================================================================
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

    # Obs: Algumas das views abaixo existem no banco original e caso nao estejam populadas podem gerar erro de Tabela Não Encontrada, mas mantive todas as suas queries
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
        ("EfdH010_ItemServicoDeclarado_EfdH005_EfdH010Descr_EfdH010Posse_EfdH010Prop", "View osf.EfdH010_ItemServicoDeclarado...")
    ]

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

    for tabela, titulo in tabelas_views:
        executar_e_formatar(f"SELECT * FROM {tabela} LIMIT {limite}", cursor, out_path, titulo)


# =============================================================================
# 5. RELATÓRIO MADF
# =============================================================================
def gerar_rel_madf(cursor, out_path):
    iniciar_relatorio(out_path, "Relatório MADF")
    where = "1 = 1"

    executar_e_formatar(f"""
        SELECT g1, sum(valconGia) AS valconGia, sum(valconEfd) AS valconEfd, sum(valconDif) AS valconDif, sum(icmsGia) AS icmsGia, sum(icmsEfd) AS icmsEfd, sum(icmsDif) AS icmsDif, sum(icmsstGia) AS icmsstGia, sum(icmsstEfd) AS icmsstEfd, sum(icmsstDif) AS icmsstDif
          FROM madf WHERE {where} GROUP BY g1
        UNION ALL SELECT '#GIAs do Período de ' || min(aaaamm) ||  ' a ' || max(aaaamm) ||  '#', Null, Null, Null, Null, Null, Null, Null, Null, Null FROM madf
        UNION ALL SELECT '#Repeticao de Ref e CFOP? ' || CASE WHEN max(qtd) > 0 THEN '#' || max(qtd) || '#' ELSE max(qtd) END AS maxqtd, Null, Null, Null, Null, Null, Null, Null, Null, Null FROM
        (SELECT CFOP, referencia, count(referencia) AS qtd  FROM _fiscal_ComparacaoGiaEfdPorCfop GROUP BY CFOP, referencia) AS sqA ORDER BY g1;
    """, cursor, out_path, "Madf n1")

    executar_e_formatar(f"""
        SELECT g1,g2, sum(valconGia) AS valconGia, sum(valconEfd) AS valconEfd, sum(valconDif) AS valconDif, sum(icmsGia) AS icmsGia, sum(icmsEfd) AS icmsEfd, sum(icmsDif) AS icmsDif, sum(icmsstGia) AS icmsstGia, sum(icmsstEfd) AS icmsstEfd, sum(icmsstDif) AS icmsstDif
          FROM madf WHERE {where} GROUP BY g1, g2;
    """, cursor, out_path, "Madf n2_1")

    executar_e_formatar(f"""
        SELECT g1,dfi, sum(valconGia) AS valconGia, sum(valconEfd) AS valconEfd, sum(valconDif) AS valconDif, sum(icmsGia) AS icmsGia, sum(icmsEfd) AS icmsEfd, sum(icmsDif) AS icmsDif, sum(icmsstGia) AS icmsstGia, sum(icmsstEfd) AS icmsstEfd, sum(icmsstDif) AS icmsstDif
          FROM madf WHERE {where} GROUP BY g1, dfi
    """, cursor, out_path, "Madf n2_2")

    executar_e_formatar(f"""
        SELECT g1,g2, classe, descri_simplif, sum(valconGia) AS valconGia, sum(valconEfd) AS valconEfd, sum(valconDif) AS valconDif, sum(icmsGia) AS icmsGia, sum(icmsEfd) AS icmsEfd, sum(icmsDif) AS icmsDif, sum(icmsstGia) AS icmsstGia, sum(icmsstEfd) AS icmsstEfd, sum(icmsstDif) AS icmsstDif
          FROM madf WHERE {where} GROUP BY g1, g2, classe, descri_simplif
    """, cursor, out_path, "Madf n3")

    executar_e_formatar(f"""
        SELECT sqA.tpGia, sqA.aaaa, sum(sqA.c51) AS c51, sum(sqA.c56) AS c56, sum(sqA.sdoOper) AS sdoOper, sum(sqA.c52) AS c52, sum(sqA.c53) AS c53, sum(sqA.c57) AS c57, sum(sqA.c58) AS c58, sum(sqA.sdoNOper) AS sdoNOper FROM (
        SELECT substr(dataDeReferencia, 1, 4) AS aaaa, idTipoDeOperacaoNaGia AS tpGia, campo51SaidasComDebito AS c51, campo56EntradasComCredito AS c56, round(campo51SaidasComDebito - campo56EntradasComCredito, 2) AS sdoOper, campo52OutrosDebitos AS c52, campo53EstornoDeCreditos AS c53, campo57OutrosCreditos AS c57, campo58EstornoDeDebitos AS c58, round(campo52OutrosDebitos + campo53EstornoDeCreditos - campo57OutrosCreditos - campo58EstornoDeDebitos, 2) AS sdoNOper
          FROM _fiscal_ApuracaoDeIcmsPelaGia AS A WHERE {where} ) AS sqA GROUP BY tpGia, aaaa
    """, cursor, out_path, "PT Seleção X01 GIAs")

    executar_e_formatar(f"""
        SELECT sqA.aaaa, sum(sqA.c51) AS efd_c51, sum(sqA.c56) AS efd_c56, sum(sqA.sdoOper) AS efd_sdoOper, sum(sqA.c52) AS efd_c52, sum(sqA.c53) AS efd_c53, sum(sqA.c57) AS efd_c57, sum(sqA.c58) AS efd_c58, sum(sqA.sdoNOper) AS efd_sdoNOper FROM (
        SELECT SUBSTR(referencia, 1, 4) AS aaaa, Null AS tpGia, VL_TOT_DEBITOS AS c51, VL_TOT_CREDITOS AS c56, VL_TOT_DEBITOS - VL_TOT_CREDITOS AS sdoOper, VL_TOT_AJ_DEBITOS AS c52, VL_ESTORNOS_CRED AS c53, VL_TOT_AJ_CREDITOS AS c57, VL_ESTORNOS_DEB AS c58, VL_AJ_DEBITOS + VL_ESTORNOS_CRED - VL_AJ_CREDITOS - VL_ESTORNOS_DEB AS sdoNOper
          FROM _fiscal_ApuracaoDeIcmsPelaEfd AS A WHERE {where} ) AS sqA GROUP BY tpGia, aaaa
    """, cursor, out_path, "PT Seleção X01 EFDs")

    executar_e_formatar("""
        SELECT A.g1, A.g2, A.classe, A.descri_simplif, substr(A.aaaamm, 1, 4) AS aaaa, sum(A.valconGia) AS valconGia, sum(A.valconEfd) AS valconEfd, sum(A.icmsGia) AS icmsGia, sum(A.icmsEfd) AS icmsEfd, sum(A.icmsstGia) AS icmsstGia, sum(A.icmsstEfd) AS icmsstEfd
          FROM madf AS A LEFT OUTER JOIN cfopd AS B ON B.cfop = A.cfopi WHERE A.icmsGia < 0 AND B.pod_creditar <> 'S' GROUP BY A.classe, aaaa
    """, cursor, out_path, "PT Seleção X04")

    executar_e_formatar("""
        SELECT A.g1, A.g2, A.classe, A.descri_simplif, substr(A.aaaamm, 1, 4) AS aaaa, sum(A.valconGia) AS valconGia, sum(A.valconEfd) AS valconEfd, sum(A.icmsGia) AS icmsGia, sum(A.icmsEfd) AS icmsEfd, sum(A.icmsstGia) AS icmsstGia, sum(A.icmsstEfd) AS icmsstEfd
          FROM madf AS A LEFT OUTER JOIN cfopd AS B ON B.cfop = A.cfopi WHERE A.classe IN ('E927', 'S927') GROUP BY A.classe, aaaa
    """, cursor, out_path, "PT Seleção Perda Roubo")

    executar_e_formatar("""
        SELECT A.g1, A.g2, A.classe, A.descri_simplif, substr(A.aaaamm, 1, 4) AS aaaa, sum(A.valconGia) AS valconGia, sum(A.valconEfd) AS valconEfd, sum(A.icmsGia) AS icmsGia, sum(A.icmsEfd) AS icmsEfd, sum(A.icmsstGia) AS icmsstGia, sum(A.icmsstEfd) AS icmsstEfd
          FROM madf AS A LEFT OUTER JOIN cfopd AS B ON B.cfop = A.cfopi WHERE B.classe IN ('S933','S949') GROUP BY A.classe, aaaa
    """, cursor, out_path, "PT Seleção X06 ISS e Exclusões BC")

    executar_e_formatar("""
        SELECT A.g1, A.g2, A.classe, A.descri_simplif, substr(A.aaaamm, 1, 4) AS aaaa, sum(A.valconGia) AS valconGia, sum(A.valconEfd) AS valconEfd, sum(A.icmsGia) AS icmsGia, sum(A.icmsEfd) AS icmsEfd, sum(A.icmsstGia) AS icmsstGia, sum(A.icmsstEfd) AS icmsstEfd
          FROM madf AS A LEFT OUTER JOIN cfopd AS B ON B.cfop = A.cfopi WHERE B.classe IN ('S905','S934','E906','E907') GROUP BY A.classe, aaaa
    """, cursor, out_path, "PT Seleção X11 Depósito Fechado")

# =============================================================================
# 6. RELATÓRIO SAFIC MENU (RESUMÃO)
# =============================================================================
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

# =============================================================================
# 7. RELATÓRIO SAFIC MENU DETALHES
# =============================================================================
def gerar_rel_safic_menu_det(cursor, out_path):
    iniciar_relatorio(out_path, "Análises do Safic - Detalhes")

    MENU_TOP_TEMPLATE = """
    WITH BaseDados AS (
        SELECT {campos_adic}
            tp_codSit, tp_oper, 
            CASE 
                WHEN length(Part) > 70 THEN substr(Part, 1, 35) || '<br>' || substr(Part, 36, 35) || '<br>' || substr(Part, 71)
                WHEN length(Part) > 35 THEN substr(Part, 1, 35) || '<br>' || substr(Part, 36)
               ELSE Part 
            END AS Part,
            ChNrOrigem, ChNrCfops, count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(dif_icmsstSP) AS dif_icmsstSP,
            sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD,
            sum(vl_docDFe) AS vl_docDFe, sum(vl_docEFD) AS vl_docEFD,
            CASE WHEN length(DFeDescris) > 70 THEN substr(DFeDescris, 1, 35) || '<br>' || substr(DFeDescris, 36, 35) || '<br>' || substr(DFeDescris, 71, 35) WHEN length(DFeDescris) > 35 THEN substr(DFeDescris, 1, 35) || '<br>' || substr(DFeDescris, 36) ELSE DFeDescris END AS AmostraDFeDescris,
            CASE WHEN length(obs) > 70 THEN substr(obs, 1, 35) || '<br>' || substr(obs, 36, 35) || '<br>' || substr(obs, 71, 35) WHEN length(obs) > 35 THEN substr(obs, 1, 35) || '<br>' || substr(obs, 36) ELSE obs END AS AmostraObs,
            ROW_NUMBER() OVER (ORDER BY {order_by}) AS ranking
        FROM chaveNroTudao WHERE ChNrClassifs LIKE '%{classif}%' GROUP BY {campos_adic} tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops
    )
    SELECT {campos_adic} tp_codSit AS codSit, tp_oper AS op, Part, ChNrOrigem, ChNrCfops, qtd, dif_vl_doc, dif_icms, dif_icmsstSP, vl_icmsDFe AS icmsDFe, vl_icmsEFD AS icmsEFD, vl_icmsstSP_DFe AS icmsstDFeSP, vl_icmsstSP_EFD AS icmsstEFDSP, vl_docDFe, vl_docEFD, AmostraDFeDescris, AmostraObs
    FROM BaseDados WHERE ranking <= {top_n}
    UNION ALL
    SELECT {campos_adic} '---' AS tp_codSit, '---' AS tp_oper, 'DEMAIS ITENS (SOMA)' AS Part, '---' AS ChNrOrigem, '---' AS ChNrCfops, SUM(qtd) AS qtd, SUM(dif_vl_doc) AS dif_vl_doc, SUM(dif_icms) AS dif_icms, SUM(dif_icmsstSP) AS dif_icmsstSP, SUM(vl_icmsDFe) AS vl_icmsDFe, SUM(vl_icmsEFD) AS vl_icmsEFD, SUM(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, SUM(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD, SUM(vl_docDFe) AS vl_docDFe, SUM(vl_docEFD) AS vl_docEFD, AmostraDFeDescris, AmostraObs
    FROM BaseDados WHERE ranking > {top_n} HAVING COUNT(*) > 0;
    """

    def executar_menu_det(classif, titulo, top_n="18", order_by="sum(vl_docDFe) DESC", campos_adic=""):
        query = MENU_TOP_TEMPLATE.replace("{classif}", classif)\
                                 .replace("{top_n}", top_n)\
                                 .replace("{order_by}", order_by)\
                                 .replace("{campos_adic}", campos_adic)
        executar_e_formatar(query, cursor, out_path, titulo)

    executar_menu_det("[1]", "[1] Documentos escriturados cancelados")

    # Menus estáticos exclusivos: [2] e [9]
    executar_e_formatar("""
        SELECT tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops, count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(dif_icmsstSP) AS dif_icmsstSP, sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD
        FROM (SELECT * FROM chaveNroTudao WHERE ChNrClassifs LIKE '%[2]%' ORDER BY numero) GROUP BY tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops ORDER BY dif_icms
    """, cursor, out_path, "[2] E 1.13 - documentos escriturados em duplicidade")

    executar_e_formatar("""
        SELECT tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops, count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(dif_icmsstSP) AS dif_icmsstSP, sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD
        FROM (SELECT * FROM chaveNroTudao WHERE ChNrClassifs LIKE '%[9]%' ORDER BY numero) GROUP BY tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops ORDER BY dif_icms
    """, cursor, out_path, "[9] E 1.17 - operações realizadas com fornecedores com a inscrição suspensa, inapta, baixada ou nula no cadastro de contribuintes")

    # Demais menus mapeados que usam o template
    executar_menu_det("[12]", "[12] E 1.14 - crédito de ICMS operação própria maior que o destacado no documento fiscal", order_by="sum(dif_icms)")
    executar_menu_det("[13]", "[13] S 1.4 - débito a menor: débitos de ICMS OP escriturados a menor que no destaque do documento fiscal", order_by="sum(dif_icms)")
    executar_menu_det("[14]", "[14] E 1.20 - documentos de entrada não escriturados")
    executar_menu_det("[15]", "[15] S 1.1 - inconsistência na escrituração: saídas não escrituradas")
    executar_menu_det("[16]", "[16] S 1.1 - E 1.6 - simulação de entrada: documentos CANCELADOS escriturados como Válidos, mas são entradas SEM crédito")
    executar_menu_det("[20]", "[20] NFes, CTes, NFCes e CFe SATs CANCELADOS destinados ao contribuinte auditado")
    executar_menu_det("[21]", "[21] NFes, CTes, NFCes e CFe SATs sem EFD entregue no período")
    executar_menu_det("[25]", "[25] Operações de entrada com ST")
    executar_menu_det("[26]", "[26] Operações de saída com ST")
    executar_menu_det("[35]", "[35] CIAP 1.2 - saída de bens do ativo imobilizado")
    executar_menu_det("[36]", "[36] CIAP 1.3 - apropriação de crédito de ativo imobilizado")
    executar_menu_det("[37]", "[37] E 3.3 - análise de operações com materiais de uso e consumo")
    executar_menu_det("[38]", "[38] ES 1.3 - análise de operações com armazéns gerais")
    executar_menu_det("[39]", "[39] E 2.6 - análise de crédito de fornecedores enquadrados no Regime de apuração do Simples Nacional")
    executar_menu_det("[40]", "[40] operações com a ZFM e as ALC")
    executar_menu_det("[41]", "[41] operações com energia elétrica")
    executar_menu_det("[42]", "[42] operações de aquisição de transporte")
    executar_menu_det("[43]", "[43] operações de serv. de comunicação")
    executar_menu_det("[46]", "[46] ES 1.1 - análise de operações com industrialização")
    executar_menu_det("[48]", "[48] E 1.17 - operações realizadas com fornecedores com a inscrição suspensa...")
    executar_menu_det("[53]", "[53] 9.3 l) margem de lucro ou preço de varejo inferior ao previsto na legislação nas operações de substituição tributária")
    executar_menu_det("[54]", "[54] item 39.4: análise de saídas interestaduais com ST item 39.9: análise de situação cadastral do adquirente de saídas interestaduais com ST")
    executar_menu_det("[56]", "[56] S 1.9 - operações com destinatários inscritos no cadastro de contribuintes, com situação cadastral inativa")
    executar_menu_det("[62]", "[62] S 1.8 - operações com destinatários incluídos no cadastro de inidôneos")
    executar_menu_det("[63]", "[63] S 1.8 - operações com destinatários incluídos no cadastro de inidôneos") # Duplicado no ckb, mantendo
    executar_menu_det("[64]", "[64] E 1.18 - crédito de operações próprias com substituição tributária")
    executar_menu_det("[65]", "[65] E 1.4 - simulação de entrada: entrada escriturada, sem crédito, a partir de documento eletrônico sem relação com o contribuinte auditado")
    executar_menu_det("[67]", "[67] S 2.6 - operações com destinatários localizados no Estado, mas não inscritos no cadastro de contribuintes")
    executar_menu_det("[69]", "[69] E 1.16 - crédito indevido: entrada escriturada com CFOP que geralmente não aceita crédito", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    executar_menu_det("[70]", "[70] CIAP 1.1 - entrada de bens para o ativo imobilizado")
    executar_menu_det("[71]", "[71] E 3.1 - análise de entradas interestaduais de produtos importados, com alíquota do imposto superior a 4%", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    executar_menu_det("[72]", "[72] E 3.2 - análise de crédito em operações com devolução de mercadorias")
    executar_menu_det("[73]", "[73] ES 1.4 - análise de operações com CFOP 1949 / 2949 / 3949 / 5949 / 6949 / 7949")
    executar_menu_det("[77]", "[77] S 2.5 - operações interestaduais com alíquota de 4%")
    executar_menu_det("[82]", "[82] ES 1.6 - análise de operações envolvendo demonstração")
    executar_menu_det("[85]", "[85] S 2.7 - operações de remessas para a Zona Franca de Manaus (ZFM) e Área de Livre Comércio (ALC)")
    executar_menu_det("[90]", "[90] E 3.4 - análise de operações de devolução de mercadorias de maior valor")
    executar_menu_det("[98]", "[98] E 1.5 - crédito indevido: documentos CANCELADOS escriturados COM crédito")
    executar_menu_det("[99]", "[99] E 1.7 - crédito indevido: documento fiscal de saída escriturado como entrada com crédito", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    executar_menu_det("[100]", "[100] E 1.15 - crédito de ICMS ST maior que o destacado no documento fiscal", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    executar_menu_det("[103]", "[103] NFes e CTes sem relação com o contribuinte")
    executar_menu_det("[104]", "[104] S 1.3 - débito a menor: saídas regulares escrituradas como canceladas ou denegadas", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    executar_menu_det("[106]", "[106] S 1.10 - documentos eletrônicos emitidos com sequência numérica com intervalos")
    executar_menu_det("[107]", "[107] S 1.6 - nota fiscal complementar emitido após a referência da nota fiscal normal")
    executar_menu_det("[108]", "[108] S 1.11 - nota fiscal cancelada após o prazo de 24h da emissão")
    executar_menu_det("[109]", "[109] E 2.5 - operações de entrada escrituradas com crédito de ICMS OP")
    executar_menu_det("[110]", "[110] E 1.14 operações de entrada de crédito de ativo imobilizado e uso e consumo escrituradas com crédito")
    executar_menu_det("[111]", "[111] AP 1.4 - verificação do Difal nas operações de entrada interestaduais com uso e consumo e ativo imobilizado")
    executar_menu_det("[114]", "[114] NFes de emissão própria escrituradas com crédito")
    executar_menu_det("[115]", "[115] NFes de emissão de terceiro escrituradas com crédito")
    executar_menu_det("[117]", "[117] E 1.12 - simulação de entrada: escrituração, sem crédito, de documento com manifestação do destinatário negando a operação")
    executar_menu_det("[118]", "[118] S 1.16 - operações de saída escrituradas, com débito, de documento com manifestação do destinatário negando a operação")
    executar_menu_det("[119]", "[119] 	S 1.17 - operações de saída escrituradas, sem débito, de documento com manifestação do destinatário negando a operação")
    executar_menu_det("[284]", "[284] S 1.23 - operações internas de saída para contribuinte sem escrituração na EFD do participante")
    executar_menu_det("[285]", "[285] S 1.24 - operações interestaduais de saída para contribuinte sem escrituração na EFD do participante")
    executar_menu_det("[367]", "[367] E 2.2 - análise de alíquotas de operações internas")
    executar_menu_det("[368]", "[368] E 2.3 - análise de alíquotas de operações interestaduais")
    executar_menu_det("[371]", "[371] E 4.0 - análise de devoluções com lig. de ítem emissão própria")
    executar_menu_det("[372]", "[372] 4.0 - análise de devoluções com lig. de ítem emissão terceiros")
    executar_menu_det("[374]", "[374] E 4.2 - análise de devoluções sem lig. de ítem emissão terceiros")
    
    # Com campos adicionais
    executar_menu_det("[375]", "[375] E 2.2 - análise de alíquotas de operações internas", campos_adic="DFeAliqs, EfdAliqs, ")
    executar_menu_det("[376]", "[376] E 2.4 - análise de alíquota em operações de transporte", campos_adic="DFeAliqs, EfdAliqs, ")

# =============================================================================
# ORQUESTRADOR PRINCIPAL
# =============================================================================
def gerar_relatorios(db_osf: str, db_sia: str, target_dir: Path):
    num_osf = re.sub(r'\D', '', os.path.basename(db_osf))
    if not num_osf:
        num_osf = "0"

    print(f"🗄️ Conectando às bases e iniciando relatórios (OSF {num_osf})...")
    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{db_osf}' AS osf;")

    # Chamada sequencial das rotinas isoladas e guardando os ficheiros no target_dir
    print(" ➔ Gerando Relatório de Dados Básicos...")
    gerar_rel_basicos(cursor, str(target_dir / "rel_basicos.md"), num_osf)

    print(" ➔ Gerando Análises Econômicas...")
    gerar_rel_an_econ(cursor, str(target_dir / "rel_an_econ.md"))

    print(" ➔ Gerando Relatórios de Conciliação...")
    gerar_rel_conc(cursor, str(target_dir / "rel_conc.md"), limite=5)

    print(" ➔ Gerando Exportações de Dados...")
    gerar_rel_exp_dados(cursor, str(target_dir / "rel_exp_dados.md"), limite=2)

    print(" ➔ Gerando Relatório MADF...")
    gerar_rel_madf(cursor, str(target_dir / "rel_madf.md"))

    print(" ➔ Gerando Safic Menu (Resumo)...")
    gerar_rel_safic_menu(cursor, str(target_dir / "rel_safic_menu.md"))

    print(" ➔ Gerando Safic Menu (Detalhes)...")
    gerar_rel_safic_menu_det(cursor, str(target_dir / "rel_safic_menu_det.md"))

    conn.close()
    print("✅ Todos os relatórios foram gerados com sucesso e guardados no diretório indicado!")