"""
[SUB-ROTINA] MARKDOWN EXPORTER (v0.4.1)
Gera tabelas MD ricas a partir de um cursor SQLite.
Otimizado para memória: Não carrega tudo na RAM para alinhar pipes.
"""
import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

def fmt_br(val: Any) -> str:
    """Formata valores para o padrão brasileiro com suporte a cores HTML para negativos."""
    if val is None: return ""
    
    if isinstance(val, (float, int)):
        if isinstance(val, float):
            text_val = f"{val:_.2f}".replace('.', ',').replace('_', '.')
        else:
            text_val = str(val)
        return f'<span style="color:red">{text_val}</span>' if val < 0 else text_val
    
    # Tratamento seguro para strings em tabelas Markdown
    text_val = str(val)
    
    # 1. Substitui o | pelo código HTML para não criar colunas fantasmas
    if "|" in text_val:
        text_val = text_val.replace("|", "&#124;")
        
    # 2. Substitui quebras de linha por <br> para não criar linhas fantasmas
    if "\n" in text_val:
        text_val = text_val.replace("\n", "<br>").replace("\r", "")
        
    return text_val

def export_markdown(
    cursor: sqlite3.Cursor, 
    out_path: str, 
    sql_query: str = "", 
    db_path: str = "", 
    attachments: str = "", 
    title: Optional[str] = None,
    sql_file: str = "",
    mode: str = "w"  # Permite alternar entre escrever ('w') e adicionar ('a')
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

        # --- BLOCO METADADOS & SQL (ESCONDIDO NO TOPO) ---
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
        
        if not headers:
            f.write("> ⚠️ A consulta não retornou colunas.\n\n")
            return
            
        if not first_row:
            f.write("*Sem dados retornados para esta consulta.*\n\n")
            return

        # --- CONSTRUÇÃO DA TABELA ---
        # 1. Header Row
        f.write("| " + " | ".join(headers) + " |\n")

        # 2. Separator Row (Alinhamento)
        separators = []
        for i, _ in enumerate(headers):
            is_num = isinstance(first_row[i], (int, float)) if first_row else False
            separators.append("---:" if is_num else ":---")
        f.write("| " + " | ".join(separators) + " |\n")

        # 3. Write First Row (se existir)        
        row_count = 0
        if first_row:
            f.write("| " + " | ".join(fmt_br(c) for c in first_row) + " |\n")
            row_count += 1

        # 4. Write Remaining Rows (Streaming)            
        for row in cursor:
            f.write("| " + " | ".join(fmt_br(c) for c in row) + " |\n")
            row_count += 1

        # --- RODAPÉ MINIMALISTA ---
        f.write(f"\n> 📊 **Total de Registros:** {row_count}\n\n")


# --- MODO STANDALONE ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--sql", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--title", default="", help="Título do relatório")
    args = parser.parse_args()

    try:
        sql_file_name = ""
        sql_content = args.sql
        sql_path = Path(args.sql)
        
        if sql_path.exists() and sql_path.is_file():
            sql_file_name = sql_path.name
            sql_content = sql_path.read_text(encoding="utf-8")

        conn = sqlite3.connect(args.db)
        cursor = conn.cursor()
        
        cursor.execute(sql_content)
        
        export_markdown(
            cursor=cursor, 
            out_path=args.out, 
            sql_query=sql_content, 
            db_path=args.db,
            title=args.title,
            sql_file=sql_file_name
        )
        
        conn.close()
        sys.exit(0)
    except Exception as e:
        print(f"[ERRO MD] {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()