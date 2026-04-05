"""
Relatório de Análises Econômicas — Receitas, Compras, Ativo, Entradas/Saídas.
"""
from ._helpers import executar_e_formatar

def iniciar_relatorio_com_indice(out_path, titulo):
    """Cria o arquivo do relatório com o título, link para o menu e um Índice Interativo."""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n\n")
        f.write("#### Link para o menu de relatórios: [Menu de relatórios](menu_relatorios.html)\n\n")
        
        # --- Construção do Índice ---
        f.write("## 📑 Índice de Seções\n\n")
        
        f.write("### Visão Resumida (Top 20 + Demais)\n")
        f.write("1. [Receitas (Top 20)](#sec-receitas-top)\n")
        f.write("2a. [Compras Insumos (Top 20)](#sec-compras-ins-top)\n")
        f.write("2b. [Compras Consumo (Top 20)](#sec-compras-cons-top)\n")
        f.write("3. [Ativo (Top 20)](#sec-ativo-top)\n")
        f.write("4. [Entradas/Saídas - g2='01z - Produção - Outros' (Top 20)](#sec-01z-top)\n")
        f.write("5. [Entradas/Saídas - Resumo G1, G2, G3 e classe (Top 20)](#sec-outros-top)\n")
        f.write("6. [Entradas/Saídas - CFOP (Top 20)](#sec-cfop-top)\n\n")
        
        f.write("### Visão Analítica Completa\n")
        f.write("7. [Receitas (Completo)](#sec-receitas-full)\n")
        f.write("8a. [Compras Insumos (Completo)](#sec-compras-ins-full)\n")
        f.write("8b. [Compras Consumo (Completo)](#sec-compras-cons-full)\n")
        f.write("9. [Ativo (Completo)](#sec-ativo-full)\n")
        f.write("10. [Entradas/Saídas - g2='01z - Produção - Outros' (Completo)](#sec-01z-full)\n")
        f.write("11. [Entradas/Saídas - Resumo G1, G2, G3 e classe (Completo)](#sec-outros-full)\n")
        f.write("12. [Entradas/Saídas - CFOP (Completo)](#sec-cfop-full)\n\n")
        f.write("---\n\n")


def gerar_rel_an_econ(cursor, out_path):
    iniciar_relatorio_com_indice(out_path, "Análises Econômicas")

    # =========================================================================
    # PARTE 1: VISÃO RESUMIDA (TOP 20 + LINHA DEMAIS)
    # =========================================================================

    # 1. Receitas (Top 20)
    executar_e_formatar("""
        WITH BaseDados AS (
            SELECT Part, 
              SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
              SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
              ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
            FROM an_econ_base WHERE g1 = '1-Receitas' GROUP BY cnpjPart14, Part
        ),
        VisaoFinal AS (
            SELECT Part, es_valconEFD, es_icmsEFD, es_icmsstEFD, es_valconDFe, es_icmsDFe, es_icmsstDFe 
            FROM BaseDados WHERE ranking <= 20
            UNION ALL
            SELECT 'DEMAIS PARTICIPANTES (SOMA)' AS Part, 
              SUM(es_valconEFD), SUM(es_icmsEFD), SUM(es_icmsstEFD), 
              SUM(es_valconDFe), SUM(es_icmsDFe), SUM(es_icmsstDFe) 
            FROM BaseDados WHERE ranking > 20 HAVING COUNT(*) > 0
        )
        SELECT * FROM VisaoFinal 
        ORDER BY CASE WHEN Part = 'DEMAIS PARTICIPANTES (SOMA)' THEN 1 ELSE 0 END, ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-receitas-top'></a>Receitas (Top 20)")


    # 2a. Compras Insumos (Top 20)
    executar_e_formatar("""
        WITH BaseDados AS (
            SELECT Part, 
              SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
              SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
              ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
            FROM an_econ_base WHERE g1 = '2-Compras Insumos' GROUP BY cnpjPart14, Part
        ),
        VisaoFinal AS (
            SELECT Part, es_valconEFD, es_icmsEFD, es_icmsstEFD, es_valconDFe, es_icmsDFe, es_icmsstDFe 
            FROM BaseDados WHERE ranking <= 20
            UNION ALL
            SELECT 'DEMAIS PARTICIPANTES (SOMA)' AS Part, 
              SUM(es_valconEFD), SUM(es_icmsEFD), SUM(es_icmsstEFD), 
              SUM(es_valconDFe), SUM(es_icmsDFe), SUM(es_icmsstDFe) 
            FROM BaseDados WHERE ranking > 20 HAVING COUNT(*) > 0
        )
        SELECT * FROM VisaoFinal 
        ORDER BY CASE WHEN Part = 'DEMAIS PARTICIPANTES (SOMA)' THEN 1 ELSE 0 END, ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-compras-ins-top'></a>Compras Insumos (Top 20)")

    # 2b. Compras Consumo (Top 20)
    executar_e_formatar("""
        WITH BaseDados AS (
            SELECT Part, 
              SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
              SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
              ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
            FROM an_econ_base WHERE g1 = '3-Compras Consumo' GROUP BY cnpjPart14, Part
        ),
        VisaoFinal AS (
            SELECT Part, es_valconEFD, es_icmsEFD, es_icmsstEFD, es_valconDFe, es_icmsDFe, es_icmsstDFe 
            FROM BaseDados WHERE ranking <= 20
            UNION ALL
            SELECT 'DEMAIS PARTICIPANTES (SOMA)' AS Part, 
              SUM(es_valconEFD), SUM(es_icmsEFD), SUM(es_icmsstEFD), 
              SUM(es_valconDFe), SUM(es_icmsDFe), SUM(es_icmsstDFe) 
            FROM BaseDados WHERE ranking > 20 HAVING COUNT(*) > 0
        )
        SELECT * FROM VisaoFinal 
        ORDER BY CASE WHEN Part = 'DEMAIS PARTICIPANTES (SOMA)' THEN 1 ELSE 0 END, ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-compras-cons-top'></a>Compras Consumo (Top 20)")


    # 3. Ativo (Top 20)
    executar_e_formatar("""
        WITH BaseDados AS (
            SELECT Part, 
              SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
              SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
              ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
            FROM an_econ_base WHERE g1 = '4-Ativo' GROUP BY cnpjPart14, Part
        ),
        VisaoFinal AS (
            SELECT Part, es_valconEFD, es_icmsEFD, es_icmsstEFD, es_valconDFe, es_icmsDFe, es_icmsstDFe 
            FROM BaseDados WHERE ranking <= 20
            UNION ALL
            SELECT 'DEMAIS PARTICIPANTES (SOMA)' AS Part, 
              SUM(es_valconEFD), SUM(es_icmsEFD), SUM(es_icmsstEFD), 
              SUM(es_valconDFe), SUM(es_icmsDFe), SUM(es_icmsstDFe) 
            FROM BaseDados WHERE ranking > 20 HAVING COUNT(*) > 0
        )
        SELECT * FROM VisaoFinal 
        ORDER BY CASE WHEN Part = 'DEMAIS PARTICIPANTES (SOMA)' THEN 1 ELSE 0 END, ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-ativo-top'></a>Ativo (Top 20)")


    # 4. Entradas/Saídas 01z (Top 20)
    executar_e_formatar("""
        WITH BaseDados AS (
            SELECT Part, g2, g3 || ' ' || classe || ' ' || descri_simplif AS cfop_tipo,
              SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
              SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
              ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
            FROM an_econ_base WHERE g1 = '5-Entradas/Saídas' AND g2 = '01z - Produção - Outros' GROUP BY cnpjPart14, Part, g2, g3, classe, descri_simplif
        ),
        VisaoFinal AS (
            SELECT Part, g2, cfop_tipo, es_valconEFD, es_icmsEFD, es_icmsstEFD, es_valconDFe, es_icmsDFe, es_icmsstDFe 
            FROM BaseDados WHERE ranking <= 20
            UNION ALL
            SELECT 'DEMAIS ITENS (SOMA)' AS Part, '---' AS g2, '---' AS cfop_tipo, 
              SUM(es_valconEFD), SUM(es_icmsEFD), SUM(es_icmsstEFD), 
              SUM(es_valconDFe), SUM(es_icmsDFe), SUM(es_icmsstDFe) 
            FROM BaseDados WHERE ranking > 20 HAVING COUNT(*) > 0
        )
        SELECT * FROM VisaoFinal 
        ORDER BY CASE WHEN Part = 'DEMAIS ITENS (SOMA)' THEN 1 ELSE 0 END, ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-01z-top'></a>Entradas/Saídas - g2='01z - Produção - Outros' (Top 20)")


    # 5. Entradas/Saídas Outros Resumo (Top 20)
    executar_e_formatar("""
        WITH BaseDados AS (
            SELECT Part, g2, g3 || ' ' || classe || ' ' || descri_simplif AS cfop_tipo,
              SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
              SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
              ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
            FROM an_econ_base WHERE  g1 = '6-Outros' OR (g1 = '5-Entradas/Saídas' AND g2 <> '01z - Produção - Outros') GROUP BY cnpjPart14, Part, g2, g3, classe, descri_simplif
        ),
        VisaoFinal AS (
            SELECT Part, g2, cfop_tipo, es_valconEFD, es_icmsEFD, es_icmsstEFD, es_valconDFe, es_icmsDFe, es_icmsstDFe 
            FROM BaseDados WHERE ranking <= 20
            UNION ALL
            SELECT 'DEMAIS ITENS (SOMA)' AS Part, '---' AS g2, '---' AS cfop_tipo, 
              SUM(es_valconEFD), SUM(es_icmsEFD), SUM(es_icmsstEFD), 
              SUM(es_valconDFe), SUM(es_icmsDFe), SUM(es_icmsstDFe) 
            FROM BaseDados WHERE ranking > 20 HAVING COUNT(*) > 0
        )
        SELECT * FROM VisaoFinal 
        ORDER BY CASE WHEN Part = 'DEMAIS ITENS (SOMA)' THEN 1 ELSE 0 END, ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-outros-top'></a>Outros (Top 20)")


    # 6. Entradas/Saídas CFOP (Top 20)
    executar_e_formatar("""
        WITH BaseDados AS (
            SELECT classe, g1, g2 || ' ' || g3 || ' ' || descri_simplif AS cfop_tipo,
              SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
              SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
              ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
            FROM an_econ_base GROUP BY classe, g1, g2, g3, descri_simplif
        ),
        VisaoFinal AS (
            SELECT classe, g1, cfop_tipo, es_valconEFD, es_icmsEFD, es_icmsstEFD, es_valconDFe, es_icmsDFe, es_icmsstDFe 
            FROM BaseDados WHERE ranking <= 20
            UNION ALL
            SELECT '---' AS classe, 'DEMAIS ITENS (SOMA)' AS g1, '---' AS cfop_tipo, 
              SUM(es_valconEFD), SUM(es_icmsEFD), SUM(es_icmsstEFD), 
              SUM(es_valconDFe), SUM(es_icmsDFe), SUM(es_icmsstDFe) 
            FROM BaseDados WHERE ranking > 20 HAVING COUNT(*) > 0
        )
        SELECT * FROM VisaoFinal 
        ORDER BY CASE WHEN classe = '---' THEN 1 ELSE 0 END, ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-cfop-top'></a>Classes CFOP (Top 20)")



    # =========================================================================
    # PARTE 2: VISÃO ANALÍTICA COMPLETA (IGUAL AOS ORIGINAIS)
    # =========================================================================

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '1-Receitas' GROUP BY cnpjPart14 ORDER BY es_valconEFD DESC
    """, cursor, out_path, "<a id='sec-receitas-full'></a>Receitas (Completo)")

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '2-Compras Insumos' GROUP BY cnpjPart14 ORDER BY es_valconEFD
    """, cursor, out_path, "<a id='sec-compras-ins-full'></a>Compras Insumos (Completo)")

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '3-Compras Consumo' GROUP BY cnpjPart14 ORDER BY es_valconEFD
    """, cursor, out_path, "<a id='sec-compras-cons-full'></a>Compras Consumo (Completo)")

    executar_e_formatar("""
        SELECT Part, SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '4-Ativo' GROUP BY cnpjPart14 ORDER BY es_valconEFD
    """, cursor, out_path, "<a id='sec-ativo-full'></a>Ativo (Completo)")

    executar_e_formatar("""
        SELECT Part, g2, g3 || ' ' || classe || ' ' || descri_simplif AS cfop_tipo,
          SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '5-Entradas/Saídas' AND g2 = '01z - Produção - Outros' GROUP BY cnpjPart14, g2, g3, classe ORDER BY cnpjOrder, cnpjPart14, g2, g3, classe
    """, cursor, out_path, "<a id='sec-01z-full'></a>Entradas/Saídas E g2='01z - Produção - Outros' (Completo)")

    executar_e_formatar("""
        SELECT Part, g2, g3 || ' ' || classe || ' ' || descri_simplif AS cfop_tipo,
          SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe
        FROM an_econ_base WHERE g1 = '6-Outros' OR (g1 = '5-Entradas/Saídas' AND g2 <> '01z - Produção - Outros') GROUP BY cnpjPart14, g2, g3, classe ORDER BY cnpjOrder, cnpjPart14, g2, g3, classe
    """, cursor, out_path, "<a id='sec-outros-full'></a>Outros (Completo)")

    executar_e_formatar("""
        SELECT classe, g1, g2 || ' ' || g3 || ' ' || descri_simplif AS cfop_tipo,
          SUM(es_valconEFD) AS es_valconEFD, SUM(es_icmsEFD) AS es_icmsEFD, SUM(es_icmsstEFD) AS es_icmsstEFD,
          SUM(es_valconDFe) AS es_valconDFe, SUM(es_icmsDFe) AS es_icmsDFe, SUM(es_icmsstDFe) AS es_icmsstDFe,
          ROW_NUMBER() OVER (ORDER BY ABS(SUM(es_valconEFD)) DESC, ABS(SUM(es_valconDFe)) DESC) as ranking
        FROM an_econ_base GROUP BY classe, g1, g2, g3, descri_simplif ORDER BY ABS(es_valconEFD) DESC
    """, cursor, out_path, "<a id='sec-cfop-full'></a>Entradas/Saídas - CFOP (Completo)")



