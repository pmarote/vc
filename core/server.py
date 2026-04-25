"""
sfiaweb/server.py — Servidor local VC (FastAPI) v0.4.9

Novidades v0.4.9:
  - Gestão de pastas _tmpl e var/temp.
  - Endpoint de listagem para o Launchpad.
  - API de mtime para Hot Reload (sem cache).
  - Montagem de rotas estáticas para acesso direto.
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

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional, List
import subprocess

# Importa o namespace centralizado
import core.lib.vccore as vc

app = FastAPI(title="VC - sfiaweb v0.4.9")

# ---------------------------------------------------------------------------
# CAMINHOS BASE E CONFIGURAÇÃO DE DIRETÓRIOS
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
SFIAWEB_DIR = Path(__file__).resolve().parent

# O work_dir será definido na inicialização (start_server)
work_dir = None
MDS_DIR = None
TMPL_DIR = None
TEMP_DIR = None

def setup_work_dir(path: str):
    """Configura e garante a estrutura de pastas do work_dir v0.4.9."""
    global work_dir, MDS_DIR, TMPL_DIR, TEMP_DIR
    work_dir = Path(path).resolve()
    MDS_DIR = work_dir / "_mds"
    TMPL_DIR = work_dir / "_tmpl"
    TEMP_DIR = work_dir / "var" / "temp"

    # Garantir que as pastas existam
    TMPL_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    MDS_DIR.mkdir(parents=True, exist_ok=True)

    # Montar rotas estáticas para acesso via interface web
    app.mount("/mds", StaticFiles(directory=str(MDS_DIR)), name="mds")
    app.mount("/tmpl", StaticFiles(directory=str(TMPL_DIR)), name="tmpl")
    app.mount("/temp", StaticFiles(directory=str(TEMP_DIR)), name="temp")

    # A pasta static para usar os PNGs no HTML se quiser:
    app.mount("/static", StaticFiles(directory=str(vc.STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# API: MONITORAMENTO E LISTAGEM (v0.4.9)
# ---------------------------------------------------------------------------

@app.get("/api/files/list")
async def list_files():
    """Lista arquivos para o Launchpad organizar por categorias."""
    try:
        return {
            "templates": [f.name for f in TMPL_DIR.glob("*.tmpl.md")],
            "reports": [f.name for f in MDS_DIR.glob("*.md")],
            "temp": [f.name for f in TEMP_DIR.iterdir() if f.is_file()],
            "work_dir": str(work_dir)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mtime/{folder}/{filename}")
async def get_mtime(folder: str, filename: str):
    """Retorna o timestamp de modificação para evitar cache (Hot Reload)."""
    base_paths = {
        "mds": MDS_DIR,
        "temp": TEMP_DIR,
        "tmpl": TMPL_DIR
    }
    
    if folder not in base_paths:
        raise HTTPException(status_code=400, detail="Pasta inválida")
    
    filepath = base_paths[folder] / filename
    if filepath.exists():
        return {"mtime": filepath.stat().st_mtime}
    return {"mtime": 0}

# ---------------------------------------------------------------------------
# ROTAS DE INTERFACE E EXPLORAÇÃO (EXISTENTES)
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def get_index():
    index_path = SFIAWEB_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = vc.STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    raise HTTPException(status_code=404)

@app.get("/md_viewer", response_class=HTMLResponse)
def get_md_viewer():
    viewer_path = SFIAWEB_DIR / "md-viewer-pm.html"
    return viewer_path.read_text(encoding="utf-8")

@app.get("/api/info")
def get_info():
    dbs_path = work_dir / "_dbs"
    dbs = [f.name for f in dbs_path.glob("*.sqlite")] if dbs_path.exists() else []
    return {
        "work_dir": str(work_dir),
        "dbs": dbs,
        "version": "0.4.9"
    }

# ---------------------------------------------------------------------------
# API: CONSULTAS SQL E EXPORTAÇÃO
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    db_name: str
    sql: str

@app.post("/api/query")
def execute_query(req: QueryRequest):
    db_path = work_dir / "_dbs" / req.db_name
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Banco de dados não encontrado")
    
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(req.sql)
        rows = cursor.fetchall()
        
        result = [dict(row) for row in rows]
        conn.close()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ---------------------------------------------------------------------------
# API: TERMINAL WEB (v0.4.9)
# ---------------------------------------------------------------------------

@app.get("/terminal", response_class=HTMLResponse)
def get_terminal():
    """Serve a página do Terminal Web."""
    terminal_path = SFIAWEB_DIR / "terminal.html"
    if not terminal_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo terminal.html não encontrado.")
    return terminal_path.read_text(encoding="utf-8")

# sfiaweb/server.py (Substituir o bloco do /ws/terminal)

@app.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    await websocket.accept()
    current_dir = work_dir
    
    def get_prompt():
        return f"\r\n\x1b[1;34mVC\x1b[0m:\x1b[1;32m{current_dir.name}\x1b[0m> "

    await websocket.send_text("💻 Shell VC Iniciado. Operando via asyncio (Zero Deps).\r\n")
    await websocket.send_text(get_prompt())

    try:
        while True:
            cmd = await websocket.receive_text()
            cmd = cmd.strip()

            if not cmd:
                await websocket.send_text(get_prompt())
                continue

            if cmd.lower().startswith("cd "):
                new_dir = cmd[3:].strip()
                target = (current_dir / new_dir).resolve()
                if target.exists() and target.is_dir():
                    current_dir = target
                else:
                    await websocket.send_text(f"Diretório não encontrado: {new_dir}")
                await websocket.send_text(get_prompt())
                continue

            # ==========================================
            # 1. EMULADOR DE MACROS (Doskey)
            # ==========================================
            if cmd.startswith("vc "):
                # Redireciona o 'vc' para usar o uv no monorepo
                cmd = f"uv run --directory {ROOT_DIR} " + cmd[3:]
            elif cmd == "vcdir":
                if os.name == 'nt':
                    cmd = f'dir /B /A:D "{ROOT_DIR}" | findstr /V "var"'
                else:
                    cmd = f'ls -d "{ROOT_DIR}"/*/'
            elif cmd.startswith("sqlite2md"):
                cmd = f"uv run --directory {ROOT_DIR}/utils main.py " + cmd
            elif cmd.lower() in ["cls", "clear"]:
                # Atalho extra: Limpa a tela do Xterm.js perfeitamente
                await websocket.send_text("\x1b[2J\x1b[3J\x1b[H")
                await websocket.send_text(get_prompt())
                continue

            # ==========================================
            # 2. CORREÇÃO DE ENCODING (Baseado no terminal.bat)
            # ==========================================
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"  # Força Python a usar UTF-8
            
            if os.name == 'nt':
                # Injeta chcp 65001 silenciosamente antes de rodar o comando
                cmd_to_run = f"chcp 65001 >nul & {cmd}"
            else:
                cmd_to_run = cmd

            try:
                process = await asyncio.create_subprocess_shell(
                    cmd_to_run,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    cwd=str(current_dir),
                    env=env
                )

                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    
                    text = line.decode('utf-8', errors='replace').replace('\n', '\r\n')
                    if not text.endswith('\r\n'):
                        text += '\r\n'
                    await websocket.send_text(text)

                await process.wait()
            except Exception as e:
                await websocket.send_text(f"\x1b[31mErro de execução: {str(e)}\x1b[0m\r\n")

            await websocket.send_text(get_prompt())

    except WebSocketDisconnect:
        pass

# ---------------------------------------------------------------------------
# API: EDITOR MONACO E COMPILAÇÃO DE TEMPLATES (v0.4.9)
# ---------------------------------------------------------------------------

class FileSaveRequest(BaseModel):
    filename: str
    content: str

class CompileRequest(BaseModel):
    filename: str

@app.get("/editor", response_class=HTMLResponse)
def get_editor():
    """Serve a página do Editor Monaco."""
    editor_path = SFIAWEB_DIR / "md-editor-pm.html"
    if not editor_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo md-editor-pm.html não encontrado.")
    return editor_path.read_text(encoding="utf-8")

@app.get("/api/file/read")
async def read_file(file: str):
    """Lê o conteúdo de um template na pasta _tmpl."""
    filepath = TMPL_DIR / file
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
    return {"content": filepath.read_text(encoding="utf-8")}

@app.post("/api/file/write")
async def write_file(req: FileSaveRequest):
    """Salva o conteúdo no template original."""
    filepath = TMPL_DIR / req.filename
    filepath.write_text(req.content, encoding="utf-8")
    return {"status": "ok"}

@app.post("/api/compile")
async def compile_template(req: CompileRequest):
    """Aciona o microapp sfia_safic para compilar o template."""
    # Monta o comando isolado para o uv run
    cmd = f"uv run --directory \"{ROOT_DIR}/sfia_safic\" main.py template --file \"{req.filename}\""
    
    # Força a compilação garantindo o UTF-8
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(work_dir),
            env=env
        )
        stdout, _ = await process.communicate()
        output = stdout.decode('utf-8', errors='replace')
        
        if process.returncode != 0:
            return {"status": "error", "output": output}
        return {"status": "ok", "output": output}
        
    except Exception as e:
        return {"status": "error", "output": str(e)}


# ... (Manter lógica de POST /api/export e POST /api/shutdown conforme arquivo anterior)

# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------

def start_server(port: int, work_dir_path: str):
    import uvicorn
    setup_work_dir(work_dir_path)
    print(f"🚀 VC Server v0.4.9 iniciado em http://127.0.0.1:{port}")
    print(f"📁 WorkDir: {work_dir}")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    # Exemplo de uso manual para teste
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5678)
    parser.add_argument("--dir", type=str, required=True)
    args = parser.parse_args()
    
    start_server(args.port, args.dir)