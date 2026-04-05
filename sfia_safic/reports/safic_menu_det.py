"""
Relatório Safic Menu Detalhes — top-N por idClassificacao com UNION de demais itens.
"""
from ._helpers import executar_e_formatar, iniciar_relatorio

# Template reutilizável para todos os itens de menu
_MENU_TOP_TEMPLATE = """
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


def gerar_rel_safic_menu_det(cursor, out_path):
    iniciar_relatorio(out_path, "Análises do Safic - Detalhes")

    def executar_menu_det(classif, titulo, top_n="18", order_by="sum(vl_docDFe) DESC", campos_adic=""):
        query = _MENU_TOP_TEMPLATE \
            .replace("{classif}", classif) \
            .replace("{top_n}", top_n) \
            .replace("{order_by}", order_by) \
            .replace("{campos_adic}", campos_adic)
        executar_e_formatar(query, cursor, out_path, titulo)

    executar_menu_det("[1]", "[1] Documentos escriturados cancelados")

    # Menus estáticos exclusivos: [2] e [9]
    executar_e_formatar("""
        SELECT tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops, count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(vl_docDFe) AS vl_docDFe, sum(vl_docEFD) AS vl_docEFD,
        sum(dif_icmsstSP) AS dif_icmsstSP, sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD
        FROM (SELECT * FROM chaveNroTudao WHERE ChNrClassifs LIKE '%[2]%' ORDER BY numero) GROUP BY tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops ORDER BY dif_icms
    """, cursor, out_path, "[2] E 1.13 - documentos escriturados em duplicidade")

    executar_e_formatar("""
        SELECT tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops, count(numero) AS qtd, sum(dif_vl_doc) AS dif_vl_doc, sum(dif_icms) AS dif_icms, sum(dif_icmsstSP) AS dif_icmsstSP, sum(vl_icmsDFe) AS vl_icmsDFe, sum(vl_icmsEFD) AS vl_icmsEFD, sum(vl_icmsstSP_DFe) AS vl_icmsstSP_DFe, sum(vl_icmsstSP_EFD) AS vl_icmsstSP_EFD
        FROM (SELECT * FROM chaveNroTudao WHERE ChNrClassifs LIKE '%[9]%' ORDER BY numero) GROUP BY tp_codSit, tp_oper, Part, ChNrOrigem, ChNrCfops ORDER BY dif_icms
    """, cursor, out_path, "[9] E 1.17 - operações realizadas com fornecedores com a inscrição suspensa, inapta, baixada ou nula no cadastro de contribuintes")

    # Demais menus via template
    executar_menu_det("[10]",  "[10] E 1.9 - crédito indevido (antecipado): escrituração antes da data de entrada", order_by="sum(dif_icms)")
    executar_menu_det("[12]",  "[12] E 1.14 - crédito de ICMS operação própria maior que o destacado no documento fiscal", order_by="sum(dif_icms)")
    executar_menu_det("[13]",  "[13] S 1.4 - débito a menor: débitos de ICMS OP escriturados a menor que no destaque do documento fiscal", order_by="sum(dif_icms) DESC")
    executar_menu_det("[14]",  "[14] E 1.20 - documentos de entrada não escriturados")
    executar_menu_det("[15]",  "[15] S 1.1 - inconsistência na escrituração: saídas não escrituradas")
    executar_menu_det("[16]",  "[16] S 1.1 - E 1.6 - simulação de entrada: documentos CANCELADOS escriturados como Válidos, mas são entradas SEM crédito")
    executar_menu_det("[18]",  "[18] S 1.14 - documentos fiscais cancelados escriturados como regulares")
    executar_menu_det("[20]",  "[20] NFes, CTes, NFCes e CFe SATs CANCELADOS destinados ao contribuinte auditado")
    executar_menu_det("[21]",  "[21] NFes, CTes, NFCes e CFe SATs sem EFD entregue no período")
    executar_menu_det("[25]",  "[25] Operações de entrada com ST")
    executar_menu_det("[26]",  "[26] Operações de saída com ST")
    executar_menu_det("[35]",  "[35] CIAP 1.2 - saída de bens do ativo imobilizado")
    executar_menu_det("[36]",  "[36] CIAP 1.3 - apropriação de crédito de ativo imobilizado")
    executar_menu_det("[37]",  "[37] E 3.3 - análise de operações com materiais de uso e consumo")
    executar_menu_det("[38]",  "[38] ES 1.3 - análise de operações com armazéns gerais")
    executar_menu_det("[39]",  "[39] E 2.6 - análise de crédito de fornecedores enquadrados no Regime de apuração do Simples Nacional")
    executar_menu_det("[40]",  "[40] operações com a ZFM e as ALC")
    executar_menu_det("[41]",  "[41] operações com energia elétrica")
    executar_menu_det("[42]",  "[42] operações de aquisição de transporte")
    executar_menu_det("[43]",  "[43] operações de serv. de comunicação")
    executar_menu_det("[46]",  "[46] ES 1.1 - análise de operações com industrialização")
    executar_menu_det("[48]",  "[48] E 1.17 - operações realizadas com fornecedores com a inscrição suspensa...")
    executar_menu_det("[53]",  "[53] 9.3 l) margem de lucro ou preço de varejo inferior ao previsto na legislação nas operações de substituição tributária")
    executar_menu_det("[54]",  "[54] item 39.4: análise de saídas interestaduais com ST item 39.9: análise de situação cadastral do adquirente de saídas interestaduais com ST")
    executar_menu_det("[56]",  "[56] S 1.9 - operações com destinatários inscritos no cadastro de contribuintes, com situação cadastral inativa")
    executar_menu_det("[62]",  "[62] S 1.8 - operações com destinatários incluídos no cadastro de inidôneos")
    executar_menu_det("[63]",  "[63] S 1.8 - operações com destinatários incluídos no cadastro de inidôneos")
    executar_menu_det("[64]",  "[64] E 1.18 - crédito de operações próprias com substituição tributária")
    executar_menu_det("[65]",  "[65] E 1.4 - simulação de entrada: entrada escriturada, sem crédito, a partir de documento eletrônico sem relação com o contribuinte auditado")
    executar_menu_det("[67]",  "[67] S 2.6 - operações com destinatários localizados no Estado, mas não inscritos no cadastro de contribuintes")
    executar_menu_det("[69]",  "[69] E 1.16 - crédito indevido: entrada escriturada com CFOP que geralmente não aceita crédito", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    executar_menu_det("[70]",  "[70] CIAP 1.1 - entrada de bens para o ativo imobilizado")
    executar_menu_det("[71]",  "[71] E 3.1 - análise de entradas interestaduais de produtos importados, com alíquota do imposto superior a 4%", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
    executar_menu_det("[72]",  "[72] E 3.2 - análise de crédito em operações com devolução de mercadorias")
    executar_menu_det("[73]",  "[73] ES 1.4 - análise de operações com CFOP 1949 / 2949 / 3949 / 5949 / 6949 / 7949")
    executar_menu_det("[77]",  "[77] S 2.5 - operações interestaduais com alíquota de 4%")
    executar_menu_det("[82]",  "[82] ES 1.6 - análise de operações envolvendo demonstração")
    executar_menu_det("[85]",  "[85] S 2.7 - operações de remessas para a Zona Franca de Manaus (ZFM) e Área de Livre Comércio (ALC)")
    executar_menu_det("[90]",  "[90] E 3.4 - análise de operações de devolução de mercadorias de maior valor")
    executar_menu_det("[98]",  "[98] E 1.5 - crédito indevido: documentos CANCELADOS escriturados COM crédito")
    executar_menu_det("[99]",  "[99] E 1.7 - crédito indevido: documento fiscal de saída escriturado como entrada com crédito", order_by="sum(vl_icmsEFD) DESC, sum(vl_icmsDFe) DESC")
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
    executar_menu_det("[119]", "[119] S 1.17 - operações de saída escrituradas, sem débito, de documento com manifestação do destinatário negando a operação")
    executar_menu_det("[284]", "[284] S 1.23 - operações internas de saída para contribuinte sem escrituração na EFD do participante")
    executar_menu_det("[285]", "[285] S 1.24 - operações interestaduais de saída para contribuinte sem escrituração na EFD do participante")
    executar_menu_det("[367]", "[367] E 2.2 - análise de alíquotas de operações internas")
    executar_menu_det("[368]", "[368] E 2.3 - análise de alíquotas de operações interestaduais")
    executar_menu_det("[371]", "[371] E 4.0 - análise de devoluções com lig. de ítem emissão própria")
    executar_menu_det("[372]", "[372] 4.0 - análise de devoluções com lig. de ítem emissão terceiros")
    executar_menu_det("[374]", "[374] E 4.2 - análise de devoluções sem lig. de ítem emissão terceiros")
    executar_menu_det("[375]", "[375] E 2.2 - análise de alíquotas de operações internas", campos_adic="DFeAliqs, EfdAliqs, ")
    executar_menu_det("[376]", "[376] E 2.4 - análise de alíquota em operações de transporte", campos_adic="DFeAliqs, EfdAliqs, ")
