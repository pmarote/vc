"""
sfiaweb/server.py — Servidor local VC (FastAPI)

Novidades
  - Refatorado para utilizar core.lib.vccore (vc).
  - Gestão de pastas _tmpl e var/temp centralizada na raiz.
  - Endpoint de listagem para o Launchpad.
  - API de mtime para Hot Reload (sem cache).
  - Montagem de rotas estáticas para acesso direto.
"""

import os
import sqlite3
from pathlib import Path

import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import signal

# Importa o namespace centralizado
import core.lib.vccore as vc

app = FastAPI(title="VC - Central Web")

# ---------------------------------------------------------------------------
# CAMINHOS BASE E CONFIGURAÇÃO DE DIRETÓRIOS
# ---------------------------------------------------------------------------
# As constantes ROOT, TEMP, e STATIC agora são consumidas diretamente de vc.

# Variáveis globais dinâmicas baseadas no work_dir (pasta da auditoria)
work_dir = None
MDS_DIR = None
TMPL_DIR = None

def setup_work_dir(path: str):
    """Configura e garante a estrutura de pastas do work_dir"""
    global work_dir, MDS_DIR, TMPL_DIR
    work_dir = Path(path).resolve()
    
    # Pelas regras de ouro, essas pastas começam com underscore
    MDS_DIR = work_dir / "_mds"
    TMPL_DIR = work_dir / "_tmpl"

    # Garantir que as pastas existam
    TMPL_DIR.mkdir(parents=True, exist_ok=True)
    MDS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Nota: a vc.TEMP_DIR já é garantida na inicialização do vc.ensure_env()

    # Montar rotas estáticas para acesso via interface web
    app.mount("/mds", StaticFiles(directory=str(MDS_DIR)), name="mds")
    app.mount("/tmpl", StaticFiles(directory=str(TMPL_DIR)), name="tmpl")
    app.mount("/temp", StaticFiles(directory=str(vc.TEMP_DIR)), name="temp")

    # A pasta static para usar os PNGs no HTML
    app.mount("/static", StaticFiles(directory=str(vc.STATIC_DIR)), name="static")

# ---------------------------------------------------------------------------
# API: MONITORAMENTO E LISTAGEM
# ---------------------------------------------------------------------------

@app.get("/api/files/list")
async def list_files():
    """Lista arquivos com seus caminhos de rota (mount points) para o Launchpad."""
    try:
        return {
            # Edição de template, por enquanto, somente dentro da pasta _tmpl (veja async def read_file(file: str): e save_file em seguida)
            "templates": [f.name for f in TMPL_DIR.glob("*.tmpl.md")],
            # Injetamos o prefixo da rota web antes do nome do arquivo
            "reports": [f"/mds/{f.name}" for f in MDS_DIR.glob("*.md")],
            "temp": [f"/temp/{f.name}" for f in vc.TEMP_DIR.iterdir() if f.is_file()],
            "work_dir": str(work_dir)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/mtime/{folder}/{filename}")
async def get_mtime(folder: str, filename: str):
    """Retorna o timestamp de modificação para evitar cache (Hot Reload)."""
    base_paths = {
        "mds": MDS_DIR,
        "temp": vc.TEMP_DIR,
        "tmpl": TMPL_DIR
    }
    
    if folder not in base_paths:
        raise HTTPException(status_code=400, detail="Pasta inválida")
    
    filepath = base_paths[folder] / filename
    if filepath.exists():
        return {"mtime": filepath.stat().st_mtime}
    return {"mtime": 0}

# ---------------------------------------------------------------------------
# ROTAS DE INTERFACE E EXPLORAÇÃO
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
def get_index():
    index_path = vc.CORE_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")

@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    favicon_path = vc.STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(favicon_path)
    raise HTTPException(status_code=404)

@app.get("/md_viewer", response_class=HTMLResponse)
def get_md_viewer():
    viewer_path = vc.CORE_DIR / "md-viewer-pm.html"
    return viewer_path.read_text(encoding="utf-8")

@app.get("/api/info")
def get_info():
    dbs_path = work_dir / "_dbs"
    dbs = [f.name for f in dbs_path.glob("*.sqlite")] if dbs_path.exists() else []
    return {
        "work_dir": str(work_dir),
        "dbs": dbs,
        "version": vc.get_vc_version()
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
# API: TERMINAL WEB
# ---------------------------------------------------------------------------

@app.get("/terminal", response_class=HTMLResponse)
def get_terminal():
    """Serve a página do Terminal Web."""
    terminal_path = vc.CORE_DIR / "terminal.html"
    if not terminal_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo terminal.html não encontrado.")
    return terminal_path.read_text(encoding="utf-8")

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

            # O comando 'cd' continua precisando ser interceptado pois ele altera o 
            # estado do diretório atual da nossa sessão do websocket
            if cmd.lower().startswith("cd "):
                new_dir = cmd[3:].strip()
                target = (current_dir / new_dir).resolve()
                if target.exists() and target.is_dir():
                    current_dir = target
                else:
                    await websocket.send_text(f"Diretório não encontrado: {new_dir}")
                await websocket.send_text(get_prompt())
                continue

            # O 'cls' também é interceptado pois ele limpa a interface visual do navegador
            if cmd.lower() in ["cls", "clear"]:
                await websocket.send_text("\x1b[2J\x1b[3J\x1b[H")
                await websocket.send_text(get_prompt())
                continue

            # ==========================================
            # CORREÇÃO DE AMBIENTE E PATH 
            # ==========================================
            env = os.environ.copy()
            env["PYTHONUTF8"] = "1"  # Força Python a usar UTF-8
            
            # 1. Ajuste do PATH (Mantendo a sua sacada brilhante)
            path_parts = env.get("PATH", "").split(os.pathsep)
            core_scripts_path = str(vc.CORE_DIR / "Scripts")
            # 2. Remove o core\Scripts da posição atual para evitar duplicidade
            # Usamos normpath para evitar problemas com barras invertidas/normais no Windows
            path_parts = [p for p in path_parts if os.path.normpath(p) != os.path.normpath(core_scripts_path)]
            # 3. Insere o core\Scripts rigorosamente na posição 0 (Primeiro)
            path_parts.insert(0, core_scripts_path)
            # 4. Reconstrói a variável PATH
            env["PATH"] = os.pathsep.join(path_parts)

            # ==========================================
            # NOVIDADE: SANITIZAÇÃO DO AMBIENTE VIRTUAL
            # ==========================================
            # Remove o rastro do ambiente 'core' para não confundir o uv em outros microapps
            env.pop("VIRTUAL_ENV", None)
            
            # Remove o executável do UV e travas de recursão (UV_RUN_RECURSION_DEPTH, etc)
            uv_keys = [k for k in env.keys() if k.startswith("UV")]
            for k in uv_keys:
                env.pop(k, None)

            # Execução do comando
            if os.name == 'nt':
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
# API: EDITOR MONACO E COMPILAÇÃO DE TEMPLATES
# ---------------------------------------------------------------------------

class FileSaveRequest(BaseModel):
    filename: str
    content: str

class CompileRequest(BaseModel):
    filename: str

@app.get("/editor", response_class=HTMLResponse)
def get_editor():
    """Serve a página do Editor Monaco."""
    editor_path = vc.CORE_DIR / "md-editor-pm.html"
    if not editor_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo md-editor-pm.html não encontrado.")
    return editor_path.read_text(encoding="utf-8")

@app.get("/api/file/read")
async def read_file(file: str):
    """Lê o conteúdo de um template (colocar na url a pasta _tmpl)."""
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
    # Monta o comando isolado para o uv run com o caminho correto do ROOT_DIR
    cmd = f"uv run --directory \"{vc.ROOT_DIR}/sfia_safic\" main.py template --file \"{req.filename}\""
    
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


# ---------------------------------------------------------------------------
# API: BOTÃO DESLIGAR SERVIDOR
# ---------------------------------------------------------------------------

@app.post("/api/shutdown")
def shutdown_server():
    """Encerra o servidor web graciosamente."""
    vc.log("Sinal de desligamento recebido via Web. Encerrando o Launchpad...", level="WARNING")
    
    # Envia o sinal de interrupção para o próprio processo do Python (equivalente ao Ctrl+C)
    # Isso faz o Uvicorn iniciar seu processo de encerramento limpo.
    if os.name == 'nt':
        os.kill(os.getpid(), signal.CTRL_C_EVENT)
    else:
        os.kill(os.getpid(), signal.SIGINT)
        
    return {"status": "ok", "message": "Servidor sendo desligado..."}

import subprocess
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# --- API: GESTÃO DE FERRAMENTAS ---
# ---------------------------------------------------------------------------

class ToolRunRequest(BaseModel):
    args: str = ""

@app.get("/api/tools/list")
async def list_tools():
    """Varre a pasta core/Scripts em busca de :: DESC: e :: ARGS:"""
    scripts_dir = vc.CORE_DIR / "Scripts"
    tools = []
    if not scripts_dir.exists():
        return tools
        
    for f in scripts_dir.glob("*.bat"):
        if f.name.lower() == "vc_env.bat": continue
        
        desc = ""
        args_hint = ""
        
        try:
            with open(f, "r", encoding="utf-8", errors="ignore") as file:
                for _ in range(15):  # Lendo as primeiras linhas
                    line = file.readline()
                    if not line: break
                    if line.startswith(":: DESC:"):
                        desc = line.replace(":: DESC:", "").strip()
                    elif line.startswith(":: ARGS:"):
                        args_hint = line.replace(":: ARGS:", "").strip()
        except Exception:
            pass
            
        if desc:
            tools.append({
                "name": f.stem, 
                "desc": desc, 
                "args_hint": args_hint
            })
            
    return sorted(tools, key=lambda x: x['name'])

@app.post("/api/tools/run/{tool_name}")
async def run_tool(tool_name: str, payload: ToolRunRequest):
    """Abre uma ferramenta, repassando os argumentos digitados."""
    
    # Adiciona espaço antes dos argumentos, se eles existirem
    args_str = f" {payload.args.strip()}" if payload.args.strip() else ""
    
    # Mensagem mais curta que serve como "título" para o cronômetro do Windows
    msg = "✅ Execucao concluida! Pressione qualquer tecla, feche a janela ou aguarde o tempo abaixo:"
    
    # Removemos o >nul no final para que o contador regressivo volte a ser exibido
    cmd = f'start "{tool_name.upper()} - VC" cmd /c "call vc_env.bat && call {tool_name}.bat{args_str} && echo. && echo {msg} && timeout /t 30"'
    
    try:
        subprocess.Popen(cmd, shell=True, cwd=str(vc.CORE_DIR / "Scripts"))
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------------------------------

def start_server(port: int, work_dir_path: str):
    import uvicorn
    setup_work_dir(work_dir_path)
    
    # Substitui os prints antigos pelo log centralizado e puxa a versão da raiz
    vc.log(f"VC Server v{vc.get_vc_version()} iniciado em http://127.0.0.1:{port}", level="INFO")
    vc.log(f"WorkDir Web: {work_dir}", level="INFO")
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")

if __name__ == "__main__":
    # Exemplo de uso manual para teste
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5678)
    parser.add_argument("--dir", type=str, required=True)
    args = parser.parse_args()
    
    start_server(args.port, args.dir)