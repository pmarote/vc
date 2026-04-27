"""
core/lib/to_markdown.py

[SUB-ROTINA] MARKDOWN EXPORTER
Gera tabelas MD ricas a partir de um cursor SQLite.
Também faz log de execução em query_history.sqlite.
Otimizado para memória: Não carrega tudo na RAM para alinhar pipes.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from decimal import Decimal
from typing import Any, Optional

# IMPORTANTE: Importando a biblioteca central do VC
import core.lib.vccore as vc

def _registrar_historico_sql(out_path: str, sql_query: str, db_path: str, attachments: str, title: str, sql_file: str, row_count: int):
    """
    Grava o log da execução em um banco SQLite de histórico.
    Aplica a lógica de diretório solicitada.
    """
    try:
        p_out = Path(out_path).resolve()
        out_dir = p_out.parent
        root_dir = out_dir.parent
        
        # Lógica de localização: prioriza a pasta _dbs do projeto
        if (root_dir / "_dbs").exists():
            hist_dir = root_dir / "_dbs"
        else:
            hist_dir = out_dir
            
        hist_db_path = hist_dir / "query_history.sqlite"
        
        conn = sqlite3.connect(hist_db_path)
        cursor = conn.cursor()
        
        # Cria a tabela caso não exista
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                sql_query TEXT,
                db_path TEXT,
                attachments TEXT,
                title TEXT,
                sql_file TEXT,
                row_count INTEGER,
                out_path TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO history (timestamp, sql_query, db_path, attachments, title, sql_file, row_count, out_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            sql_query,
            str(db_path),
            str(attachments),
            title,
            sql_file,
            row_count,
            str(out_path)
        ))
        
        conn.commit()
        conn.close()
    except Exception as e:
        # Silencioso para não interromper a geração do relatório, 
        # apenas avisa no terminal usando o padrao de log do vccore
        vc.log(f"Não foi possível registrar o histórico SQL: {e}", level="WARNING")


def fmt_br(val: Any) -> str:
    """Formata valores para o padrão brasileiro com suporte a cores HTML para negativos."""
    if val is None: return ""

    # Tratamento bool
    if isinstance(val, bool):
        return "True" if val else "False"
    
    # Tratamento Numérico
    if isinstance(val, (float, int, Decimal)):
        if isinstance(val, int):
            text_val = str(val)
        else:
            text_val = f"{val:_.2f}".replace('.', ',').replace('_', '.')
        return f'<span style="color:red">{text_val}</span>' if val < 0 else text_val
    
    # Tratamento seguro para strings em tabelas Markdown
    text_val = str(val)
    
    # 1. Escapa HTML acidental (crucial para o navegador não esconder dados)
    text_val = text_val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # 2. Substitui o | pelo código HTML para não criar colunas fantasmas
    text_val = text_val.replace("|", "&#124;")
        
    # 3. Substitui quebras de linha por <br> para não criar linhas fantasmas
    text_val = text_val.replace("\r", "")
    text_val = text_val.replace("\n", "<br>")
        
    return text_val


def export_markdown(
    cursor: sqlite3.Cursor, 
    out_path: str, 
    sql_query: str = "", 
    db_path: str = "", 
    attachments: str = "", 
    title: Optional[str] = None,
    sql_file: str = "",
    mode: str = "w",  # Permite alternar entre escrever ('w') e adicionar ('a')
    show_meta: bool = False  
) -> None:
    """
    Gera Markdown streamando o cursor.
    Nota: O arquivo .md bruto não terá colunas alinhadas visualmente (espaços),
    mas o render (HTML/GitHub) ficará perfeito. Isso economiza RAM.
    """
    headers = [desc[0] for desc in cursor.description] if cursor.description else []
    first_row = cursor.fetchone()
    
    with open(out_path, mode, encoding="utf-8") as f:
        if title:
            f.write(f"## {title}\n\n")

        # --- BLOCO METADADOS & SQL ---
        if show_meta:
            f.write('<details>\n  <summary><span style="font-size:0.9em; color:gray; cursor:pointer">🔍 Detalhes da Execução e Query SQL</span></summary>\n\n')
            data_hora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            f.write(f"> 📅 **Gerado em:** `{data_hora}`\n")
            if db_path:
                f.write(f"> 🗄️ **Base Principal:** `{db_path}`\n")
            if attachments:
                f.write(f"> 🔗 **Anexos:** `{attachments}`\n")
            if sql_file:
                f.write(f"> 📄 **Arquivo SQL:** `{sql_file}`\n")
            if sql_query:
                f.write(f"\n```sql\n{sql_query.strip()}\n```\n")
            f.write("</details>\n\n")

        row_count = 0
        
        if not headers:
            f.write("> ⚠️ A consulta não retornou colunas.\n\n")
        elif not first_row:
            f.write("*Sem dados retornados para esta consulta.*\n\n")
        else:
            # --- CONSTRUÇÃO DA TABELA ---
            # 1. Header Row
            f.write("| " + " | ".join(headers) + " |\n")

            # 2. Separator Row (Alinhamento)
            separators = []
            for i, _ in enumerate(headers):
                is_num = isinstance(first_row[i], (int, float)) if first_row else False
                separators.append("---:" if is_num else ":---")
            f.write("| " + " | ".join(separators) + " |\n")

            # 3. Write First Row
            f.write("| " + " | ".join(fmt_br(c) for c in first_row) + " |\n")
            row_count += 1

            # 4. Write Remaining Rows (Streaming)            
            for row in cursor:
                f.write("| " + " | ".join(fmt_br(c) for c in row) + " |\n")
                row_count += 1

            # --- RODAPÉ MINIMALISTA ---
            if show_meta:
                f.write(f"\n> 📊 **Total de Registros:** {row_count}\n\n")

        # Em qualquer hipótese (com ou sem erro/dados), registra o log
        _registrar_historico_sql(
            out_path=out_path,
            sql_query=sql_query,
            db_path=db_path,
            attachments=attachments,
            title=title,
            sql_file=sql_file,
            row_count=row_count
        )