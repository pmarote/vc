import os
import sys
from pathlib import Path

# Tenta importar tomllib (Python 3.11+) ou tomli como fallback
try:
    import tomllib
except ImportError:
    import tomli as tomllib

# --- DEFINIÇÃO DE CAMINHOS TÉCNICOS ---
LIB_DIR = Path(__file__).resolve().parent
CORE_DIR = LIB_DIR.parent
STATIC_DIR = CORE_DIR / "static"
ROOT_DIR = CORE_DIR.parent
VAR_DIR = ROOT_DIR / "var"
TEMP_DIR = VAR_DIR / "temp"
LOGS_DIR = VAR_DIR / "logs"
CONFIG_FILE = VAR_DIR / "sfia_config.toml"
PYPROJECT_FILE = ROOT_DIR / "pyproject.toml"
USR_DIR = ROOT_DIR.parent / "usr"


# --- CORES ANSI PARA TERMINAL ---
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BG_RED = "\033[41;97m"

# --- GESTÃO DE WORKSPACE ---
def get_work_dir():
    """Lê o diretório de trabalho do arquivo de configuração centralizado."""
    if not CONFIG_FILE.exists():
        return None
    try:
        with open(CONFIG_FILE, "rb") as f:
            config = tomllib.load(f)
            return Path(config.get("work_dir", ""))
    except Exception:
        return None

# --- INICIALIZAÇÃO E VALIDAÇÃO DE AMBIENTE ---
def ensure_env():
    """Garante que a estrutura de pastas existe e as variáveis de ambiente estão setadas."""
    # 1. Criação de pastas vitais
    for folder in [VAR_DIR, TEMP_DIR, LOGS_DIR]:
        folder.mkdir(parents=True, exist_ok=True)

    # 2. Validação de Variáveis de Ambiente (terminal.bat)
    errors = []
    
    if os.environ.get("PYTHONUTF8") != "1":
        errors.append("PYTHONUTF8 deve ser '1'")
        
    vc_root = os.environ.get("VC_ROOT")
    if not vc_root:
        errors.append("VC_ROOT (Raiz do Projeto) não está definida")
    
    path_env = os.environ.get("PATH", "")
    if "core\\Scripts" not in path_env:
        errors.append("A pasta core\\Scripts não foi injetada no PATH")
        
    pythonpath = os.environ.get("PYTHONPATH", "")
    # Verifica se a raiz do projeto está no caminho de importação do Python
    if not vc_root or vc_root.strip('\\') not in pythonpath:
        errors.append("A raiz do projeto não está no PYTHONPATH")

    if errors:
        log("FALHA CRÍTICA DE AMBIENTE", level="ERROR")
        for err in errors:
            print(f"   -> {err}")
        print(f"\n{Colors.YELLOW}💡 SOLUÇÃO: O projeto deve ser iniciado via 'terminal.bat' na raiz.{Colors.RESET}")
        sys.exit(1)

# --- SISTEMA DE LOGS ---
def log(message, level="INFO"):
    level = level.upper()
    if level == "INFO": prefix = f"{Colors.CYAN}[INFO]{Colors.RESET}"
    elif level == "WARNING": prefix = f"{Colors.YELLOW}[WARNING]{Colors.RESET}"
    elif level == "ERROR": prefix = f"{Colors.BG_RED} #ERROR# {Colors.RESET}"
    elif level == "DEBUG": prefix = f"{Colors.BOLD}[DEBUG]{Colors.RESET}"
    else: prefix = f"[{level}]"
    print(f"{prefix} {message}")

def get_vc_version():
    """Lê a versão diretamente do pyproject.toml na raiz."""
    if not PYPROJECT_FILE.exists(): return "0.0.0"
    try:
        with open(PYPROJECT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version ="):
                    return line.split("=")[1].strip().replace('"', '').replace("'", "")
    except Exception: return "0.0.0"
    return "0.0.0"

# Executa validação ao carregar a biblioteca
ensure_env()