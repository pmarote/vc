# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "tomli; python_version < '3.11'",
# ]
# ///

import os
import sys
import webbrowser
import argparse
from pathlib import Path

# Tenta importar tomllib (Python 3.11+) ou tomli como fallback
try:
    import tomllib
except ImportError:
    import tomli as tomllib

# Configuração de caminhos relativos (utils está dentro da raiz do projeto)
UTILS_DIR = Path(__file__).resolve().parent
ROOT_DIR = UTILS_DIR.parent
VAR_DIR = ROOT_DIR / "var"
SFIAWEB_DIR = ROOT_DIR / "sfiaweb"
CONFIG_FILE = VAR_DIR / "sfia_config.toml"

def abrir_explorer_workdir():
    """Abre o Windows Explorer no diretório work_dir definido no TOML."""
    if not VAR_DIR.exists():
        print(f"❌ ERRO: Pasta 'var' não encontrada em {VAR_DIR}")
        return

    if not CONFIG_FILE.exists():
        print(f"❌ ERRO: Arquivo de configuração '{CONFIG_FILE.name}' não encontrado.")
        return

    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
        
        work_dir_str = config.get("work_dir")
        if not work_dir_str:
            print(f"❌ ERRO: Chave 'work_dir' não encontrada dentro de {CONFIG_FILE.name}")
            return

        work_dir = Path(work_dir_str)
        if not work_dir.exists():
            print(f"❌ ERRO: O diretório de trabalho definido não existe:\n   ➜ {work_dir}")
            return

        print(f"📂 Abrindo Explorer em: {work_dir}")
        os.startfile(work_dir)

    except Exception as e:
        print(f"❌ ERRO ao processar configuração: {e}")

def abrir_explorer_rootdir():
    """Abre o Windows Explorer no diretório raiz, do código fonte, do projeto VC."""
    if not ROOT_DIR.exists():
        print(f"❌ ERRO: Pasta ROOT_DIR {ROOT_DIR} não encontrada.")
        return

    print(f"📂 Abrindo Explorer em: {ROOT_DIR}")
    os.startfile(ROOT_DIR)

def abrir_servidor_web():
    """Abre o browser no endereço padrão do SFIA Web Server."""
    url = "http://127.0.0.1:5678/"
    print(f"🌐 Abrindo VC Workspace (Web Viewer): {url}")
    webbrowser.open(url)

def abrir_visualizador_local():
    """Abre o visualizador de markdown local (HTML) no browser."""
    viewer_file = SFIAWEB_DIR / "md-viewer-pm.html"
    
    if not SFIAWEB_DIR.exists():
        print(f"❌ ERRO: Pasta 'sfiaweb' não encontrada em {SFIAWEB_DIR}")
        return

    if not viewer_file.exists():
        print(f"❌ ERRO: Arquivo visualizador '{viewer_file.name}' não encontrado em {SFIAWEB_DIR}")
        return

    print(f"📑 Abrindo Visualizador de Markdown Local: {viewer_file.name}")
    # Converte o caminho para URI (file://...) para garantir compatibilidade no browser
    webbrowser.open(viewer_file.as_uri())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="🚀 VC Shortcuts - Atalhos Rápidos para o dia a dia",
        epilog="Exemplo: uv run shortcuts.py -w"
    )
    
    parser.add_argument('-w', '--work', action='store_true', help='Abre o Explorer no work_dir atual')
    parser.add_argument('-r', '--root', action='store_true', help='Abre o Explorer na pasta raiz, fonte, do projeto VC')
    parser.add_argument('-s', '--server', action='store_true', help='Abre o VC Workspace (127.0.0.1:5678)')
    parser.add_argument('-v', '--viewer', action='store_true', help='Abre o visualizador MD local (HTML)')
    
    # Se rodar sem argumentos, exibe o help
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.work:
        abrir_explorer_workdir()

    if args.root:
        abrir_explorer_rootdir()
    
    if args.server:
        abrir_servidor_web()
        
    if args.viewer:
        abrir_visualizador_local()