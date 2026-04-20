import sqlite3
import sys
import argparse
from pathlib import Path

# =========================================================================
# HELPER VISUAL: Imprimir tabelas em Markdown no terminal
# =========================================================================
def print_md_table(headers, rows):
    print("| " + " | ".join(headers) + " |")
    print("|" + "|".join(["---"] * len(headers)) + "|")
    for row in rows:
        print("| " + " | ".join(str(v) if v is not None else "" for v in row) + " |")
    print("\n")


# =========================================================================
# COMANDO: MAP (Gera o banco de relacionamentos)
# =========================================================================
def processar_banco(db_entrada: Path, db_saida: Path):
    if not db_entrada.exists():
        print(f"❌ Erro: O arquivo '{db_entrada}' não foi encontrado.")
        sys.exit(1)

    print(f"🗄️  Conectando ao banco de entrada: {db_entrada.name}")
    conn_in = sqlite3.connect(db_entrada)
    cursor_in = conn_in.cursor()

    print(f"💾 Criando/Atualizando banco de saída: {db_saida.name}")
    # Garante que a pasta de destino exista
    db_saida.parent.mkdir(parents=True, exist_ok=True)
    conn_out = sqlite3.connect(db_saida)
    cursor_out = conn_out.cursor()

    # 1. Cria a primeira tabela para consolidar o PRAGMA table_info
    cursor_out.execute('''
        CREATE TABLE IF NOT EXISTS schema_info (
            tbl_name TEXT,
            cid INTEGER,
            name TEXT,
            type TEXT,
            "notnull" INTEGER, 
            dflt_value TEXT,
            pk INTEGER
        )
    ''')
    cursor_out.execute('DELETE FROM schema_info') # Limpa caso o db de saída já exista

    # Obtém todas as tabelas do banco de entrada
    cursor_in.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor_in.fetchall()

    print(f" ➔ Extraindo metadados de {len(tabelas)} tabelas...")
    
    # 2. Lê o PRAGMA table_info de cada tabela e grava na tabela unificada
    for (tbl_name,) in tabelas:
        if tbl_name.startswith('sqlite_'):
            continue # Pula tabelas internas do SQLite
            
        cursor_in.execute(f'PRAGMA table_info("{tbl_name}")')
        colunas_info = cursor_in.fetchall()
        
        for col in colunas_info:
            # O retorno de col é: (cid, name, type, notnull, dflt_value, pk)
            cursor_out.execute('''
                INSERT INTO schema_info (tbl_name, cid, name, type, "notnull", dflt_value, pk)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (tbl_name,) + col)

    conn_out.commit()

    # 3. Cria a segunda tabela de relacionamentos (campo, pk, fk)
    cursor_out.execute('''
        CREATE TABLE IF NOT EXISTS relacionamentos (
            campo TEXT,
            pk TEXT,
            fk TEXT
        )
    ''')
    cursor_out.execute('DELETE FROM relacionamentos')

    print(" ➔ Calculando cruzamentos de chaves (cid=0 vs cid>0)...")

    # Pega todos os campos que são a primeira coluna de suas respectivas tabelas (PKs)
    cursor_out.execute("SELECT name, tbl_name FROM schema_info WHERE cid = 0")
    possiveis_pks = cursor_out.fetchall()

    for campo, tabela_pk in possiveis_pks:
        # Busca tabelas onde esse mesmo campo aparece, mas NÃO é a primeira coluna (FKs)
        cursor_out.execute('''
            SELECT tbl_name 
            FROM schema_info 
            WHERE name = ? AND cid > 0
        ''', (campo,))
        
        tabelas_fk = [row[0] for row in cursor_out.fetchall()]

        # Só insere no banco se houver correspondência (se a lista tabelas_fk não estiver vazia)
        if tabelas_fk:
            for tabela_fk in tabelas_fk:
                cursor_out.execute('''
                    INSERT INTO relacionamentos (campo, pk, fk) 
                    VALUES (?, ?, ?)
                ''', (campo, tabela_pk, tabela_fk))

    conn_out.commit()

    conn_in.close()
    conn_out.close()
    
    print(f"✅ Processamento finalizado! Banco salvo em: {db_saida.resolve()}")
    print(f"\\n💡 DICA: Você agora pode pesquisar os relacionamentos de uma tabela executando:")
    print(f"   vc utils mapeador_sqlite.py search --table NOME_DA_TABELA")


# =========================================================================
# COMANDO: SEARCH (Consulta o banco gerado)
# =========================================================================
def pesquisar_tabela(db_path: Path, tabela: str):
    if not db_path.exists():
        print(f"❌ Erro: O banco de mapeamento '{db_path}' não existe. Rode o comando 'map' primeiro.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print(f"\\n🔎 INICIANDO PESQUISA PARA A TABELA: `{tabela}`")
    print("=" * 60)
    print("O objetivo aqui é descobrir qual é a chave primária (primeiro campo) desta tabela")
    print("e listar todas as outras tabelas que utilizam este mesmo campo como chave estrangeira.\\n")

    # --- PASSO 1: Buscar na tabela de relacionamentos ---
    sql_relacionamentos = f"""SELECT campo, pk, fk 
FROM relacionamentos 
WHERE pk = '{tabela}'"""

    print("### 1. Busca Direta de Cruzamentos")
    print(f"Primeiro, consultamos a tabela `relacionamentos` para ver quem aponta para `{tabela}`.\\n")
    print(f"**SQL Executado:**\\n```sql\\n{sql_relacionamentos}\\n```\\n")

    cursor.execute("SELECT campo, pk, fk FROM relacionamentos WHERE pk = ?", (tabela,))
    linhas_rel = cursor.fetchall()

    if not linhas_rel:
        print(f"> ⚠️ A tabela `{tabela}` não possui relacionamentos mapeados ou não existe.\\n")
        conn.close()
        return

    # Imprime a tabela Markdown
    cabecalhos_rel = [desc[0] for desc in cursor.description]
    print_md_table(cabecalhos_rel, linhas_rel)

    # Identificando o nome do campo PK para o Passo 2
    campo_chave = linhas_rel[0][0]

    # --- PASSO 2: Buscar metadados consolidados no schema_info ---
    print("### 2. Detalhamento Estrutural das Chaves (PK e FKs)")
    print(f"Agora, vamos visualizar a estrutura física do campo `{campo_chave}`.")
    print("O SQL abaixo faz uma UNIÃO (UNION ALL) de duas buscas:")
    print("1. Traz a definição oficial do campo onde ele é a Chave Primária (cid = 0).")
    print("2. Traz a definição de onde ele aparece como Chave Estrangeira (cid > 0) nas demais tabelas.\\n")

    sql_schema = f"""SELECT tbl_name, cid, name, type, "notnull", dflt_value, pk 
FROM schema_info WHERE tbl_name = '{tabela}' AND cid = 0
UNION ALL
SELECT tbl_name, cid, name, type, "notnull", dflt_value, pk 
FROM schema_info WHERE name = '{campo_chave}' AND cid > 0"""

    print(f"**SQL Executado:**\\n```sql\\n{sql_schema}\\n```\\n")

    cursor.execute("""
        SELECT tbl_name, cid, name, type, "notnull", dflt_value, pk 
        FROM schema_info WHERE tbl_name = ? AND cid = 0
        UNION ALL
        SELECT tbl_name, cid, name, type, "notnull", dflt_value, pk 
        FROM schema_info WHERE name = ? AND cid > 0
    """, (tabela, campo_chave))
    
    linhas_schema = cursor.fetchall()
    cabecalhos_schema = [desc[0] for desc in cursor.description]
    
    # Imprime a tabela Markdown
    print_md_table(cabecalhos_schema, linhas_schema)

    conn.close()
    print("✅ Pesquisa concluída com sucesso!\\n")


# =========================================================================
# ENTRYPOINT (CLI)
# =========================================================================
if __name__ == "__main__":
    # Resolve o caminho da raiz do projeto (sobe um nível de 'utils' para 'vc')
    ROOT_DIR = Path(__file__).resolve().parent.parent
    VAR_DIR = ROOT_DIR / "var"
    VAR_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_DB = VAR_DIR / "mapeamento_chaves.sqlite"
    
    parser = argparse.ArgumentParser(description="Mapeador e Pesquisador de Relacionamentos (PK/FK) em banco SQLite.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- Subcomando: map ---
    p_map = subparsers.add_parser("map", help="Extrai o schema e gera o banco de relacionamentos")
    p_map.add_argument("--src", required=True, help="Caminho para o arquivo .sqlite de origem (obrigatório)")
    p_map.add_argument("--dst", default=str(DEFAULT_DB), help="Arquivo .sqlite de destino gerado (padrão: var/mapeamento_chaves.sqlite)")

    # --- Subcomando: search ---
    p_search = subparsers.add_parser("search", help="Pesquisa tabelas filhas a partir do nome de uma tabela pai")
    p_search.add_argument("--table", required=True, help="Nome exato da tabela que você quer investigar")
    p_search.add_argument("--db", default=str(DEFAULT_DB), help="Banco gerado pelo comando 'map' (padrão: var/mapeamento_chaves.sqlite)")

    args = parser.parse_args()
    
    if args.command == "map":
        src_path = Path(args.src).resolve()
        dst_path = Path(args.dst).resolve()
        processar_banco(src_path, dst_path)
        
    elif args.command == "search":
        db_path = Path(args.db).resolve()
        pesquisar_tabela(db_path, args.table)