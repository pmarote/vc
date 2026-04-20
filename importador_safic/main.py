import argparse
from pathlib import Path
from mdf2sqlite import convert_mdf_to_sqlite
from importador_safic import merge_safic_databases

def main():
    parser = argparse.ArgumentParser(description="Motor de Extração e Merge SAFIC")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Subcomando: convert
    p_convert = subparsers.add_parser("convert", help="Converte MDF inteiro para SQLite")
    p_convert.add_argument("--mdf", required=True, help="Caminho do arquivo .mdf")
    p_convert.add_argument("--ldf", required=True, help="Caminho do arquivo .ldf")
    p_convert.add_argument("--out", required=True, help="Caminho do .db3 de saída")
    p_convert.add_argument("--server", default=r"(localdb)\SaficV150", help="Instância do SQL Server")

    # Subcomando: merge
    p_merge = subparsers.add_parser("merge", help="Consolida arquivos SQLite de uma pasta em um único banco")
    p_merge.add_argument("--src", required=True, help="Pasta contendo os arquivos .db3 ou .sqlite extraídos")
    p_merge.add_argument("--out", required=True, help="Caminho completo do arquivo SQLite final (ex: ../var/osf.sqlite)")
    p_merge.add_argument("--all-tables", action="store_true", help="Importa TODAS as tabelas encontradas aplicando as regras de prefixo dinâmico")

    args = parser.parse_args()

    if args.command == "convert":
        # Resolve caminhos para evitar problemas com chamadas de outras pastas via 'vc'
        convert_mdf_to_sqlite(
            Path(args.mdf).resolve(), 
            Path(args.ldf).resolve(), 
            Path(args.out).resolve(), 
            args.server
        )
    
    elif args.command == "merge":
        # Resolve os caminhos para permitir chamadas relativas de qualquer lugar
        src_dir = Path(args.src).resolve()
        out_file = Path(args.out).resolve()
        
        # Repassa a nova flag all_tables
        merge_safic_databases(out_file, src_dir, all_tables=args.all_tables)

if __name__ == "__main__":
    main()