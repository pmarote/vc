import sys
from pathlib import Path
from datetime import datetime
from typing import List

# Configurações de exclusão e inclusão (Contrato Vibe Code)
IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", ".idea", ".vscode", "usr", "build", "dist", "var", "data"}
TARGET_EXTENSIONS = {".py", ".md", ".bat", ".json", ".sql", ".toml"}

def build_tree(root: Path) -> str:
    """Gera a representação visual da árvore de diretórios."""
    lines: List[str] = []
    def walk(dir_path: Path, prefix: str = "") -> None:
        try:
            entries = sorted([
                e for e in dir_path.iterdir() 
                if e.name not in IGNORE_DIRS
            ], key=lambda x: (x.is_file(), x.name))
        except PermissionError:
            lines.append(f"{prefix}├── [ERRO DE PERMISSÃO: {dir_path.name}]")
            return

        for i, entry in enumerate(entries):
            is_last = (i == len(entries) - 1)
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")
            if entry.is_dir():
                extension = "    " if is_last else "│   "
                walk(entry, prefix + extension)

    lines.append(root.name)
    walk(root)
    return "\n".join(lines)

def run_dump(root_path: Path, dst_path: Path):
    """Executa a consolidação de código para Markdown."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"# 🧠 CONTEXTO DO PROJETO: {root_path.name}", f"> Gerado em: {now}", ""]
    
    parts.append("## 1. 🌳 Estrutura de Diretórios\n```text")
    parts.append(build_tree(root_path))
    parts.append("```\n")

    collected = []
    for path in root_path.rglob('*'):
        if path.is_file() and path.suffix.lower() in TARGET_EXTENSIONS:
            if not any(part in IGNORE_DIRS for part in path.parts):
                collected.append(path)
    
    parts.append(f"## 2. 📦 Conteúdo dos Arquivos ({len(collected)} arquivos)\n")

    for file_path in sorted(collected):
        rel_path = file_path.relative_to(root_path).as_posix()
        ext = file_path.suffix.lower().replace(".", "")
        lang_map = {"py": "python", "md": "markdown", "bat": "batch", "json": "json", "sql": "sql", "toml": "toml"}
        lang = lang_map.get(ext, "text")

        parts.append(f"### 📄 `{rel_path}`\n```{lang}")
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = file_path.read_text(encoding="latin-1")
        parts.append(f"{content.strip()}\n```\n---\n")

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text("\n".join(parts), encoding="utf-8")
    print(f"[SUCESSO] Dump gerado em: {dst_path}")

if __name__ == "__main__":
    import argparse
    
    # Resolve o caminho da raiz do projeto (sobe um nível de 'utils' para 'vc')
    ROOT_DIR = Path(__file__).resolve().parent.parent
    VAR_DIR = ROOT_DIR / "var"
    
    # Garante que a pasta var existe para não dar erro ao salvar
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    
    parser = argparse.ArgumentParser(description="Gera consolidado Markdown de código-fonte para contexto de IA.")
    parser.add_argument("--root", default=str(ROOT_DIR), help="Pasta raiz para iniciar a leitura (padrão: raiz do projeto)")
    parser.add_argument("--dst", default=str(VAR_DIR / "contexto_projeto.md"), help="Arquivo de destino (padrão: var/contexto_projeto.md)")
    
    args = parser.parse_args()
    
    root_path = Path(args.root).resolve()
    dst_path = Path(args.dst).resolve()
    
    print(f"🧠 Gerando dump do código...")
    print(f"   Origem:  {root_path}")
    print(f"   Destino: {dst_path}")
    
    # Chama a função principal existente no arquivo
    run_dump(root_path, dst_path)
    print("✅ Dump finalizado com sucesso!")