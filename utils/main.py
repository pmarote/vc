import argparse
import sys
import tomllib
from pathlib import Path

# Importa os módulos utilitários da mesma pasta
import dump_code
import sqlite_dump

# Resolve o caminho da raiz do projeto (sobe um nível: de 'utils' para 'vc')
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "config.toml"

def load_config() -> dict:
    """Lê o arquivo config.toml da raiz do projeto."""
    if not CONFIG_FILE.exists():
        print(f"[AVISO] Arquivo {CONFIG_FILE} não encontrado. Usando rotas padrão.")
        return {}
    with open(CONFIG_FILE, "rb") as f:
        return tomllib.load(f)

def main():
    config = load_config()
    
    # Captura a pasta 'var' do config, com fallback para 'var'
    var_dir_name = config.get("paths", {}).get("var", "var")
    var_dir = ROOT_DIR / var_dir_name

    parser = argparse.ArgumentParser(
        description=f"Toolkit de Utilitários ({config.get('app', {}).get('name', 'Vibe Code')})",
        epilog="💡 DICA: Para ver os parâmetros de um comando específico, use: main.py <comando> -h"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # === Comando: dump ===
    dump_parser = subparsers.add_parser("dump", help="Gera consolidado Markdown de código-fonte")
    dump_parser.add_argument("--root", default=str(ROOT_DIR), help="Pasta raiz (padrão: raiz do projeto)")
    dump_parser.add_argument("--dst", default=str(var_dir / "contexto_projeto.md"), help="Destino do arquivo MD")

    # === Comando: sqlite2md ===
    sql_parser = subparsers.add_parser("sqlite2md", help="Gera relatório Markdown de um arquivo SQLite")
    sql_parser.add_argument("--src", required=True, help="Arquivo .db3 ou .sqlite de origem (obrigatório)")
    # O --dst agora é opcional, pois ele sabe onde fica a pasta var graças ao config.toml
    sql_parser.add_argument("--dst", default=str(var_dir / "relatorio_banco.md"), help="Arquivo .md de saída")
    sql_parser.add_argument("--limit", type=int, default=5, help="Linhas de amostra por tabela (padrão=5)")
    sql_parser.add_argument("--name", help="Filtra por nome (aceita % como curinga, ex: cfop%)")

    args = parser.parse_args()

    if args.command == "dump":
        dump_code.run_dump(Path(args.root).resolve(), Path(args.dst).resolve())
    elif args.command == "sqlite2md":
        sqlite_dump.run_sqlite_dump(
            Path(args.src).resolve(), 
            Path(args.dst).resolve(), 
            limit=args.limit, 
            name_pattern=args.name
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()