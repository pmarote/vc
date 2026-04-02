import argparse
import sys
from pathlib import Path
from builder import construir_banco_sia
from reporter import gerar_relatorios

def main():
    parser = argparse.ArgumentParser(description="Gerador do Banco SIA e Relatórios.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # === Subcomando: build ===
    p_build = subparsers.add_parser("build", help="Gera o banco de dados SIA a partir do OSF.")
    p_build.add_argument("--src", required=True, help="Ficheiro OSF de origem (ex: ../data/osf123.sqlite)")
    p_build.add_argument("--out", required=True, help="Ficheiro SIA de destino (ex: ../var/sia123.sqlite)")
    p_build.add_argument("--excel", default="../sfia_safic/TrabPaulo.xlsm", help="Caminho do ficheiro de CFOPs")

    # === Subcomando: report ===
    p_report = subparsers.add_parser("report", help="Gera os relatórios MD a partir de uma pasta.")
    p_report.add_argument("--dir", required=True, help="Pasta que contém os bancos osf*.sqlite e sia*.sqlite")

    args = parser.parse_args()

    if args.command == "build":
        src_path = Path(args.src).resolve()
        out_path = Path(args.out).resolve()
        excel_path = Path(args.excel).resolve()

        if not src_path.exists():
            print(f"[ERRO] Ficheiro OSF não encontrado: {src_path}")
            sys.exit(1)

        print(f"🛠️ Iniciando a construção do banco SIA:\n ➔ OSF: {src_path.name}\n ➔ SIA: {out_path.name}")
        construir_banco_sia(src_path, out_path, excel_path)
        print("✅ Construção finalizada com sucesso.")

    elif args.command == "report":
        target_dir = Path(args.dir).resolve()
        
        if not target_dir.exists():
            print(f"[ERRO] Diretório não encontrado: {target_dir}")
            sys.exit(1)

        # Procura automaticamente os ficheiros na pasta
        try:
            db_osf = next(target_dir.glob("osf*.sqlite"))
            db_sia = next(target_dir.glob("sia*.sqlite"))
        except StopIteration:
            print(f"[ERRO] Não foi possível encontrar osf*.sqlite e/ou sia*.sqlite na pasta {target_dir}")
            sys.exit(1)

        print(f"📊 Bancos encontrados para relatório:\n ➔ OSF: {db_osf.name}\n ➔ SIA: {db_sia.name}")
        gerar_relatorios(str(db_osf), str(db_sia), target_dir)

if __name__ == "__main__":
    main()