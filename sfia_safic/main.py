"""
sfia_safic/main.py
Orquestrador Principal (CLI) do fluxo de auditoria
"""
import argparse
import sys
import shutil
import tomllib
from pathlib import Path

# Imports do seu ecossistema
from builder import construir_banco_sia
from reporter import gerar_relatorios
from reporter import gerar_relatorio_operacoes, gerar_relatorio_itens
from template_engine import compilar_todos_templates

# ==========================================\n# GESTÃO DE CONTEXTO E PASTAS (VIBE CODING)
# ==========================================

# Resolve o caminho da raiz do projeto (Ex: C:/srcP/vc)
# Path(__file__).resolve().parent é 'sfia_safic'
ROOT_DIR = Path(__file__).resolve().parent.parent
VAR_DIR = ROOT_DIR / "var"
# Garante que a pasta var existe para não dar erro ao salvar
VAR_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = VAR_DIR / "sfia_config.toml"

def get_work_dir() -> Path | None:
    """Lê o diretório de trabalho atual do TOML."""
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
        wd_str = config.get("work_dir")
        if wd_str:
            wd = Path(wd_str)
            if wd.exists():
                return wd
    except Exception:
        pass
    return None

def set_work_dir(wd: Path):
    """Salva o diretório de trabalho no TOML."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(f'work_dir = "{wd.resolve().as_posix()}"\n')

# ==========================================\n# VALIDAÇÕES DE AMBIENTE
# ==========================================

def validar_para_init(wd: Path):
    """Valida se a pasta atende aos rigorosos critérios para receber 'init'."""
    if not wd.exists() or not wd.is_dir():
        print(f"❌ ERRO: O diretório informado não existe ou não é acessível:\n  {wd}")
        sys.exit(1)

    # 1. Não pode ter NENHUMA subpasta
    subpastas = [p for p in wd.iterdir() if p.is_dir()]
    if subpastas:
        print(f"❌ ERRO: O diretório de inicialização deve ser limpo e NÃO PODE conter subpastas.")
        print(f"  Encontradas: {[p.name for p in subpastas]}")
        sys.exit(1)

    # 2. DEVE ter o arquivo osf.sqlite na raiz
    db_osf = wd / "osf.sqlite"
    if not db_osf.exists():
        print(f"❌ ERRO: O arquivo base 'osf.sqlite' não foi encontrado na raiz do diretório.")
        print(f"  Por favor, coloque o banco de dados extraído do SAFIC nesta pasta antes de rodar o init.")
        sys.exit(1)

def validar_workspace_ativo(wd: Path):
    """Valida se o workspace ativo possui as três pastas obrigatórias."""
    dbs = wd / "_dbs"
    mds = wd / "_mds"
    xls = wd / "_xls"
    
    if not (dbs.exists() and mds.exists() and xls.exists()):
        print(f"❌ ERRO: O diretório de trabalho atual está corrompido ou não foi inicializado corretamente.")
        print(f"  Diretório: {wd}")
        print(f"  Esperado: Pastas '_dbs', '_mds' e '_xls'.")
        print(f"\n💡 SOLUÇÃO: Execute 'vc sfia_safic main.py init --dir <caminho_da_auditoria>' para organizar a pasta.")
        sys.exit(1)

# ==========================================\n# SETUP DE WORKSPACE
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

    # 1. Cria a estrutura de diretórios
    for d in [dbs_dir, mds_dir, xls_dir]:
        d.mkdir(parents=True, exist_ok=True)
        print(f" ➔ Criada pasta: {d.relative_to(wd)}")

    # 2. Move o osf.sqlite da raiz para a pasta _dbs
    osf_origem = wd / "osf.sqlite"
    osf_destino = dbs_dir / "osf.sqlite"
    if osf_origem.exists():
        shutil.move(osf_origem, osf_destino)
        print(f" ➔ Movido 'osf.sqlite' para a pasta _dbs")

    # 3. Cópia dos arquivos template para a raiz da pasta de trabalho
    files_to_copy = [
        ("auditoria.tmpl.md", "copiado template de markdown modelo de nome auditoria.tmpl.md para"),
        ("TrabPaulo.xlsm", "copiada arquivo excel com planilhas de trabalho modelo para")
    ]

    for filename, message in files_to_copy:
        src = script_dir / filename
        dest = wd / filename
        
        if src.exists():
            if not dest.exists():
                shutil.copy2(src, dest)
                print(f" ➔ {message} {dest}")
        else:
            print(f" ⚠️ Aviso: Modelo {filename} não encontrado na pasta do sistema ({script_dir.name}).")

# ==========================================\n# CLI ENTRYPOINT
# ==========================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VC - SAFIC (Auditor Inteligente)")
    
    # Adicionado o comando 'init'
    parser.add_argument("command", choices=["init", "build", "report", "report_oper", "report_item", "template"],
                        help="Comando a executar.")
    
    # O parâmetro dir agora é exclusivo (e obrigatório) para o 'init'
    parser.add_argument("--dir", help="Caminho para a pasta da auditoria (Obrigatório apenas no comando 'init').")
    parser.add_argument("--debug", action="store_true", help="Gera os relatórios com os metadados e SQL visíveis.")
    
    args = parser.parse_args()

    # ---------------------------------------------------------
    # FLUXO 1: INICIALIZAÇÃO (init)
    # ---------------------------------------------------------
    if args.command == "init":
        if not args.dir:
            print("❌ ERRO: O comando 'init' exige o parâmetro --dir.")
            print("  Exemplo: vc sfia_safic main.py init --dir ../auditorias/empresa_x")
            sys.exit(1)
            
        target_wd = Path(args.dir).resolve()
        
        print(f"🧽 Validando diretório para inicialização: {target_wd}")
        validar_para_init(target_wd)
        
        print(f"🏗️ Inicializando o Workspace da Auditoria...")
        setup_workspace(target_wd)
        set_work_dir(target_wd)
        
        print(f"\n✅ Workspace inicializado com sucesso!")
        print(f"🔗 O VC agora está apontando para esta auditoria.")
        print(f"➡️  Próximo passo recomendado: vc sfia_safic main.py build")
        sys.exit(0)

    # ---------------------------------------------------------
    # FLUXO 2: PROCESSAMENTO (build, report, template, etc.)
    # ---------------------------------------------------------
    
    # Se o usuário tentar passar --dir num comando que não seja init, bloqueia.
    if args.dir:
        print(f"❌ ERRO: O parâmetro '--dir' só pode ser usado com o comando 'init'.")
        print(f"  Para trocar de auditoria, rode: vc sfia_safic main.py init --dir <nova_pasta>")
        sys.exit(1)

    # 1. Tenta recuperar a pasta ativa
    work_dir = get_work_dir()
    if not work_dir:
        print(f"❌ ERRO: Nenhum workspace ativo encontrado no arquivo sfia_config.toml.")
        print(f"💡 Execute: vc sfia_safic main.py init --dir <caminho_da_auditoria>")
        sys.exit(1)

    # 2. Valida se a pasta ativa não foi corrompida / apagada
    validar_workspace_ativo(work_dir)

    # 3. Mapeia os caminhos absolutos padronizados
    dbs_dir = work_dir / "_dbs"
    mds_dir = work_dir / "_mds"
    xls_dir = work_dir / "_xls"
    db_osf = dbs_dir / "osf.sqlite"
    db_sia = dbs_dir / "sia.sqlite"

    # --- EXECUÇÃO DOS COMANDOS ---
    if args.command == "build":
        if not db_osf.exists():
            print(f"❌ ERRO: O banco base 'osf.sqlite' desapareceu da pasta _dbs.")
            sys.exit(1)

        excel_path = str(work_dir / "TrabPaulo.xlsm")
        if not Path(excel_path).exists():
            # Fallback de segurança caso o auditor tenha apagado o arquivo da pasta
            excel_path = str(ROOT_DIR / "sfia_safic" / "TrabPaulo.xlsm")

        print(f"🛠️ Construindo banco SIA:\n ➔ OSF: {db_osf.name}\n ➔ SIA: {db_sia.name}\n ➔ Excel: {Path(excel_path).name}")
        construir_banco_sia(str(db_osf), str(db_sia), excel_path)
        print("✅ Construção finalizada com sucesso.")

    elif args.command in ["report", "report_oper", "report_item"]:
        if not db_sia.exists():
            print(f"❌ ERRO: '{db_sia.name}' não encontrado em _dbs. Rode 'build' primeiro.")
            sys.exit(1)

        print(f"📊 Gerando relatórios na pasta: _mds/")
        
        if args.command == "report":
            gerar_relatorios(db_osf, db_sia, mds_dir, xls_dir, debug=args.debug)
        elif args.command == "report_oper":
            gerar_relatorio_operacoes(db_osf, db_sia, mds_dir, dbs_dir, xls_dir, debug=args.debug)
        elif args.command == "report_item":
            gerar_relatorio_itens(db_osf, db_sia, mds_dir, dbs_dir, xls_dir, debug=args.debug)

    elif args.command == "template":
        print(f"📖 Processando Literate Documents (*.tmpl.md) na #SOMENTE NA RAIZ# do workspace...")
        compilar_todos_templates(work_dir, debug=args.debug)
        print("✅ Processamento de templates finalizado.")