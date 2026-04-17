"""
Relatório MADF — Movimento Anual de Documentos Fiscais (GIA x EFD por CFOP).
"""
from ._helpers import executar_e_formatar, iniciar_relatorio


def gerar_rel_madf(cursor, out_path, debug=False):
    iniciar_relatorio(out_path, "Relatório MADF", debug=debug)
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
