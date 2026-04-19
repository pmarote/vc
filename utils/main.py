import argparse
import sys
import subprocess
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(
        description="🛠️ Toolkit de Utilitários do VC Workspace.\nEsta pasta contém scripts independentes que podem ser executados diretamente via linha de comando.",
        epilog="💡 DICA: Use 'uv run <nome_do_script.py> -h' para ver os detalhes de uma ferramenta específica."
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: list
    subparsers.add_parser("list", help="Lista e exibe a ajuda (-h) de todas as ferramentas .py disponíveis na pasta utils")

    # Se nenhum comando for passado, exibe o help principal
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "list":
        utils_dir = Path(__file__).resolve().parent
        print(f"\n🌊 Listando ferramentas em: {utils_dir.name}/")
        print("=" * 60)
        
        # Procura todos os arquivos .py na pasta
        for py_file in sorted(utils_dir.glob("*.py")):
            # Ignora o próprio main.py e arquivos ocultos/iniciais
            if py_file.name in ("main.py", "__init__.py") or py_file.name.startswith("."):
                continue
            
            print(f"\n🚀 Ferramenta: {py_file.name}")
            print("-" * 60)
            try:
                # Usa o executável Python atual (do .venv gerado pelo uv) para rodar o script com -h
                subprocess.run([sys.executable, str(py_file), "-h"], check=False)
            except Exception as e:
                print(f"[!] Erro ao tentar executar {py_file.name}: {e}")

if __name__ == "__main__":
    main()