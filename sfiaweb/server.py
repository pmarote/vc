"""
sfiaweb/server.py — Servidor local VC (FastAPI)

Endpoints:
  GET  /                  → index.html (dashboard)
  GET  /md_viewer         → md-viewer-pm.html
  GET  /api/info          → work_dir + lista de bancos disponíveis
  GET  /api/ls/{subpath}  → listagem de diretório
  GET  /raw/{subpath}     → servir arquivo físico
  POST /api/query         → executar SQL e retornar JSON
  POST /api/export        → executar SQL e retornar arquivo (xlsx/md/tsv)
  POST /api/shutdown      → desligar servidor
"""

import os
import sys
import signal
import sqlite3
import time
import tomllib
import mimetypes
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="VC - sfiaweb")

# ---------------------------------------------------------------------------
# CAMINHOS BASE
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent   # raiz do monorepo (vc/)
SFIAWEB_DIR = Path(__file__).resolve().parent       # pasta sfiaweb/

# Adiciona o exportador ao sys.path para poder importar exporter.py
EXPORTADOR_DIR = ROOT_DIR / "exportador"
if str(EXPORTADOR_DIR) not in sys.path:
    sys.path.insert(0, str(EXPORTADOR_DIR))

try:
    from exporter import export_excel, export_markdown, export_tsv
    EXPORTER_AVAILABLE = True
except ImportError:
    EXPORTER_AVAILABLE = False


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def get_work_dir() -> Path:
    """Lê o work_dir do sfia_config.toml. Lança HTTPException se não encontrado."""
    config_path = ROOT_DIR / "var" / "sfia_config.toml"

    if not config_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Configuração não encontrada. Rode 'build' no sfia_safic primeiro."
        )

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    work_dir_str = config.get("work_dir", "")
    if not work_dir_str:
        raise HTTPException(status_code=503, detail="work_dir não definido no TOML.")

    work_dir = Path(work_dir_str)
    if not work_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Pasta de trabalho não encontrada: {work_dir}"
        )

    return work_dir.resolve()


def formatar_tamanho(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def listar_bancos(work_dir: Path) -> tuple[list[dict], str | None]:
    """
    Varre o work_dir (recursivamente dentro de _dbs/) em busca de bancos SQLite.
    Retorna (lista_de_bancos, caminho_do_banco_padrao).
    """
    banks = []
    default_bank = None

    # Procura em _dbs primeiro (estrutura padrão do sfia_safic)
    dbs_dir = work_dir / "_dbs"
    search_dirs = [dbs_dir] if dbs_dir.exists() else [work_dir]

    for search_dir in search_dirs:
        for p in sorted(search_dir.glob("*.sqlite")) + sorted(search_dir.glob("*.db3")):
            entry = {"name": p.name, "path": str(p)}
            banks.append(entry)
            # O banco sia*.sqlite é o padrão
            if p.name.startswith("sia") and default_bank is None:
                default_bank = str(p)

    # Fallback: usa o primeiro banco como padrão
    if banks and default_bank is None:
        default_bank = banks[0]["path"]

    return banks, default_bank


# ---------------------------------------------------------------------------
# ROTAS ESTÁTICAS
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def ler_index():
    index_path = SFIAWEB_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")


@app.get("/md_viewer", response_class=HTMLResponse)
def ler_md_viewer():
    viewer_path = SFIAWEB_DIR / "md-viewer-pm.html"
    if not viewer_path.exists():
        raise HTTPException(status_code=404, detail="md-viewer-pm.html não encontrado.")
    return viewer_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# API: INFO
# ---------------------------------------------------------------------------

@app.get("/api/info")
def api_info():
    """Retorna work_dir e lista de bancos disponíveis."""
    try:
        work_dir = get_work_dir()
        banks, default_bank = listar_bancos(work_dir)
        return {
            "work_dir": str(work_dir),
            "banks": banks,
            "default_bank": default_bank,
        }
    except HTTPException as e:
        return JSONResponse(status_code=e.status_code, content={"error": e.detail})


# ---------------------------------------------------------------------------
# API: LISTAGEM DE ARQUIVOS
# ---------------------------------------------------------------------------

@app.get("/api/ls/{subpath:path}")
def listar_arquivos(subpath: str = ""):
    try:
        base_dir = get_work_dir()
        target = (base_dir / subpath).resolve()

        if not target.is_relative_to(base_dir):
            raise HTTPException(status_code=403, detail="Acesso negado.")
        if not target.exists() or not target.is_dir():
            raise HTTPException(status_code=404, detail="Pasta não encontrada.")

        items = []
        for p in target.iterdir():
            stat = p.stat()
            items.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size": formatar_tamanho(stat.st_size) if p.is_file() else "",
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
            })

        items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return {"status": "ok", "path": subpath, "items": items}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# API: SERVIR ARQUIVO RAW
# ---------------------------------------------------------------------------

@app.get("/raw/{subpath:path}")
def ler_arquivo_raw(subpath: str):
    try:
        base_dir = get_work_dir()
        target = (base_dir / subpath).resolve()

        if not target.is_relative_to(base_dir):
            raise HTTPException(status_code=403, detail="Acesso negado.")
        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

        media_type, _ = mimetypes.guess_type(target)
        return FileResponse(target, media_type=media_type)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# API: QUERY SQL
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    db: str
    sql: str


@app.post("/api/query")
def api_query(req: QueryRequest):
    """
    Executa uma query SQL contra um banco e retorna os resultados como JSON.
    Limita automaticamente a 2000 linhas para não travar o browser.
    """
    db_path = Path(req.db)

    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Banco não encontrado: {db_path.name}")

    # Garante que o banco está dentro do work_dir ou _dbs (segurança básica)
    try:
        work_dir = get_work_dir()
        db_path.resolve().relative_to(work_dir)
    except (HTTPException, ValueError):
        raise HTTPException(status_code=403, detail="Acesso a este banco não é permitido.")

    sql = req.sql.strip()
    if not sql:
        raise HTTPException(status_code=400, detail="SQL vazio.")

    # Bloqueia comandos destrutivos por precaução
    sql_upper = sql.upper().lstrip()
    BLOCKED = ("DROP ", "DELETE ", "TRUNCATE ", "ALTER ", "INSERT ", "UPDATE ", "CREATE ", "ATTACH ")
    for cmd in BLOCKED:
        if sql_upper.startswith(cmd):
            raise HTTPException(
                status_code=400,
                detail=f"Comando '{cmd.strip()}' não permitido na query rápida. Use o exportador para operações de escrita."
            )

    LIMIT_ROWS = 2000
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        t0 = time.time()
        cursor.execute(sql)
        rows_raw = cursor.fetchmany(LIMIT_ROWS + 1)  # pega um a mais para detectar truncamento
        elapsed_ms = round((time.time() - t0) * 1000)

        truncated = len(rows_raw) > LIMIT_ROWS
        rows_raw = rows_raw[:LIMIT_ROWS]

        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in rows_raw]

        conn.close()

        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "truncated": truncated,
            "limit": LIMIT_ROWS,
            "elapsed_ms": elapsed_ms,
        }

    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Erro SQL: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# API: EXPORT (SQL → arquivo)
# ---------------------------------------------------------------------------

class AttachItem(BaseModel):
    path: str
    alias: str


class ExportRequest(BaseModel):
    db: str
    sql: str
    out: str                             # nome do arquivo de saída (ex: resultado.xlsx)
    attach: Optional[list[AttachItem]] = None


@app.post("/api/export")
def api_export(req: ExportRequest):
    """
    Executa SQL e retorna o arquivo gerado como download direto.
    Suporta .xlsx, .md e .txt/.tsv.
    Delega ao exporter.py do microapp exportador.
    """
    if not EXPORTER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Módulo exportador não disponível. Certifique-se de rodar 'uv sync' na pasta exportador/."
        )

    db_path = Path(req.db)
    if not db_path.exists():
        raise HTTPException(status_code=404, detail=f"Banco não encontrado: {db_path.name}")

    # Valida extensão
    out_name = req.out.strip() or "resultado.xlsx"
    ext = Path(out_name).suffix.lower()
    if ext not in (".xlsx", ".md", ".txt", ".tsv"):
        raise HTTPException(
            status_code=400,
            detail=f"Extensão '{ext}' não suportada. Use .xlsx, .md ou .txt"
        )

    # Arquivo de saída temporário na pasta var/temp
    temp_dir = ROOT_DIR / "var" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    out_path = temp_dir / out_name

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # ATTACH adicional
        attach_info = []
        if req.attach:
            for att in req.attach:
                att_path = Path(att.path).resolve()
                if not att_path.exists():
                    raise HTTPException(status_code=404, detail=f"Banco ATTACH não encontrado: {att_path.name}")
                cursor.execute(f"ATTACH DATABASE '{att_path.as_posix()}' AS {att.alias};")
                attach_info.append(f"{att.alias} ({att_path.name})")

        cursor.execute(req.sql.strip())

        if ext == ".xlsx":
            export_excel(cursor, out_path)
        elif ext == ".md":
            export_markdown(cursor, out_path, sql_query=req.sql, db_path=db_path.name,
                            attachments=", ".join(attach_info))
        else:  # .txt / .tsv
            export_tsv(cursor, out_path)

        conn.close()

        # Determina o media_type correto
        media_types = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".md":   "text/markdown",
            ".txt":  "text/plain",
            ".tsv":  "text/tab-separated-values",
        }
        media_type = media_types.get(ext, "application/octet-stream")

        return FileResponse(
            path=str(out_path),
            media_type=media_type,
            filename=out_name,
        )

    except HTTPException:
        raise
    except sqlite3.OperationalError as e:
        raise HTTPException(status_code=400, detail=f"Erro SQL: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# API: SHUTDOWN
# ---------------------------------------------------------------------------

@app.post("/api/shutdown")
def shutdown_server():
    os.kill(os.getpid(), signal.SIGINT)
    return {"status": "ok", "message": "Desligando..."}


# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------

def start_server(port: int):
    import uvicorn
    print(f"🚀 Iniciando VC sfiaweb na porta {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)
