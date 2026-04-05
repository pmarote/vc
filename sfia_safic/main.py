import argparse
import sys
from pathlib import Path
from builder import construir_banco_sia
from reporter import gerar_relatorios
from reporter import gerar_relatorio_operacoes

def main():
    parser = argparse.ArgumentParser(description="Gerador do Banco SIA e Relatórios.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # === Subcomando: build ===
    p_build = subparsers.add_parser("build", help="Gera o banco de dados SIA a partir do OSF.")
    p_build.add_argument("--src", required=True, help="Ficheiro OSF de origem (ex: ../data/osf123.sqlite)")
    p_build.add_argument("--out", required=True, help="Ficheiro SIA de destino (ex: ../var/sia123.sqlite)")
    p_build.add_argument("--excel", default="../sfia_safic/TrabPaulo.xlsm", help="Caminho do ficheiro de CFOPs")

    # === Subcomando: report ===
    p_report = subparsers.add_parser("report", help="Gera os relatórios MD padrão.")
    p_report.add_argument("--dir", required=True, help="Pasta que contém os bancos osf*.sqlite e sia*.sqlite")

    # === NOVO Subcomando: report_oper ===
    p_oper = subparsers.add_parser("report_oper", help="Gera o relatório de operações (rel_oper.md).")
    p_oper.add_argument("--dir", required=True, help="Pasta com os bancos de dados")

    # === NOVO Subcomando: report_item ===
    p_item = subparsers.add_parser("report_item", help="Gera o relatório de itens (rel_item.md) com aceleração via tabela item{osf}.sqlite.")
    p_item.add_argument("--dir", required=True, help="Pasta com os bancos de dados")

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

    elif args.command in ["report", "report_oper", "report_item"]:
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
        if args.command == "report":
            gerar_relatorios(str(db_osf), str(db_sia), target_dir)
        elif args.command == "report_oper":
            from reporter import gerar_relatorio_operacoes
            gerar_relatorio_operacoes(str(db_osf), str(db_sia), target_dir)
        elif args.command == "report_item":
            from reporter import gerar_relatorio_itens
            gerar_relatorio_itens(str(db_osf), str(db_sia), target_dir)

if __name__ == "__main__":
    main()