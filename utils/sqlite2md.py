"""
utils/sqlite2md.py

Utilitário Standalone: Exportador de SQLite para Markdown
Utiliza a biblioteca central do VC (core.lib.to_markdown).
"""
import argparse
import sqlite3
import sys
from pathlib import Path

# IMPORTANTE: Importando a biblioteca central e o exportador
import core.lib.vccore as vc
from core.lib.to_markdown import export_markdown

def main():
    parser = argparse.ArgumentParser(description="Utilitário VC - Exportador Direto de SQLite para Markdown")
    parser.add_argument("--db", required=True, help="Caminho do banco de dados")
    parser.add_argument("--sql", required=True, help="Query SQL ou caminho para arquivo .sql")
    parser.add_argument("--out", required=True, help="Caminho do arquivo de saída .md")
    parser.add_argument("--title", default="", help="Título do relatório")
    parser.add_argument("--debug", action="store_true", help="Se definido, exibe metadados e SQL no topo")
    args = parser.parse_args()

    try:
        sql_file_name = ""
        sql_content = args.sql
        sql_path = Path(args.sql)
        
        # Verifica se o que foi passado no --sql é um arquivo ou a query direta
        if sql_path.exists() and sql_path.is_file():
            sql_file_name = sql_path.name
            sql_content = sql_path.read_text(encoding="utf-8")

        conn = sqlite3.connect(args.db)
        cursor = conn.cursor()
        
        vc.log("Executando a consulta e convertendo os dados...", level="INFO")
        # Executa a query
        cursor.execute(sql_content)
        
        # Chama a exportação da biblioteca passando o estado do debug (show_meta)
        export_markdown(
            cursor=cursor, 
            out_path=args.out, 
            sql_query=sql_content, 
            db_path=args.db,
            sql_file=sql_file_name,
            title=args.title,
            show_meta=args.debug
        )
        
        conn.close()
        vc.log(f"Relatório gerado com sucesso em: {args.out}", level="INFO")
        print(f"{vc.Colors.GREEN}✅ Operação concluída.{vc.Colors.RESET}")
        
    except Exception as e:
        vc.log(f"Erro ao gerar relatório standalone: {e}", level="ERROR")
        sys.exit(1)

if __name__ == "__main__":
    main()