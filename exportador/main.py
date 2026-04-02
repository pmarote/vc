import argparse
import sqlite3
import sys
from pathlib import Path
from exporter import export_excel, export_markdown, export_tsv

def resolve_sql(sql_input: str) -> str:
    """Lê a query do arquivo ou da própria string informada."""
    if sql_input.lower().endswith('.sql'):
        sql_path = Path(sql_input).resolve()
        if not sql_path.exists():
            print(f"[ERRO] Arquivo SQL não encontrado: {sql_path}")
            sys.exit(1)
        return sql_path.read_text(encoding='utf-8')
    return sql_input

def main():
    parser = argparse.ArgumentParser(description="Exportador de Dados Vibe Code")
    parser.add_argument("--db", required=True, help="Caminho do banco SQLite principal")
    parser.add_argument("--sql", required=True, help="Query SQL direta ou caminho para arquivo .sql")
    parser.add_argument("--out", required=True, help="Arquivo de saída (.xlsx, .txt, .md)")
    
    # Novo parâmetro: aceita dois argumentos (caminho e alias) e pode ser repetido
    parser.add_argument("--attach", nargs=2, action="append", metavar=("CAMINHO_DB", "ALIAS"), 
                        help="Banco adicional para ATTACH e seu ALIAS (ex: --attach ../data/osf.db3 osf)")

    args = parser.parse_args()

    db_path = Path(args.db).resolve()
    out_path = Path(args.out).resolve()
    sql_query = resolve_sql(args.sql)

    if not db_path.exists():
        print(f"[ERRO] Banco principal não encontrado: {db_path}")
        sys.exit(1)

    ext = out_path.suffix.lower()
    
    print(f"🔌 Conectando ao banco principal: {db_path.name}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- Lógica de ATTACH ---
        attach_info = []
        if args.attach:
            for attach_path_str, alias in args.attach:
                attach_path = Path(attach_path_str).resolve()
                if not attach_path.exists():
                    print(f"[ERRO] Banco para attach não encontrado: {attach_path}")
                    sys.exit(1)
                
                cursor.execute(f"ATTACH DATABASE '{attach_path}' AS {alias};")
                print(f"🔗 Banco anexado (ATTACH): {attach_path.name} AS {alias}")
                attach_info.append(f"{alias} ({attach_path.name})")

        print("🚀 Executando Query...")
        cursor.execute(sql_query)
        
        print(f"📦 Exportando para {ext}...")
        
        if ext == '.xlsx':
            linhas = export_excel(cursor, out_path)
        elif ext == '.md':
            anexos_str = ", ".join(attach_info) if attach_info else ""
            linhas = export_markdown(cursor, out_path, sql_query, db_path=db_path.name, attachments=anexos_str)
        elif ext in ['.txt', '.tsv']:
            linhas = export_tsv(cursor, out_path)
        else:
            print(f"[ERRO] Extensão '{ext}' não suportada. Use .xlsx, .txt ou .md")
            sys.exit(1)

        print(f"✅ Sucesso! {linhas} linhas salvas em: {out_path.name}")
        conn.close()

    except sqlite3.OperationalError as e:
        print(f"[ERRO SQL] Falha na consulta ou no attach: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERRO FATAL] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()