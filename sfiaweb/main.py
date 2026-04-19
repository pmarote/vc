import argparse
import sys
import tomllib
from pathlib import Path

# Resolve o caminho da raiz do projeto (vc/)
ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT_DIR / "var" / "sfia_config.toml"

def validar_ambiente():
    """Verifica se a pasta de trabalho existe."""
    if not CONFIG_FILE.exists():
        print(f"\n❌ ERRO: Arquivo de configuração não encontrado em: {CONFIG_FILE}")
        print("💡 DICA: Você precisa rodar o 'build' no microapp 'sfia_safic' primeiro.")
        sys.exit(1)
    
    with open(CONFIG_FILE, "rb") as f:
        config = tomllib.load(f)
        work_dir = Path(config.get("work_dir", ""))
        
        if not work_dir.exists():
            print(f"\n❌ ERRO: A pasta raiz '{work_dir}' não foi encontrada.")
            sys.exit(1)
    
    return True

def main():
    parser = argparse.ArgumentParser(description="VC - sfiaweb (Servidor de Interface e Relatórios)")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando 'serve'
    serve_parser = subparsers.add_parser("serve", help="Inicia o servidor web local")
    serve_parser.add_argument(
        "--port", 
        type=int, 
        default=5678, 
        help="Porta do servidor (padrão: 5678)"
    )

    args = parser.parse_args()

    if args.command == "serve":
        # Importa apenas na hora de usar, economiza tempo de boot se houver outros comandos no futuro
        from server import start_server
        start_server(port=args.port)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()