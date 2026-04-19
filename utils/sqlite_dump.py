import sqlite3
from pathlib import Path
from datetime import datetime
import fnmatch

# ======= FUNÇÕES AUXILIARES =======

def get_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    return [r[0] for r in rows]

def get_views(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='view' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
    return [r[0] for r in rows]

def get_triggers(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name").fetchall()
    return [r[0] for r in rows]

def get_create_sql(conn: sqlite3.Connection, name: str) -> str | None:
    row = conn.execute("SELECT sql FROM sqlite_master WHERE name=?", (name,)).fetchone()
    return row[0] if row and row[0] else None

def get_indexes(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name=? AND sql IS NOT NULL", (table,)).fetchall()
    return [r[0] for r in rows]

def get_select_statement(conn: sqlite3.Connection, name: str) -> str:
    """Gera um SELECT com todos os campos da tabela ou view, na ordem original."""
    try:
        cols = conn.execute(f"PRAGMA table_info('{name}')").fetchall()
        colnames = [c[1] for c in cols if c and c[1]]
        if not colnames:
            return f"-- não foi possível obter colunas de {name}"
        joined = ", ".join(colnames)
        return f"SELECT {joined} FROM {name}"
    except Exception:
        return f"-- erro ao montar SELECT para {name}"

def get_sample_md(conn: sqlite3.Connection, name: str, limit: int = 5) -> str:
    """Extrai uma amostra e converte para Markdown sem usar o Pandas."""
    try:
        cursor = conn.execute(f'SELECT * FROM "{name}" LIMIT {limit}')
        rows = cursor.fetchall()
        if not rows:
            return "*(sem linhas)*"
        
        cols = [desc[0] for desc in cursor.description]
        header = "| " + " | ".join(cols) + " |"
        separator = "| " + " | ".join(["---"] * len(cols)) + " |"
        
        table_lines = [header, separator]
        for row in rows:
            # Limpa quebras de linha que estragariam a tabela markdown
            cleaned_row = [str(item).replace('\n', ' ') if item is not None else 'NULL' for item in row]
            table_lines.append("| " + " | ".join(cleaned_row) + " |")
            
        return "\n".join(table_lines)
    except Exception as e:
        return f"*(Erro ao extrair amostra: {e})*"

def _matches(name: str, pattern: str | None) -> bool:
    if not pattern:
        return True
    py_pattern = pattern.replace("%", "*").lower()
    return fnmatch.fnmatch(name.lower(), py_pattern)

# ======= GERAÇÃO DO RELATÓRIO =======

def run_sqlite_dump(db_path: Path, dst_path: Path, limit: int = 5, name_pattern: str | None = None):
    """Lógica principal para gerar e salvar o Markdown."""
    if not db_path.exists():
        print(f"[ERRO] Arquivo SQLite não encontrado: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        tables = get_tables(conn)
        views = get_views(conn)
        triggers = get_triggers(conn)

        parts: list[str] = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        parts.append(f"# 🗄️ Relatório do Arquivo SQLite: {db_path.name}")
        parts.append(f"> _Gerado em: {now}_")
        parts.append(f"> _Linhas de amostra: **{limit}**_")
        if name_pattern:
            parts.append(f"> _Filtro aplicado: **{name_pattern}**_")
        parts.append("")

        if not name_pattern:
            parts.append(f"**Tabelas ({len(tables)}):** " + ", ".join(f"`{t}`" for t in tables))
            parts.append(f"**Views ({len(views)}):** " + ", ".join(f"`{v}`" for v in views))
            parts.append(f"**Triggers ({len(triggers)}):** " + ", ".join(f"`{tr}`" for tr in triggers))
            parts.append("\n---\n")

        # ======== TABELAS ========
        parts.append("## 1. Tabelas (definição, índices, uso e amostra)\n")
        filtered_tables = [t for t in tables if _matches(t, name_pattern)]
        if not filtered_tables:
            parts.append("_(sem tabelas para o filtro informado)_\n")

        for table in filtered_tables:
            parts.append(f"### 📊 `{table}`\n")
            create_sql = get_create_sql(conn, table)
            if create_sql:
                parts.append(f"```sql\n{create_sql}\n```\n")
            
            for idx_sql in get_indexes(conn, table):
                parts.append(f"```sql\n{idx_sql}\n```\n")

            parts.append(f"```sql\n{get_select_statement(conn, table)}\n```\n")
            parts.append(get_sample_md(conn, table, limit=limit))
            parts.append("\n---\n")

        # ======== VIEWS e TRIGGERS ========
        # (Lógica mantida compacta para Views e Triggers)
        parts.append("## 2. Views\n")
        for view in [v for v in views if _matches(v, name_pattern)]:
            parts.append(f"### 👁️ `{view}`\n")
            parts.append(f"```sql\n{get_create_sql(conn, view)}\n```\n")
            parts.append(f"```sql\n{get_select_statement(conn, view)}\n```\n")
            parts.append(get_sample_md(conn, view, limit=limit))
            parts.append("\n---\n")

        parts.append("## 3. Triggers\n")
        for trig in [tr for tr in triggers if _matches(tr, name_pattern)]:
            parts.append(f"### ⚡ `{trig}`\n")
            parts.append(f"```sql\n{get_create_sql(conn, trig)}\n```\n")
            parts.append("\n---\n")

        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text("\n".join(parts), encoding="utf-8")
        print(f"[SUCESSO] Markdown do SQLite gerado em: {dst_path}")

    finally:
        conn.close()

if __name__ == "__main__":
    import argparse
    
    # Resolve o caminho da raiz do projeto (sobe um nível de 'utils' para 'vc')
    ROOT_DIR = Path(__file__).resolve().parent.parent
    VAR_DIR = ROOT_DIR / "var"
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    
    parser = argparse.ArgumentParser(description="Gera relatório Markdown completo de um banco de dados SQLite.")
    parser.add_argument("--src", required=True, help="Caminho para o arquivo .db3 ou .sqlite de origem (obrigatório)")
    parser.add_argument("--dst", default=str(VAR_DIR / "relatorio_banco.md"), help="Arquivo .md de saída (padrão: var/relatorio_banco.md)")
    parser.add_argument("--limit", type=int, default=5, help="Número de linhas de amostra por tabela (padrão=5)")
    parser.add_argument("--name", help="Filtra tabelas/views por nome (aceita %% como curinga, ex: cfop%%)")
    
    args = parser.parse_args()
    
    src_path = Path(args.src).resolve()
    dst_path = Path(args.dst).resolve()
    
    if not src_path.exists():
        print(f"❌ Erro: O banco de dados '{src_path}' não foi encontrado.")
        sys.exit(1)
        
    print(f"🗄️ Inspecionando banco SQLite...")
    print(f"   Origem:  {src_path}")
    print(f"   Destino: {dst_path}")
    
    # NOTA: Adapte a chamada abaixo para o nome real da função principal
    # que faz a geração e salva o arquivo dentro do seu sqlite_dump.py
    # Exemplo: gerar_markdown_sqlite(src_path, dst_path, args.limit, args.name)