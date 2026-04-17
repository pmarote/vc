# sfia_safic/reports/menu.py
import os
from pathlib import Path

def gerar_menu_interativo(cursor, out_path: Path, num_osf: str, debug=False):
    """
    Gera um Menu HTML Standalone com área editável para o auditor.
    """
    dir_out_path = os.path.dirname(out_path)
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Menu de Relatórios - OSF {num_osf}</title>
    <style>
        body {{ font-family: sans-serif; background: #f4f4f9; color: #333; padding: 10px; margin: auto; }}
        .painel {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 20px; }}
        .notas {{ min-height: 200px; padding: 15px; border: 1px dashed #ccc; background: #fffdf5; border-radius: 5px; outline: none; }}
        .notas:focus {{ border-color: #0d6efd; background: #fff; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ margin: 10px 0; padding: 10px; background: #eef2f5; border-radius: 5px; border-left: 4px solid #0d6efd; }}
        a {{ text-decoration: none; color: #0d6efd; font-weight: bold; }}
        .salvar-aviso {{ font-size: 0.8em; color: #666; margin-top: 5px; display: block; }}
    </style>
</head>
<body>
    <div class="painel">
        <h1>📑 Menu de Auditoria - OSF {num_osf}</h1>
        <p>Utilize o <strong>VC Reader</strong> (via DOSKEY <code>vcmd</code>) para abrir os relatórios abaixo:</p>
        <ul>
            <li><a href="rel_basicos.md" target="_blank">📄 Relatório de Dados Básicos</a></li>
            <li><a href="rel_an_econ.md" target="_blank">📈 Análises Econômicas</a></li>
            <li><a href="rel_conc.md" target="_blank">⚖️ Relatórios de Conciliação</a></li>
            <li><a href="rel_exp_dados.md" target="_blank">📦 Amostras de Exportações</a></li>
            <li><a href="rel_madf.md" target="_blank">📊 Relatório MADF</a></li>
            <li><a href="rel_safic_menu.md" target="_blank">📋 Análises do Safic (Resumo)</a></li>
            <li><a href="rel_safic_menu_det.md" target="_blank">🔍 Análises do Safic (Detalhes)</a></li>
        </ul>
    </div>

    <div class="painel">
        <h2>📝 Caderno de Notas do Auditor</h2>
        Report básico básico para exportador:<br>uv run main.py --db {dir_out_path}\sia{num_osf}.sqlite --sql "SELECT * FROM chaveNroTudao WHERE ChNrClassifs LIKE '%[12]%' LIMIT 10000" --out F:\sef\result\13009149244_Nakano\chNrTd_12.xlsx --attach {dir_out_path}\osf{num_osf}.sqlite osf
        <span class="salvar-aviso">⚠️ Dica: Digite suas notas abaixo e aperte <b>Ctrl + S</b> no navegador para salvar este arquivo HTML localmente com as alterações.</span>
        <br>
        <div class="notas" contenteditable="true">
            <i>Comece a digitar as suas constatações de auditoria aqui...algumas sugestões de marcação:<br>
            ✅🆗 Ok ✔️ "check" 👌 está tudo bem 👍 joinha<br>
            ❌✖️ erro 🚫 proibido<br>
            ⚠️ aviso 👎 deu errado<br>
            </i>
        </div>
    </div>
</body>
</html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)