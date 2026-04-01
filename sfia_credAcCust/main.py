import argparse
import sys
from pathlib import Path
from builder import construir_banco_siaCredAc
from reporter import gerar_relatorios

def main():
    parser = argparse.ArgumentParser(description="Gerador do Banco SIA e Relatórios - ECredAc Custeio.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # === Subcomando: build ===
    p_build = subparsers.add_parser("build", help="Gera o banco de dados SIA_Credac a partir dos arquivos de ECredAc Custeio.")
    p_build.add_argument("--src", required=True, help="Diretório Onde Estão os Arquivos Excel de Custeio")
    p_build.add_argument("--out", required=True, help="DB Sqlite SIA_CredAc de destino (ex: ../var/siaCredAc.sqlite)")

    # === Subcomando: report ===
    p_report = subparsers.add_parser("report", help="Gera os relatórios MD a partir de uma pasta.")
    p_report.add_argument("--dir", required=True, help="Pasta que contém os bancos osf*.sqlite, sia*.sqlite e siaCredAc*.sqlite")

    args = parser.parse_args()

    if args.command == "build":
        src_path = Path(args.src).resolve()
        out_path = Path(args.out).resolve()

        if not src_path.exists():
            print(f"[ERRO] Diretório dos Arquivos Excel de Custeio não encontrado: {src_path}")
            sys.exit(1)

        print(f"🛠️ Iniciando a construção do banco SIA_CredAc:\n ➔ Origem: {src_path.name}\n ➔ SIA_CredAc: {out_path.name}")
        construir_banco_siaCredAc(src_path, out_path)
        print("✅ Construção finalizada com sucesso.")

    elif args.command == "report":
        target_dir = Path(args.dir).resolve()
        
        if not target_dir.exists():
            print(f"[ERRO] Diretório não encontrado: {target_dir}")
            sys.exit(1)

        # Procura automaticamente os ficheiros na pasta
        try:
            db_siaCredAc = next(target_dir.glob("siaCredAc*.sqlite"))
            db_osf = next(target_dir.glob("osf*.sqlite"))
            db_sia = next(target_dir.glob("sia*.sqlite"))
        except StopIteration:
            print(f"[ERRO] Não foi possível encontrar osf*.sqlite, sia*.sqlite e/ou siaCredAc*.sqlite na pasta {target_dir}")
            sys.exit(1)

        print(f"📊 Bancos encontrados para relatório:\n ➔ OSF: {db_osf.name}\n ➔ SIA: {db_sia.name}\n ➔ SIA_CredAc: {db_siaCredAc.name}")
        gerar_relatorios(str(db_osf), str(db_sia), str(db_siaCredAc), target_dir)

if __name__ == "__main__":
    main()