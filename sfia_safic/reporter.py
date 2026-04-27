"""
Orquestrador de relatórios do sfia_safic.
Cada relatório vive em seu próprio módulo dentro de reports/.

Refatorado para utilizar a biblioteca central core.lib.vccore
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

# IMPORTANTE: Importando a biblioteca central do VC
import core.lib.vccore as vc

def gerar_relatorios(db_osf: Path, db_sia: Path, target_dir: Path, xls_dir: Path, debug: bool = False):
    db_osf = Path(db_osf)
    target_dir = Path(target_dir)
    
    vc.log(f"Conectando às bases e iniciando relatórios...", level="INFO")
    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()

    # Anexa OSF para relatórios que fazem JOIN entre DFe e DocAtrib
    cursor.execute(f"ATTACH DATABASE '{db_osf.as_posix()}' AS osf;")

    vc.log("Gerando Menu Principal...", level="INFO")
    gerar_menu_interativo(cursor, str(target_dir / "menu_relatorios.html"), debug=debug)

    vc.log("Gerando Básico...", level="INFO")
    gerar_rel_basicos(cursor, str(target_dir / "rel_basicos.md"), debug=debug)

    vc.log("Gerando Análise Econômica...", level="INFO")
    gerar_rel_an_econ(cursor, str(target_dir / "rel_an_econ.md"), debug=debug)

    vc.log("Gerando Conciliação DFe x EFD...", level="INFO")
    gerar_rel_conc(cursor, str(target_dir / "rel_conc.md"), debug=debug)

    vc.log("Gerando Exportações de Dados...", level="INFO")
    gerar_rel_exp_dados(cursor, str(target_dir / "rel_exp_dados.md"), limite=2, debug=debug)

    vc.log("Gerando MADF (GIA x EFD)...", level="INFO")
    gerar_rel_madf(cursor, str(target_dir / "rel_madf.md"), debug=debug)

    vc.log("Gerando Safic Menu (Resumo)...", level="INFO")
    gerar_rel_safic_menu(cursor, str(target_dir / "rel_safic_menu.md"), debug=debug)

    vc.log("Gerando Safic Menu (Detalhes)...", level="INFO")
    gerar_rel_safic_menu_det(cursor, str(target_dir / "rel_safic_menu_det.md"), xls_dir, debug=debug)

    conn.close()
    print(f"{vc.Colors.GREEN}✅ Todos os relatórios foram gerados com sucesso!{vc.Colors.RESET}")

def gerar_relatorio_operacoes(db_osf: Path, db_sia: Path, target_dir: Path, dbs_dir: Path, xls_dir: Path, debug: bool = False):
    vc.log("Gerando Relatório de Operações...", level="INFO")
    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{db_osf.as_posix()}' AS osf;")

    # Repassa as pastas específicas para o relatório colocar cada arquivo no seu lugar
    gerar_rel_oper(cursor, str(target_dir / "rel_oper.md"), dbs_dir, xls_dir, debug=debug)
    
    conn.close()
    print(f"{vc.Colors.GREEN}✅ Relatório rel_oper.md gerado com sucesso!{vc.Colors.RESET}")

def gerar_relatorio_itens(db_osf: Path, db_sia: Path, target_dir: Path, dbs_dir: Path, xls_dir: Path, debug: bool = False):
    vc.log("Gerando Relatório de Itens...", level="INFO")
    conn = sqlite3.connect(db_sia)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{db_osf.as_posix()}' AS osf;")

    # Repassa as pastas específicas para o relatório colocar cada arquivo no seu lugar
    gerar_rel_item(cursor, str(target_dir / "rel_item.md"), dbs_dir, xls_dir, debug=debug)
    
    conn.close()
    print(f"{vc.Colors.GREEN}✅ Relatório rel_item.md gerado com sucesso!{vc.Colors.RESET}")