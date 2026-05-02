import sqlite3
from pathlib import Path

# Mapa de tabelas mantido intacto
MAPA_TABELAS = {
    "dbo_Versao": "_dbo_Versao",
    "dbo_auditoria": "_dbo_auditoria",
    "fiscalCadesp_Cadastro": "_fiscalCadesp_Cadastro",
    "fiscalCadesp_HistoricoRegimeDeApuracao": "_fiscalCadesp_HistoricoRegimeDeApuracao",
    "fiscal_ApuracaoDeIcmsPelaEfd": "_fiscal_ApuracaoDeIcmsPelaEfd",
    "fiscal_ApuracaoDeIcmsPelaGia": "_fiscal_ApuracaoDeIcmsPelaGia",
    "fiscal_CfIcms": "_fiscal_CfIcms",
    "fiscal_Classificacao": "_fiscal_Classificacao",
    "fiscal_ComparacaoGiaEfdPorCfop": "_fiscal_ComparacaoGiaEfdPorCfop",
    "fiscal_CteOs0000": "_fiscal_CteOs0000",
    "fiscal_Efd0000": "_fiscal_Efd0000",
    "fiscal_Efd0200": "_fiscal_Efd0200",
    "fiscal_Efd0205": "_fiscal_Efd0205",
    "fiscal_Efd0206": "_fiscal_Efd0206",
    "fiscal_EfdCte": "_fiscal_EfdCte",
    "fiscal_EfdE110": "_fiscal_EfdE110",
    "fiscal_EfdE111": "_fiscal_EfdE111",
    "fiscal_EfdE111Descr": "_fiscal_EfdE111Descr",
    "fiscal_EfdE112": "_fiscal_EfdE112",
    "fiscal_EfdE112Descr": "_fiscal_EfdE112Descr",
    "fiscal_EfdE113": "_fiscal_EfdE113",
    "fiscal_EfdE115": "_fiscal_EfdE115",
    "fiscal_EfdE115Descr": "_fiscal_EfdE115Descr",
    "fiscal_EfdE116": "_fiscal_EfdE116",
    "fiscal_EfdE116Descr": "_fiscal_EfdE116Descr",
    "fiscal_EfdNfe": "_fiscal_EfdNfe",
    "fiscal_EfdSat": "_fiscal_EfdSat",
    "fiscal_Evt0000": "_fiscal_Evt0000",
    "fiscal_Fci0000": "_fiscal_Fci0000",
    "fiscal_ItemServicoDeclarado": "_fiscal_ItemServicoDeclarado",
    "fiscal_Nfce0000": "_fiscal_Nfce0000",
    "fiscal_Nfe0000": "_fiscal_Nfe0000",
    "fiscal_NatOp": "_fiscal_NatOp",
    "fiscal_OcorrenciaCadesp": "_fiscal_OcorrenciaCadesp",
    "fiscal_ParamConsultaDoc": "_fiscal_ParamConsultaDoc",
    "fiscal_ParamConsultaDocClassificacao": "_fiscal_ParamConsultaDocClassificacao",
    "fiscal_ParticipanteDeclarado": "_fiscal_ParticipanteDeclarado",
    "fiscal_Sat0000": "_fiscal_Sat0000",
    "fiscal_Efd0190": "_fiscal_Efd0190",
    "fiscal_HistoricoDeIe": "_fiscal_HistoricoDeIe",
    "imp_ReferenciasSelecionadasNaImportacao": "_imp_ReferenciasSelecionadasNaImportacao",
    "procFisc_ReferenciaDaOsf": "_procFisc_ReferenciaDaOsf",
    "fiscal_DocNum": "Dfe_fiscal_DocNum",
    "fiscal_Efd0150": "Dfe_fiscal_Efd0150",
    "fiscal_EfdC100": "Dfe_fiscal_EfdC100",
    "fiscal_EfdC100Detalhe": "Dfe_fiscal_EfdC100Detalhe",
    "fiscal_EfdC110": "Dfe_fiscal_EfdC110",
    "fiscal_EfdC170": "Dfe_fiscal_EfdC170",
    "fiscal_EfdC190": "Dfe_fiscal_EfdC190",
    "fiscal_EfdC195": "Dfe_fiscal_EfdC195",
    "fiscal_EfdC197": "Dfe_fiscal_EfdC197",
    "fiscal_EfdC800": "Dfe_fiscal_EfdC800",
    "fiscal_EfdD100": "Dfe_fiscal_EfdD100",
    "fiscal_EfdD100Detalhe": "Dfe_fiscal_EfdD100Detalhe",
    "fiscal_EfdD190": "Dfe_fiscal_EfdD190",
    "fiscal_EfdG110": "Dfe_fiscal_EfdG110",
    "fiscal_EfdG125": "Dfe_fiscal_EfdG125",
    "fiscal_EfdG126": "Dfe_fiscal_EfdG126",
    "fiscal_EfdG130": "Dfe_fiscal_EfdG130",
    "fiscal_EfdG140": "Dfe_fiscal_EfdG140",
    "fiscal_EfdH005": "Dfe_fiscal_EfdH005",
    "fiscal_EfdH010": "Dfe_fiscal_EfdH010",
    "fiscal_EfdH010Descr": "Dfe_fiscal_EfdH010Descr",
    "fiscal_EfdH010Posse": "Dfe_fiscal_EfdH010Posse",
    "fiscal_EfdH010Prop": "Dfe_fiscal_EfdH010Prop",
    "fiscal_Evt100": "Dfe_fiscal_Evt100",
    "fiscal_Evt101": "Dfe_fiscal_Evt101",
    "fiscal_Evt102": "Dfe_fiscal_Evt102",
    "fiscal_Evt103": "Dfe_fiscal_Evt103",
    "fiscal_Evt104": "Dfe_fiscal_Evt104",
    "fiscal_Evt105": "Dfe_fiscal_Evt105",
    "fiscal_Evt106": "Dfe_fiscal_Evt106",
    "fiscal_Evt107": "Dfe_fiscal_Evt107",
    "fiscal_Evt111": "Dfe_fiscal_Evt111",
    "fiscal_Evt113": "Dfe_fiscal_Evt113",
    "fiscal_Evt114": "Dfe_fiscal_Evt114",
    "fiscal_Evt115": "Dfe_fiscal_Evt115",
    "fiscal_Evt119": "Dfe_fiscal_Evt119",
    "fiscal_Evt120": "Dfe_fiscal_Evt120",
    "fiscal_Evt121": "Dfe_fiscal_Evt121",
    "fiscal_Evt122": "Dfe_fiscal_Evt122",
    "fiscal_Evt123": "Dfe_fiscal_Evt123",
    "fiscal_Evt127": "Dfe_fiscal_Evt127",
    "fiscal_Evt131": "Dfe_fiscal_Evt131",
    "fiscal_Evt132": "Dfe_fiscal_Evt132",
    "fiscal_Evt189": "Dfe_fiscal_Evt189",
    "fiscal_Evt190": "Dfe_fiscal_Evt190",
    "fiscal_Evt191": "Dfe_fiscal_Evt191",
    "fiscal_Evt192": "Dfe_fiscal_Evt192",
    "fiscal_Evt291": "Dfe_fiscal_Evt291",
    "fiscal_Evt292": "Dfe_fiscal_Evt292",
    "fiscal_NfceC100": "Dfe_fiscal_NfceC100",
    "fiscal_NfeC100": "Dfe_fiscal_NfeC100",
    "fiscal_NfeC100Detalhe": "Dfe_fiscal_NfeC100Detalhe",
    "fiscal_NfeC101": "Dfe_fiscal_NfeC101",
    "fiscal_NfeC102": "Dfe_fiscal_NfeC102",
    "fiscal_NfeC103": "Dfe_fiscal_NfeC103",
    "fiscal_NfeC104": "Dfe_fiscal_NfeC104",
    "fiscal_NfeC106": "Dfe_fiscal_NfeC106",
    "fiscal_NfeC110": "Dfe_fiscal_NfeC110",
    "fiscal_NfeC112": "Dfe_fiscal_NfeC112",
    "fiscal_NfeC115": "Dfe_fiscal_NfeC115",
    "fiscal_NfeC116": "Dfe_fiscal_NfeC116",
    "fiscal_NfeC119": "Dfe_fiscal_NfeC119",
    "fiscal_NfeC127": "Dfe_fiscal_NfeC127",
    "fiscal_NfeC130": "Dfe_fiscal_NfeC130",
    "fiscal_NfeC140": "Dfe_fiscal_NfeC140",
    "fiscal_NfeC141": "Dfe_fiscal_NfeC141",
    "fiscal_NfeC160": "Dfe_fiscal_NfeC160",
    "fiscal_NfeC170": "Dfe_fiscal_NfeC170",
    "fiscal_NfeC170InfProd": "Dfe_fiscal_NfeC170InfProd",
    "fiscal_NfeC170IpiNaoTrib": "Dfe_fiscal_NfeC170IpiNaoTrib",
    "fiscal_NfeC170IpiTrib": "Dfe_fiscal_NfeC170IpiTrib",
    "fiscal_NfeC170Resumo": "Dfe_fiscal_NfeC170Resumo",
    "fiscal_NfeC170Tributos": "Dfe_fiscal_NfeC170Tributos",
    "fiscal_NfeC176": "Dfe_fiscal_NfeC176",
    "fiscal_NfeC182": "Dfe_fiscal_NfeC182",
    "fiscal_NfeC183": "Dfe_fiscal_NfeC183",
    "fiscal_NfeC200": "Dfe_fiscal_NfeC200",
    "fiscal_NfeC200Detalhe": "Dfe_fiscal_NfeC200Detalhe",
    "fiscal_NfeC201": "Dfe_fiscal_NfeC201",
    "fiscal_NfeC202": "Dfe_fiscal_NfeC202",
    "fiscal_NfeC203": "Dfe_fiscal_NfeC203",
    "fiscal_NfeC205": "Dfe_fiscal_NfeC205",
    "fiscal_NfeC206": "Dfe_fiscal_NfeC206",
    "fiscal_NfeC207": "Dfe_fiscal_NfeC207",
    "fiscal_NfeC209": "Dfe_fiscal_NfeC209",
    "fiscal_NfeC211": "Dfe_fiscal_NfeC211",
    "fiscal_NfeC211Resumo": "Dfe_fiscal_NfeC211Resumo",
    "fiscal_NfeC211infAd": "Dfe_fiscal_NfeC211infAd",
    "fiscal_NfeC212": "Dfe_fiscal_NfeC212",
    "fiscal_NfeC215": "Dfe_fiscal_NfeC215",
    "fiscal_NfeC217": "Dfe_fiscal_NfeC217",
    "fiscal_NfeC219": "Dfe_fiscal_NfeC219",
    "fiscal_NfeC225": "Dfe_fiscal_NfeC225",
    "fiscal_NfeC227": "Dfe_fiscal_NfeC227",
    "fiscal_Sat100": "Dfe_fiscal_Sat100",
    "fiscal_Sat104": "Dfe_fiscal_Sat104",
    "fiscal_DocAtributos": "DocAtrib_fiscal_DocAtributos",
    "fiscal_DocAtributosDeApuracao": "DocAtrib_fiscal_DocAtributosDeApuracao",
    "fiscal_DocAtributosItem": "DocAtrib_fiscal_DocAtributosItem",
    "fiscal_DocAtributosPart": "DocAtrib_fiscal_DocAtributosPart",
    "fiscal_DocClassificado": "DocAtrib_fiscal_DocClassificado",
}

# Tabelas muito grandes (resumo de várias outras) que ocupam cerca de 65% do SQLite final
TABELAS_GIGANTES_DESCARTAVEIS = {
    "fiscal_DocAtributosItemCompleto",
    "fiscal_DocAtributosDeApuracaoCompleto",
    "fiscal_DocAtributosEvt"
}

def merge_safic_databases(out_db_path: Path, source_dir: Path, all_tables: bool = False, optimized: bool = False):
    print(f"\n🎯 Iniciando Consolidação Safic")
    print(f"📂 Lendo diretório: {source_dir.resolve()}")
    
    # Se o usuário escolheu o modo otimizado, ele engloba a ideia de "all_tables", mas com bloqueios
    if optimized:
        print(f"⚡ MODO OTIMIZADO ATIVO: Importando todas as tabelas (regra dinâmica), EXCETO tabelas gigantes de _DocAtrib_.")
        print(f"   (Motivo: Reduz ~65% do tamanho do banco. Estas tabelas são resumos e não possuem dados novos).")
        all_tables = True 
    elif all_tables:
        print(f"⚠️ MODO EXPANDIDO: Importando TODAS as tabelas com regras dinâmicas.")
    
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"❌ Diretório não encontrado: {source_dir}")
        return

    # Busca por db3 e sqlite na pasta
    db_paths = list(source_dir.glob("*.db3")) + list(source_dir.glob("*.sqlite"))
    
    if not db_paths:
        print(f"⚠️ Nenhum arquivo .db3 ou .sqlite encontrado em {source_dir}")
        return

    # Garante que a pasta de destino exista (ex: var/)
    out_db_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"💾 Arquivo final será: {out_db_path.resolve()}")
    conn_final = sqlite3.connect(out_db_path)
    cursor_final = conn_final.cursor()

    for db_path in db_paths:
        print(f"\n📄 Processando: {db_path.name}")
        cursor_final.execute(f"ATTACH DATABASE '{db_path.resolve()}' AS origem;")
        
        # Pega as tabelas que existem neste banco específico
        cursor_final.execute("SELECT name FROM origem.sqlite_master WHERE type='table';")
        tabelas_origem = [row[0] for row in cursor_final.fetchall()]
        
        for tabela_original in tabelas_origem:
            tabela_destino = None
            
            # Bloqueio imediato se estivermos no modo otimizado e for uma tabela gigante do _DocAtrib_
            if optimized and tabela_original in TABELAS_GIGANTES_DESCARTAVEIS:
                print(f"   [!] Ignorando tabela gigante: {tabela_original}")
                continue
                
            # 1. Verifica primeiro o override explícito (MAPA_TABELAS)
            if tabela_original in MAPA_TABELAS:
                tabela_destino = MAPA_TABELAS[tabela_original]
                
            # 2. Se não achou e a flag --all-tables estiver ativada, aplica a regra dinâmica
            elif all_tables:
                if "_DocAtrib_" in db_path.name:
                    tabela_destino = f"DocAtrib_{tabela_original}"
                elif "_Dfe_" in db_path.name:
                    tabela_destino = f"Dfe_{tabela_original}"
                else:
                    tabela_destino = f"_{tabela_original}"
            
            # Se a tabela ganhou um destino (pelo mapa ou pela regra), faz o merge
            if tabela_destino:
                # Verifica se a tabela já foi criada no banco final
                cursor_final.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (tabela_destino,))
                existe = cursor_final.fetchone()
                
                if not existe:
                    print(f"   [+] Criando e importando: {tabela_destino}")
                    cursor_final.execute(f"CREATE TABLE {tabela_destino} AS SELECT * FROM origem.[{tabela_original}];")
                else:
                    print(f"   [>] Fazendo merge (append): {tabela_destino}")
                    cursor_final.execute(f"INSERT INTO {tabela_destino} SELECT * FROM origem.[{tabela_original}];")
                    
                conn_final.commit()
        
        cursor_final.execute("DETACH DATABASE origem;")
        print("   Concluído!")

    conn_final.close()
    print(f"\n✅ Consolidação finalizada com sucesso!")