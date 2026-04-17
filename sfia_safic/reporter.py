"""
Orquestrador de relatórios do sfia_safic.
Cada relatório vive em seu próprio módulo dentro de reports/.
"""
import re
import os
import sqlite3
from pathlib import Path

from reports.menu          import gerar_menu_interativo
from reports.basicos       import gerar_rel_basicos
from reports.an_econ       import gerar_rel_an_econ
from reports.conc          import gerar_rel_conc
from reports.exp_dados     import gerar_rel_exp_dados
from reports.madf          import gerar_rel_madf
from reports.safic_menu    import gerar_rel_safic_menu
from reports.safic_menu_det import gerar_rel_safic_menu_det
from reports.oper          import gerar_rel_oper
from reports.item          import gerar_rel_item

def gerar_relatorios(db_osf: str, db_sia: str, target_dir: Path, debug: bool = False):
    num_osf = re.sub(r'\D', '', os.path.basename(db_osf))
    if not num_osf:
        num_osf = "0"

    print(f"🗄️ Conectando às bases e iniciando relatórios (OSF {num_osf})...")
    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{db_osf}' AS osf;")

    print(" ➔ Gerando Menu Interativo...")
    gerar_menu_interativo(cursor, str(target_dir / "menu_relatorios.html"), num_osf, debug=debug)

    print(" ➔ Gerando Relatório de Dados Básicos...")
    gerar_rel_basicos(cursor, str(target_dir / "rel_basicos.md"), num_osf, debug=debug)
    
    print(" ➔ Gerando Análises Econômicas...")
    gerar_rel_an_econ(cursor, str(target_dir / "rel_an_econ.md"), debug=debug)

    print(" ➔ Gerando Relatórios de Conciliação...")
    gerar_rel_conc(cursor, str(target_dir / "rel_conc.md"), limite=5, debug=debug)

    print(" ➔ Gerando Exportações de Dados...")
    gerar_rel_exp_dados(cursor, str(target_dir / "rel_exp_dados.md"), limite=2, debug=debug)

    print(" ➔ Gerando Relatório MADF...")
    gerar_rel_madf(cursor, str(target_dir / "rel_madf.md"), debug=debug)

    print(" ➔ Gerando Safic Menu (Resumo)...")
    gerar_rel_safic_menu(cursor, str(target_dir / "rel_safic_menu.md"), debug=debug)

    print(" ➔ Gerando Safic Menu (Detalhes)...")
    gerar_rel_safic_menu_det(cursor, str(target_dir / "rel_safic_menu_det.md"), debug=debug)

    conn.close()
    print("✅ Todos os relatórios foram gerados com sucesso e guardados no diretório indicado!")

def gerar_relatorio_operacoes(db_osf: str, db_sia: str, target_dir: Path, debug: bool = False):
    print(f"🚀 Gerando Relatório de Operações...")
    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{db_osf}' AS osf;")

    gerar_rel_oper(cursor, str(target_dir / "rel_oper.md"), debug=debug)
    
    conn.close()
    print(f"✅ Relatório rel_oper.md gerado em {target_dir}")

def gerar_relatorio_itens(db_osf: str, db_sia: str, target_dir: Path, debug: bool = False):
    print(f"🚀 Preparando ambiente para Relatório de Itens...")
    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{db_osf}' AS osf;")

    gerar_rel_item(cursor, str(target_dir / "rel_item.md"), debug=debug)
    
    conn.close()
    print(f"✅ Relatório rel_item.md gerado em {target_dir}")