import os
import signal
import uvicorn
import tomllib
import mimetypes
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

app = FastAPI(title="VC - Explorer")

# Resolve o caminho da raiz (vc/)
ROOT_DIR = Path(__file__).resolve().parent.parent

def get_work_dir() -> Path:
    """Retorna o objeto Path da pasta raiz da auditoria."""
    caminho_toml = ROOT_DIR / "var" / "sfia_config.toml"
    
    if not caminho_toml.exists():
        raise HTTPException(status_code=500, detail="Configuração não encontrada.")
        
    with open(caminho_toml, "rb") as f:
        config = tomllib.load(f)
        work_dir = config.get("work_dir")
        if not work_dir:
            raise HTTPException(status_code=500, detail="work_dir não definido no TOML.")
        
        pasta = Path(work_dir)
        if not pasta.exists():
            raise HTTPException(status_code=404, detail="Pasta de trabalho não encontrada.")
            
        return pasta.resolve()

def formatar_tamanho(size_bytes: int) -> str:
    """Formata bytes para um texto legível."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@app.get("/", response_class=HTMLResponse)
def ler_index():
    """Entrega a interface do File Explorer."""
    index_path = Path(__file__).parent / "index.html"
    return index_path.read_text(encoding="utf-8")

@app.get("/md_viewer", response_class=HTMLResponse)
def ler_md_viewer():
    """Entrega o renderizador de Markdown customizado pelo usuário."""
    viewer_path = Path(__file__).parent / "markdown-it.html"
    if not viewer_path.exists():
        raise HTTPException(status_code=404, detail="Arquivo markdown-it.html não encontrado na pasta sfiaweb.")
    return viewer_path.read_text(encoding="utf-8")

@app.get("/api/ls/{subpath:path}")
def listar_arquivos(subpath: str = ""):
    """Lista diretórios e arquivos de um subpath, com bloqueio de segurança."""
    try:
        base_dir = get_work_dir()
        target_dir = (base_dir / subpath).resolve()
        
        # Segurança contra directory traversal (ex: subir além do work_dir com ../)
        if not target_dir.is_relative_to(base_dir):
            raise HTTPException(status_code=403, detail="Acesso negado para fora do Work Dir.")
            
        if not target_dir.exists() or not target_dir.is_dir():
            raise HTTPException(status_code=404, detail="Pasta não encontrada.")

        itens = []
        for p in target_dir.iterdir():
            stat = p.stat()
            itens.append({
                "name": p.name,
                "is_dir": p.is_dir(),
                "size": formatar_tamanho(stat.st_size) if p.is_file() else "",
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M")
            })
        
        # Ordena: Pastas primeiro, depois por nome alfabético
        itens.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        
        return {"status": "ok", "path": subpath, "items": itens}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/raw/{subpath:path}")
def ler_arquivo_raw(subpath: str):
    """Serve arquivos físicos para download ou visualização (HTML)."""
    try:
        base_dir = get_work_dir()
        target_file = (base_dir / subpath).resolve()
        
        if not target_file.is_relative_to(base_dir):
            raise HTTPException(status_code=403, detail="Acesso negado.")
        if not target_file.exists() or not target_file.is_file():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado.")
            
        media_type, _ = mimetypes.guess_type(target_file)
        return FileResponse(target_file, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/shutdown")
def shutdown_server():
    """Desliga o servidor Uvicorn enviando um sinal de interrupção."""
    # O sinal SIGINT simula um "Ctrl+C" no terminal de forma amigável
    os.kill(os.getpid(), signal.SIGINT)
    return {"status": "ok", "message": "Desligando servidor..."}

def start_server(port: int):
    print(f"🚀 Iniciando VC sfiaweb na porta {port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)