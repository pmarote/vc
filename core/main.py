import argparse
import sys
import webbrowser
import os
import subprocess
from pathlib import Path

# Importa o namespace centralizado
import core.lib.vccore as vc
    
def show_welcome():
    """Exibe o banner de status, ferramentas e boas-vindas."""
    work_dir = vc.get_work_dir()
    version = vc.get_vc_version()
    
    print(f"{vc.Colors.CYAN}{vc.Colors.BOLD}")
    print(r"  _   _  ____   ")
    print(r" | | | |/ ___|  ")
    print(r" | | | | |      ")
    print(r" | |_| | |___   ")
    print(r"  \___/ \____|  ")
    print(f"{vc.Colors.RESET}")
    vc.log(f"🌊 VC Core - Central de Comando v{version}", level="INFO")
    print(f"{vc.Colors.CYAN}{'='*70}{vc.Colors.RESET}")
    
    if work_dir and work_dir.exists():
        vc.log(f"WorkDir: {vc.Colors.YELLOW}{work_dir}{vc.Colors.RESET}")
    else:
        vc.log("WorkDir: Não configurado.", level="WARNING")

    # --- VERIFICAÇÃO CRÍTICA DO DRIVE (Restrição ao Drive C:) ---
    if os.name == 'nt' and vc.ROOT_DIR.drive.upper() != 'C:':
        print(f" {vc.Colors.BG_RED}======================================================================{vc.Colors.RESET}")
        print(f" {vc.Colors.BG_RED} ALERTA CRÍTICO: AMBIENTE FORA DO DRIVE C: !                          {vc.Colors.RESET}")
        print(f" {vc.Colors.BG_RED}======================================================================{vc.Colors.RESET}")
        print(f" {vc.Colors.YELLOW}Você está executando o VC a partir do drive {vc.Colors.BOLD}{vc.ROOT_DIR.drive}{vc.Colors.RESET}{vc.Colors.YELLOW}.{vc.Colors.RESET}")
        print("")
        print(f" {vc.Colors.RED}{vc.Colors.BOLD}Por que isso é um problema e não é recomendável?{vc.Colors.RESET}")
        print(" Se você der boot no computador usando outro Windows (dual boot, disco externo,")
        print(" etc.), o sistema operacional pode reatribuir a letra deste drive original")
        print(" (por exemplo, o que era C: passa a ser E:).")
        print("")
        print(" O ecossistema VC, o Python e os ambientes virtuais (.venv) gerados pelo 'uv'")
        print(" dependem de caminhos absolutos para criar links de sistema corretos.")
        print(f" A mudança da letra do drive {vc.Colors.BOLD}QUEBRARÁ{vc.Colors.RESET} os links do ambiente, corromperá as")
        print(" bibliotecas e causará falhas imprevisíveis nos relatórios.")
        print("")
        print(f" {vc.Colors.GREEN}{vc.Colors.BOLD}Recomendação Fortemente Aconselhada:{vc.Colors.RESET}")
        print(" Feche este terminal, mova a pasta inteira do VC para o seu drive C:, limpe os")
        print(f" ambientes virtuais com o comando {vc.Colors.BOLD}vcclean{vc.Colors.RESET} e execute o terminal.bat")
        print(" a partir de seu drive C:.")
        print("")
        print(f" {vc.Colors.BG_RED}======================================================================{vc.Colors.RESET}")
        print("")
        input(f" Se deseja continuar mesmo assim (ciente de que o sistema pode quebrar), pressione Enter...")
        print("")
        vc.log("Iniciando terminal em modo de risco...", level="WARNING")
        print("")

    print(f"{vc.Colors.CYAN}{'='*70}{vc.Colors.RESET}")
    
    # --- VERIFICAÇÃO DE FERRAMENTAS PORTÁTEIS (USR_DIR) ---
    if vc.USR_DIR.exists():
        print(f" {vc.Colors.YELLOW}{vc.Colors.BOLD}[FERRAMENTAS]{vc.Colors.RESET}")
        print(f"  {vc.Colors.GREEN}wm{vc.Colors.RESET}, {vc.Colors.GREEN}dbb{vc.Colors.RESET}, {vc.Colors.GREEN}ct{vc.Colors.RESET}, {vc.Colors.GREEN}mp{vc.Colors.RESET}       WinMerge, DBBrowser, CudaText, Markpad")
    else:
        print(f" {vc.Colors.BG_RED} AVISO CRÍTICO: PASTA DE FERRAMENTAS 'usr' NÃO ENCONTRADA! {vc.Colors.RESET}")
        print(f" {vc.Colors.YELLOW}A pasta {vc.Colors.BOLD}{vc.USR_DIR}{vc.Colors.RESET}{vc.Colors.YELLOW} não foi detectada. Atalhos desativados.{vc.Colors.RESET}")
        print("")
        print(f" {vc.Colors.RED}{vc.Colors.BOLD}Por que isso é um problema?{vc.Colors.RESET}")
        print(" As ferramentas contidas nela (WinMerge, DB Browser, CudaText e Markpad)")
        print(f" são {vc.Colors.BOLD}EXTREMAMENTE IMPORTANTES{vc.Colors.RESET} para o trabalho diário de auditoria.")
        print(" Elas garantem agilidade para inspecionar bancos de dados, comparar códigos")
        print(" e editar os templates Markdown de forma eficiente.")
        print("")
        print(f" {vc.Colors.GREEN}{vc.Colors.BOLD}Ação Altamente Recomendada:{vc.Colors.RESET}")
        print(" Providencie a cópia desta pasta 'usr'. Copie a pasta inteira e cole-a")
        print(f" exatamente no seguinte caminho: {vc.Colors.YELLOW}{vc.Colors.BOLD}{vc.USR_DIR}{vc.Colors.RESET}")


    print(f"{vc.Colors.CYAN}{'='*70}{vc.Colors.RESET}")
    print(f" {vc.Colors.BOLD}Comandos de Atalho:{vc.Colors.RESET}")
    vc.log("vc [app] [cmd]  - Executa ferramentas (ex: vc core main.py -h)")
    vc.log("vcdir           - Lista microapps disponíveis")
    vc.log("vcclean         - Limpa ambientes e caches")
    vc.log("vcw (vc core main.py serve)     - Inicia o servidor web local")
    vc.log("vcew (vc core main.py --work)   - Abre Explorer no WorkDir")
    vc.log("vcer (vc core main.py --root)   - Abre Explorer na Raiz")
    vc.log("vcmd (vc core main.py --viewer) - Abre Visualizador MD")
    print(f"{vc.Colors.CYAN}{'='*70}{vc.Colors.RESET}")

def open_path(path_type):
    """Gerencia a abertura de diretórios e arquivos locais no SO."""
    work_dir = vc.get_work_dir()
    
    if path_type == 'work' and work_dir:
        os.startfile(work_dir) if os.name == 'nt' else subprocess.run(['open', work_dir])
    
    elif path_type == 'root':
        os.startfile(vc.ROOT_DIR) if os.name == 'nt' else subprocess.run(['open', vc.ROOT_DIR])
    
    elif path_type == 'viewer':
        # Localiza o arquivo HTML do visualizador na pasta core
        viewer_path = vc.CORE_DIR / "md-viewer-pm.html"
        if viewer_path.exists():
            vc.log(f"Abrindo Visualizador MD: {viewer_path.name}")
            # Abre o arquivo local no navegador padrão como uma URI file:///
            webbrowser.open(viewer_path.as_uri())
        else:
            vc.log(f"Erro: Arquivo {viewer_path.name} não encontrado em {vc.CORE_DIR}", level="ERROR")

def main():
    parser = argparse.ArgumentParser(description="🚀 VC Core - Orquestrador Central")
    
    # Flags de utilidade
    parser.add_argument('--welcome', action='store_true', help='Banner de status')
    parser.add_argument('-w', '--work', action='store_true', help='Abre Explorer no WorkDir')
    parser.add_argument('-r', '--root', action='store_true', help='Abre Explorer na Raiz')
    parser.add_argument('-v', '--viewer', action='store_true', help='Abre Visualizador MD')
    parser.add_argument('--clean', action='store_true', help='Limpa venvs e caches')

    # Subcomando 'serve'
    subparsers = parser.add_subparsers(dest="command")
    serve_parser = subparsers.add_parser("serve", help="Inicia o servidor web local")
    serve_parser.add_argument("--port", type=int, default=5678)

    args = parser.parse_args()

    if args.welcome:
        show_welcome()
    elif args.work:
        open_path('work')
    elif args.root:
        open_path('root')
    elif args.viewer:
        # Implementação correta para abrir o browser no endereço local
        open_path('viewer')
    elif args.clean:
        vc.log("Iniciando limpeza...", level="WARNING")
        # Chamar lógica do vcclean.bat ou script interno
    elif args.command == "serve":
        work_dir = vc.get_work_dir()
        if not work_dir:
            vc.log("Não é possível iniciar o servidor: WorkDir não configurado.", level="ERROR")
            sys.exit(1)
        
        from server import start_server
        url = f"http://127.0.0.1:{args.port}/"
        vc.log(f"Abrindo VC Launchpad: {url}", level="INFO")
        webbrowser.open(url)
        start_server(port=args.port, work_dir_path=str(work_dir))
    else:
        if len(sys.argv) == 1: parser.print_help()

if __name__ == "__main__":
    main()