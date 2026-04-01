import sqlite3
import pandas as pd
from pathlib import Path
import sys

# =========================================================================
# MAPEAMENTO DE IMPORTAÇÃO (Excel -> SQLite)
# Estrutura: "Nome do Arquivo": {"Nome da Aba": "Nome_da_Tabela"}
# =========================================================================
PLANILHAS_MAPEAMENTO = {
    "PWBI_C03_Fichas 3A_3B_3C Movimentação - Custeio.xlsx": {
        "Fichas_3 Custeio": "Fichas_3_Custeio",
        "Ficha_1C Custeio": "Ficha_1C_Custeio"
    },
    "Tabelas_gerais_v4.xlsx": {
        "IVA_mediana": "tgIVA_mediana",
        "CFOP": "tgCFOP",
        "NCM": "tgNCM",
        "Ufesp": "tgUFesp"
    },
    "PWBI_C01_Comparação Arquivos e-CredAc x GIAs - Custeio.xlsx": {
        "eCredAc - CFOP": "eCredAc_CFOP",
        "Cadesp": "Cadesp",
        "Arquivos transmitidos": "Arquivos_transmitidos",
        "Pedidos eCredAc": "Pedidos_eCredAc",
        "GIA - CFOP": "GIA_CFOP",
        "Comparação Arquivos x GIA": "Comparacao_Arquivos_GIA",
        "Código Legal": "Codigo_Legal",
        "Estorno Créditos": "Estorno_Creditos"
    },
    "PWBI_C08_Lancamentos_Complementares_-_Custeio.xlsx": {
        "Lancamentos_complementares": "Lancamentos_complementares",
        "Resumo lancamentos complementar": "Resumo_lancamentos_complementar",
        "Resumo por item": "Resumo_por_item"
    }
}

def construir_banco_siaCredAc(src_dir: Path, db_siaCredAc: Path):
    """Constrói o banco de dados SIA_CredAc a partir de planilhas Excel."""
    
    # 1. Prepara o banco de dados (remove o antigo se existir)
    if db_siaCredAc.exists():
        db_siaCredAc.unlink()
        
    # Garante que a pasta de destino (ex: var/) exista
    db_siaCredAc.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_siaCredAc)
    
    # =========================================================================
    # PASSO 1: Importação em Lote das Planilhas Mapeadas
    # =========================================================================
    for nome_planilha, abas in PLANILHAS_MAPEAMENTO.items():
        arquivo_excel = src_dir / nome_planilha
        
        if not arquivo_excel.exists():
            print(f" [ERRO FATAL] Planilha não encontrada: {nome_planilha}")
            print(f" Verifique se ela está na pasta: {src_dir}")
            conn.close()
            sys.exit(1)
            
        print(f"\n ➔ Lendo planilha: {nome_planilha}")
        
        try:
            for nome_aba, nome_tabela in abas.items():
                print(f"    - Importando aba: '{nome_aba}' -> Tabela: '{nome_tabela}'...")
                
                # Lê a aba específica
                df = pd.read_excel(arquivo_excel, sheet_name=nome_aba)
                
                # Salva no SQLite
                df.to_sql(nome_tabela, conn, if_exists="replace", index=False)
                
        except ValueError as e:
            print(f" [ERRO] A aba '{nome_aba}' não foi encontrada no arquivo '{nome_planilha}'.\n Detalhes: {e}")
            conn.close()
            sys.exit(1)
        except Exception as e:
            print(f" [ERRO] Ocorreu uma falha ao ler o arquivo '{nome_planilha}'.\n Detalhes: {e}")
            conn.close()
            sys.exit(1)

    # =========================================================================
    # PRÓXIMOS PASSOS (Criação de Views, Índices e Tabelas Auxiliares)
    # =========================================================================
    # (Inserir código DDL aqui)

    conn.commit()
    conn.close()
    print("\n ✅ Carga das tabelas iniciais finalizada com sucesso.")