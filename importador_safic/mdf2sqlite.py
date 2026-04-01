import time
import sqlite3
import pythoncom
import win32com.client
from pathlib import Path

def type_adjust_sqlite(sqlsrv_type: int) -> str:
    """Mapeia os tipos numéricos do ADODB para tipos do SQLite."""
    a_int = [2, 3, 11, 16, 17, 18, 19, 20, 21, 128, 136, 204, 205]
    a_real = [4, 5, 6, 14, 64, 131, 139]
    a_blob_null = [0, 9, 10, 12, 13]
    
    if sqlsrv_type in a_int: return 'INT'
    if sqlsrv_type in a_real: return 'REAL'
    if sqlsrv_type in a_blob_null: return 'BLOB'
    return 'TEXT'

def convert_mdf_to_sqlite(mdf_path: Path, ldf_path: Path, out_path: Path, server_name: str):
    print(f"\n🚀 Iniciando conversão bruta: {mdf_path.name} -> {out_path.name}")
    pythoncom.CoInitialize()
    db = win32com.client.Dispatch('ADODB.Connection')
    temp_db_name = f"SAFIC_TEMP_{int(time.time())}"
    
    conn_str = f"Provider=MSOLEDBSQL;Data Source={server_name};Integrated Security=SSPI;"
    db.Open(conn_str)

    try:
        print(f"🔗 Anexando banco {temp_db_name} no LocalDB...")
        db.Execute(f"CREATE DATABASE [{temp_db_name}] ON (FILENAME = '{mdf_path.resolve()}'), (FILENAME = '{ldf_path.resolve()}') FOR ATTACH")
        
        db.Close()
        db.Open(conn_str + f"Initial Catalog={temp_db_name};")

        rs = db.Execute("SELECT name FROM sys.tables WHERE is_ms_shipped = 0")[0]
        tables = []
        while not rs.EOF:
            tables.append(rs.Fields.Item("name").Value)
            rs.MoveNext()

        if out_path.exists():
            out_path.unlink()
            
        sqlite_conn = sqlite3.connect(out_path)
        
        for i, table in enumerate(tables, 1):
            print(f"   [{i}/{len(tables)}] Copiando {table}...", end="", flush=True)
            rs = db.Execute(f"SELECT * FROM [{table}]")[0]
            
            n_cols = rs.Fields.Count
            cols_def = [f"[{rs.Fields.Item(j).Name}] {type_adjust_sqlite(rs.Fields.Item(j).Type)}" for j in range(n_cols)]
            sqlite_conn.execute(f"CREATE TABLE [{table}] ({', '.join(cols_def)})")
            
            batch = []
            while not rs.EOF:
                row = []
                for j in range(n_cols):
                    val = rs.Fields.Item(j).Value
                    if hasattr(val, "isoformat"):
                        val = val.isoformat(sep=' ')
                    elif isinstance(val, str) and ',' in val:
                        try: val = float(val.replace(',', '.'))
                        except ValueError: pass
                    row.append(val)
                batch.append(tuple(row))
                rs.MoveNext()

            if batch:
                placeholders = ", ".join(["?"] * n_cols)
                sqlite_conn.execute("BEGIN;")
                sqlite_conn.executemany(f"INSERT INTO [{table}] VALUES ({placeholders})", batch)
                sqlite_conn.execute("COMMIT;")
            
            print(" ✅")

    finally:
        print("🧹 Desanexando do LocalDB...")
        sqlite_conn.close()
        db.Close()
        time.sleep(1)
        db_detach = win32com.client.Dispatch('ADODB.Connection')
        db_detach.Open(conn_str)
        try:
            db_detach.Execute(f"EXEC sp_detach_db '{temp_db_name}'")
        except Exception as e:
            print(f"   [AVISO] Erro ao desanexar: {e}")
        db_detach.Close()
        pythoncom.CoUninitialize()