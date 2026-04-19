import argparse
import sys
import re
import shutil
import tomllib
from pathlib import Path

# Imports do seu ecossistema
from builder import construir_banco_sia
from reporter import gerar_relatorios
from reporter import gerar_relatorio_operacoes, gerar_relatorio_itens

# ==========================================
# GESTÃO DE CONTEXTO E PASTAS (VIBE CODING)
# ==========================================

# Resolve o caminho da raiz do projeto (Ex: C:/srcP/vc)
# Path(__file__).resolve().parent é 'sfia_safic'
ROOT_DIR = Path(__file__).resolve().parent.parent
VAR_DIR = ROOT_DIR / "var"

# Garante que a pasta var existe para não dar erro ao salvar
VAR_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_FILE = VAR_DIR / "sfia_config.toml"

def load_or_save_work_dir(args_dir: str | None) -> Path:
    """Lê a pasta do TOML ou salva uma nova se `--dir` for passado."""
    if args_dir:
        wd = Path(args_dir).resolve()
        # Salva no toml (usamos .as_posix() para evitar problemas com barras no Windows)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f'work_dir = "{wd.as_posix()}"\n')
        return wd
    
    # Se não passou --dir, tenta ler do TOML
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
            if "work_dir" in config:
                return Path(config["work_dir"])
    
    print("❌ ERRO: Pasta de trabalho não definida.")
    print("💡 DICA: Na primeira execução, use: --dir <caminho>")
    sys.exit(1)

def setup_workspace(wd: Path) -> tuple[Path, Path, Path, Path]:
    """
    Garante a estrutura de pastas e organiza o banco OSF.
    Pastas: _dbs, _xls, _mds
    """
    if not wd.exists():
        print(f"❌ ERRO: A pasta '{wd}' não existe.")
        sys.exit(1)

    # 1. Definição da Estrutura de Pastas (Nomes atualizados)
    dbs_dir = wd / "_dbs"
    xls_dir = wd / "_xls"
    mds_dir = wd / "_mds"

    dbs_dir.mkdir(exist_ok=True)
    xls_dir.mkdir(exist_ok=True)
    mds_dir.mkdir(exist_ok=True)

    # 2. Busca do Arquivo OSF (11 dígitos)
    osf_pattern = re.compile(r"^osf(\d{11})\.sqlite$", re.IGNORECASE)
    db_osf = None

    # Tenta encontrar na raiz (wd) e mover para _dbs
    for p in wd.iterdir():
        if p.is_file() and osf_pattern.match(p.name):
            db_osf = dbs_dir / p.name
            print(f"📦 Organizando: Movendo '{p.name}' para '_dbs/'")
            shutil.move(str(p), str(db_osf))
            break
    
    # Se não estava na raiz, procura dentro de _dbs
    if not db_osf:
        for p in dbs_dir.iterdir():
            if p.is_file() and osf_pattern.match(p.name):
                db_osf = p
                break
    
    if not db_osf:
        print(f"❌ ERRO: osf11111111111.sqlite não encontrado em '{wd}' ou '{wd}/_dbs'.")
        sys.exit(1)

    # 3. Nome do Banco SIA baseado no número da OSF
    numero_osf = osf_pattern.match(db_osf.name).group(1)
    db_sia = dbs_dir / f"sia{numero_osf}.sqlite"

    return db_osf, db_sia, mds_dir, xls_dir

# ==========================================
# MOTOR PRINCIPAL (CLI)
# ==========================================

def main():
    parser = argparse.ArgumentParser(description="Pipeline Automatizado de Auditoria SAFIC (VC)")
    
    # Argumento global (--dir) injetado em todos os subcomandos
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--dir", help="Caminho da pasta SFIA (Obrigatório na primeira execução)")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Comandos
    p_build = subparsers.add_parser("build", parents=[parent_parser], help="Constrói o banco SIA.")
    p_build.add_argument("--excel", help="Caminho manual para TrabPaulo.xlsm")

    subparsers.add_parser("report", parents=[parent_parser], help="Gera todos os relatórios.")
    subparsers.add_parser("report_oper", parents=[parent_parser], help="Gera relatório de operações.")
    subparsers.add_parser("report_item", parents=[parent_parser], help="Gera relatório de itens.")

    args = parser.parse_args()

    # Inicia Workspace
    work_dir = load_or_save_work_dir(args.dir)
    db_osf, db_sia, out_mds, out_xls = setup_workspace(work_dir)

    # Execução das Rotinas
    if args.command == "build":
        # Lógica de fallback robusta para o Excel
        excel_path = args.excel
        if not excel_path:
            # 1ª Tentativa: Dentro da pasta de trabalho (_xls)
            tentativa_local = out_xls / "TrabPaulo.xlsm"
            if tentativa_local.exists():
                excel_path = str(tentativa_local)
            else:
                # 2ª Tentativa: Caminho absoluto na instalação do VC
                # ROOT_DIR (vc/) + sfia_safic/ + TrabPaulo.xlsm
                excel_path = str(ROOT_DIR / "sfia_safic" / "TrabPaulo.xlsm")

        print(f"🛠️ Construindo banco SIA:\\n ➔ OSF: {db_osf.name}\\n ➔ SIA: {db_sia.name}\\n ➔ Excel: {Path(excel_path).name}")
        construir_banco_sia(str(db_osf), str(db_sia), excel_path)
        print("✅ Construção finalizada com sucesso.")

    elif args.command in ["report", "report_oper", "report_item"]:
        if not db_sia.exists():
            print(f"❌ ERRO: '{db_sia.name}' não encontrado. Rode 'build' primeiro.")
            sys.exit(1)

        print(f"📊 Gerando relatórios em: {out_mds}")
        
        # Agora passamos os objetos Path e também informamos onde ficam 
        # os bancos (db_osf.parent) e os planilhas (out_xls) para os relatórios auxiliares
        if args.command == "report":
            # AGORA PASSA out_xls TAMBÉM
            gerar_relatorios(db_osf, db_sia, out_mds, out_xls)
        elif args.command == "report_oper":
            gerar_relatorio_operacoes(db_osf, db_sia, out_mds, db_osf.parent, out_xls)
        elif args.command == "report_item":
            gerar_relatorio_itens(db_osf, db_sia, out_mds, db_osf.parent, out_xls)


if __name__ == "__main__":
    main()