"""
sfia_safic/main.py
Orquestrador Principal (CLI) do fluxo de auditoria

Refatorado para utilizar a biblioteca central core.lib.vccore
"""
import argparse
import sys
import shutil
from pathlib import Path

# Imports do seu ecossistema
from builder import construir_banco_sia
from reporter import gerar_relatorios
from reporter import gerar_relatorio_operacoes, gerar_relatorio_itens
from template_engine import compilar_todos_templates

# IMPORTANTE: Importando a biblioteca central do VC
import core.lib.vccore as vc

# ==========================================
# GESTÃO DE CONTEXTO E PASTAS
# ==========================================

def set_work_dir(wd: Path):
    """Salva o diretório de trabalho no TOML global do VC."""
    with open(vc.CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(f'work_dir = "{wd.resolve().as_posix()}"\n')

# ==========================================
# TELA DE AJUDA DIDÁTICA (CUSTOM -h)
# ==========================================

def show_help():
    """Exibe uma tela de ajuda interativa, colorida e contextualizada."""
    work_dir = vc.get_work_dir()
    
    print(f"\n{vc.Colors.CYAN}{vc.Colors.BOLD}======================================================================{vc.Colors.RESET}")
    print(f"{vc.Colors.CYAN}{vc.Colors.BOLD} 🚀 VC SAFIC - Módulo de Processamento e Auditoria{vc.Colors.RESET}")
    print(f"{vc.Colors.CYAN}{vc.Colors.BOLD}======================================================================{vc.Colors.RESET}\n")

    # 1. Status do Workspace
    print(f" {vc.Colors.BOLD}📌 STATUS DO WORKSPACE (Lido de var/sfia_config.toml):{vc.Colors.RESET}")
    if work_dir and work_dir.exists():
        print(f"    {vc.Colors.GREEN}Ativo ➔ {work_dir}{vc.Colors.RESET}\n")
    else:
        print(f"    {vc.Colors.YELLOW}Nenhum Workspace ativo no momento. Você precisa inicializar um.{vc.Colors.RESET}\n")

    # 2. Explicação Didática
    print(f" {vc.Colors.BOLD}📖 FLUXO DE TRABALHO:{vc.Colors.RESET}")
    print("    O SAFIC opera em etapas sequenciais. Primeiro você inicializa a pasta,")
    print("    depois constrói os bancos de dados e, por fim, gera os relatórios.\n")

    # 3. Comandos
    print(f" {vc.Colors.BOLD}⚙️  COMANDOS DISPONÍVEIS:{vc.Colors.RESET}\n")
    
    print(f"  {vc.Colors.GREEN}init{vc.Colors.RESET}         Inicializa e formata uma nova pasta de auditoria (work_dir).")
    print(f"               {vc.Colors.YELLOW}Uso:{vc.Colors.RESET} vc sfia_safic main.py init --dir <CAMINHO_DA_PASTA>")
    print(f"               {vc.Colors.RED}Regra de Ouro:{vc.Colors.RESET} A pasta informada DEVE estar completamente vazia,")
    print("               contendo APENAS o arquivo 'osf.sqlite' extraído do sistema.")
    print("               O parâmetro '--dir' é OBRIGATÓRIO e EXCLUSIVO deste comando.")
    print("               Após a execução, work_dir conterá as pastas _dbs (bancos de dados sqlite),")
    print("                _mds (relatórios markdown), _xls (planilhas Excel),")
    print("                _tmpl (templates para elaboração de relatórios markdown)")
    print("                e um arquivo Excel inicial de modelos de trabalho, de nome TrabPaulo.xlsx\n")

    print(f"  {vc.Colors.GREEN}build{vc.Colors.RESET}        Constrói o banco de dados analítico 'sia.sqlite'.")
    print("               Execute logo após o 'init' ou sempre que alterar a planilha Excel.\n")

    print(f"  {vc.Colors.GREEN}report{vc.Colors.RESET}       Gera o conjunto de relatórios básicos na pasta '_mds/'.")
    print(f"  {vc.Colors.GREEN}report_oper{vc.Colors.RESET}  Gera relatórios detalhados com foco em Operações.")
    print(f"  {vc.Colors.GREEN}report_item{vc.Colors.RESET}  Gera relatórios detalhados com foco em Itens.\n")
    
    print(f"  {vc.Colors.GREEN}template{vc.Colors.RESET}     Processa Literate Documents (*.tmpl.md) salvos na pasta _tmpl.\n")

    print(f" {vc.Colors.BOLD}🔧 FLAGS GLOBAIS:{vc.Colors.RESET}")
    print(f"  {vc.Colors.CYAN}--debug{vc.Colors.RESET}      Exibe as queries SQL e metadados dentro dos relatórios gerados.")
    print(f"  {vc.Colors.CYAN}-h, --help{vc.Colors.RESET}   Exibe esta tela de ajuda maravilhosa.\n")

# ==========================================
# VALIDAÇÕES DE AMBIENTE
# ==========================================

def validar_para_init(wd: Path):
    """Valida se a pasta atende aos rigorosos critérios para receber 'init'."""
    if not wd.exists() or not wd.is_dir():
        vc.log(f"O diretório informado não existe ou não é acessível:\n  {wd}", level="ERROR")
        sys.exit(1)

    # 1. Não pode ter NENHUMA subpasta
    subpastas = [p for p in wd.iterdir() if p.is_dir()]
    if subpastas:
        vc.log("O diretório de inicialização deve ser limpo e NÃO PODE conter subpastas.", level="ERROR")
        print(f"  Encontradas: {[p.name for p in subpastas]}")
        sys.exit(1)

    # 2. DEVE ter o arquivo osf.sqlite na raiz
    db_osf = wd / "osf.sqlite"
    if not db_osf.exists():
        vc.log("O arquivo base 'osf.sqlite' não foi encontrado na raiz do diretório.", level="ERROR")
        print("  Por favor, coloque o banco de dados extraído do SAFIC nesta pasta antes de rodar o init.")
        sys.exit(1)

def validar_workspace_ativo(wd: Path):
    """Valida se o workspace ativo possui as quatro pastas obrigatórias."""
    dbs = wd / "_dbs"
    mds = wd / "_mds"
    xls = wd / "_xls"
    tmpl = wd / "_tmpl"
    
    if not (dbs.exists() and mds.exists() and xls.exists() and tmpl.exists()):
        vc.log("O diretório de trabalho atual está com estrutura errada ou não foi inicializado corretamente.", level="ERROR")
        print(f"  Diretório: {wd}")
        print("  Esperado: Pastas '_dbs', '_mds', '_xls' e '_tmpl'.")
        print(f"\n{vc.Colors.YELLOW}💡 SOLUÇÃO: Execute 'vc sfia_safic main.py init --dir <caminho_da_auditoria>' para organizar a pasta.{vc.Colors.RESET}")
        sys.exit(1)

# ==========================================
# SETUP DE WORKSPACE
# ==========================================

def setup_workspace(wd: Path):
    """
    Cria a estrutura rigorosa de pastas.
    Move o osf.sqlite para _dbs e copia os templates.
    """
    script_dir = Path(__file__).resolve().parent
    dbs_dir = wd / "_dbs"
    mds_dir = wd / "_mds"
    xls_dir = wd / "_xls"
    tmpl_dir = wd / "_tmpl"

    # 1. Cria a estrutura de diretórios
    for d in [dbs_dir, mds_dir, xls_dir, tmpl_dir]:
        d.mkdir(parents=True, exist_ok=True)
        vc.log(f"Criada pasta: {d.relative_to(wd)}", level="INFO")

    # 2. Move o osf.sqlite da raiz para a pasta _dbs
    osf_origem = wd / "osf.sqlite"
    osf_destino = dbs_dir / "osf.sqlite"
    if osf_origem.exists():
        shutil.move(osf_origem, osf_destino)
        vc.log("Movido 'osf.sqlite' para a pasta _dbs", level="INFO")

    # 3. Cópia dos arquivos template para a raiz da pasta de trabalho
    files_to_copy = [
        ("_tmpl/auditoria.tmpl.md", "copiado template de markdown modelo para"),
        ("TrabPaulo.xlsm", "copiada arquivo excel com planilhas de trabalho modelo para")
    ]

    for filename, message in files_to_copy:
        src = script_dir / filename
        dest = wd / filename
        
        if src.exists():
            if not dest.exists():
                shutil.copy2(src, dest)
                vc.log(f"{message.capitalize()} {dest}", level="INFO")
        else:
            vc.log(f"Modelo {filename} não encontrado na pasta do sistema ({script_dir.name}).", level="WARNING")

# ==========================================
# CLI ENTRYPOINT
# ==========================================

if __name__ == "__main__":
    
    # Intercepta o pedido de ajuda (-h ou --help) ANTES do argparse processar
    if "-h" in sys.argv or "--help" in sys.argv:
        show_help()
        sys.exit(0)
        
    # Adiciona add_help=False para evitar conflito com nossa tela customizada
    parser = argparse.ArgumentParser(description="VC - SAFIC (Auditor Inteligente)", add_help=False)
    
    parser.add_argument("command", choices=["init", "build", "report", "report_oper", "report_item", "template"])
    parser.add_argument("--dir", help="Caminho para a pasta da auditoria (Obrigatório apenas no comando 'init').")
    parser.add_argument("--debug", action="store_true", help="Gera os relatórios com os metadados e SQL visíveis.")
    
    # Lida de forma suave se o usuário esquecer o comando
    try:
        args = parser.parse_args()
    except SystemExit:
        print(f"\n{vc.Colors.YELLOW}💡 Dica: Rode 'vc sfia_safic main.py -h' para ver as instruções completas.{vc.Colors.RESET}")
        sys.exit(1)

    # ---------------------------------------------------------
    # FLUXO 1: INICIALIZAÇÃO (init)
    # ---------------------------------------------------------
    if args.command == "init":
        if not args.dir:
            vc.log("O comando 'init' exige o parâmetro --dir.", level="ERROR")
            print("  Exemplo: vc sfia_safic main.py init --dir ../auditorias/empresa_x")
            sys.exit(1)
            
        target_wd = Path(args.dir).resolve()
        
        vc.log(f"Validando diretório para inicialização: {target_wd}", level="INFO")
        validar_para_init(target_wd)
        
        vc.log("Inicializando o Workspace da Auditoria...", level="INFO")
        setup_workspace(target_wd)
        set_work_dir(target_wd)
        
        print(f"\n{vc.Colors.GREEN}✅ Workspace inicializado com sucesso!{vc.Colors.RESET}")
        print(f"🔗 O VC agora está apontando para esta auditoria.")
        print(f"➡️  Próximo passo recomendado: {vc.Colors.BOLD}vc sfia_safic main.py build{vc.Colors.RESET}")
        sys.exit(0)

    # ---------------------------------------------------------
    # FLUXO 2: PROCESSAMENTO (build, report, template, etc.)
    # ---------------------------------------------------------
    
    # Se o usuário tentar passar --dir num comando que não seja init, bloqueia.
    if args.dir:
        vc.log("O parâmetro '--dir' só pode ser usado com o comando 'init'.", level="ERROR")
        print("  Para trocar de auditoria, rode: vc sfia_safic main.py init --dir <nova_pasta>")
        sys.exit(1)

    # 1. Tenta recuperar a pasta ativa usando a biblioteca
    work_dir = vc.get_work_dir()
    if not work_dir:
        vc.log("Nenhum workspace ativo encontrado no arquivo sfia_config.toml.", level="ERROR")
        print(f"{vc.Colors.YELLOW}💡 Execute: vc sfia_safic main.py init --dir <caminho_da_auditoria>{vc.Colors.RESET}")
        sys.exit(1)

    # 2. Valida se a pasta ativa não foi corrompida / apagada
    validar_workspace_ativo(work_dir)

    # 3. Mapeia os caminhos absolutos padronizados
    dbs_dir = work_dir / "_dbs"
    mds_dir = work_dir / "_mds"
    xls_dir = work_dir / "_xls"
    tmpl_dir = work_dir / "_tmpl"
    db_osf = dbs_dir / "osf.sqlite"
    db_sia = dbs_dir / "sia.sqlite"

    # --- EXECUÇÃO DOS COMANDOS ---
    if args.command == "build":
        if not db_osf.exists():
            vc.log("O banco base 'osf.sqlite' desapareceu da pasta _dbs.", level="ERROR")
            sys.exit(1)

        excel_path = str(work_dir / "TrabPaulo.xlsm")
        if not Path(excel_path).exists():
            # Fallback de segurança usando a raiz global
            excel_path = str(vc.ROOT_DIR / "sfia_safic" / "TrabPaulo.xlsm")

        vc.log(f"Construindo banco SIA:\n ➔ OSF: {db_osf.name}\n ➔ SIA: {db_sia.name}\n ➔ Excel: {Path(excel_path).name}", level="INFO")
        construir_banco_sia(str(db_osf), str(db_sia), excel_path)
        print(f"{vc.Colors.GREEN}✅ Construção finalizada com sucesso.{vc.Colors.RESET}")

    elif args.command in ["report", "report_oper", "report_item"]:
        if not db_sia.exists():
            vc.log(f"'{db_sia.name}' não encontrado em _dbs. Rode 'build' primeiro.", level="ERROR")
            sys.exit(1)

        vc.log("Gerando relatórios na pasta: _mds/", level="INFO")
        
        if args.command == "report":
            gerar_relatorios(db_osf, db_sia, mds_dir, xls_dir, debug=args.debug)
        elif args.command == "report_oper":
            gerar_relatorio_operacoes(db_osf, db_sia, mds_dir, dbs_dir, xls_dir, debug=args.debug)
        elif args.command == "report_item":
            gerar_relatorio_itens(db_osf, db_sia, mds_dir, dbs_dir, xls_dir, debug=args.debug)

    elif args.command == "template":
        vc.log("Processando Literate Documents (*.tmpl.md) na pasta _tmpl do workspace...", level="INFO")
        compilar_todos_templates(work_dir, debug=args.debug)
        print(f"{vc.Colors.GREEN}✅ Processamento de templates finalizado.{vc.Colors.RESET}")