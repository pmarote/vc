# sfiaweb/main.py
"""
sfiaweb — Interface web local para auditoria fiscal.
Motor: FastAPI servindo relatórios .md e executando gatilhos.

Uso:
  uv run main.py serve
  uv run main.py serve --port 5678
"""
import argparse
import sys

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