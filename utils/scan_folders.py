import os
import argparse
from pathlib import Path
from datetime import datetime

def format_size(size_in_bytes):
    """Converte bytes para um formato legível (GB ou MB)."""
    gb = size_in_bytes / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.2f} GB"
    mb = size_in_bytes / (1024 ** 2)
    return f"{mb:.2f} MB"

def get_folder_sizes(root_dir):
    """
    Calcula o tamanho de cada pasta recursivamente usando os.walk.
    Propaga o tamanho dos arquivos para todas as pastas pai.
    """
    folder_sizes = {}
    root_path = os.path.abspath(root_dir)

    for dirpath, _, filenames in os.walk(root_path):
        current_dir_size = 0
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                # Ignora symlinks para evitar loop infinito ou contagem dupla
                if not os.path.islink(fp):
                    current_dir_size += os.path.getsize(fp)
            except (PermissionError, FileNotFoundError, OSError):
                continue
        
        # Se encontrou arquivos nesta pasta, propaga o peso para ela e seus ancestrais
        if current_dir_size > 0:
            parent = dirpath
            while True:
                folder_sizes[parent] = folder_sizes.get(parent, 0) + current_dir_size
                if parent == root_path:
                    break
                # Sobe um nível
                next_parent = os.path.dirname(parent)
                # Condição de saída extra caso atinja a raiz do drive
                if next_parent == parent:
                    break
                parent = next_parent

    return folder_sizes

def generate_markdown(folder_sizes, threshold_bytes, output_file, root_dir):
    """Filtra, ordena e gera o relatório em Markdown."""
    # Filtra pastas que atingiram o limite mínimo
    filtered_folders = {k: v for k, v in folder_sizes.items() if v >= threshold_bytes}
    
    # Ordena decrescente pelo tamanho
    sorted_folders = sorted(filtered_folders.items(), key=lambda item: item[1], reverse=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 📂 Relatório de Tamanho de Pastas\n\n")
        f.write(f"> 📅 **Gerado em:** `{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}`\n")
        f.write(f"> 🔍 **Diretório Alvo:** `{root_dir}`\n")
        f.write(f"> 📏 **Limite Mínimo:** `{format_size(threshold_bytes)}`\n\n")
        
        f.write("| Pasta | Tamanho |\n")
        f.write("| :--- | ---: |\n")
        
        if not sorted_folders:
            f.write("| _Nenhuma pasta excedeu o limite_ | - |\n")
        else:
            root_path_obj = Path(root_dir).resolve()
            for path_str, size in sorted_folders:
                path_obj = Path(path_str)
                # Tenta mostrar o caminho de forma limpa
                try:
                    display_path = str(path_obj.relative_to(root_path_obj))
                    if display_path == '.':
                        display_path = str(root_path_obj)
                except ValueError:
                    display_path = str(path_obj)
                    
                f.write(f"| `{display_path}` | **{format_size(size)}** |\n")

def main():
    parser = argparse.ArgumentParser(description="Gera um relatório Markdown das pastas que consomem mais espaço.")
    parser.add_argument("dir", help="Diretório inicial para a varredura (ex: F:/sef/result)")
    parser.add_argument("--out", default="var/rel_tamanho_pastas.md", help="Arquivo de saída (padrão: var/rel_tamanho_pastas.md)")
    parser.add_argument("--min", type=float, default=1.0, help="Tamanho mínimo em GB para listar (padrão: 1.0)")
    
    args = parser.parse_args()

    root_dir = args.dir
    if not os.path.isdir(root_dir):
        print(f"❌ Erro: Diretório '{root_dir}' não encontrado.")
        return

    threshold_bytes = args.min * (1024 ** 3)
    
    print(f"🔍 Escaneando '{root_dir}'...")
    print(f"📏 Buscando pastas maiores que {args.min} GB...")
    
    folder_sizes = get_folder_sizes(root_dir)
    
    # Garante que o diretório de saída exista
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    generate_markdown(folder_sizes, threshold_bytes, args.out, root_dir)
    
    print(f"✅ Concluído! Relatório gerado em: {args.out}")

if __name__ == "__main__":
    main()