import uvicorn
import tomllib
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="VC - sfiaweb")

def ler_config_auditoria():
    """Lê o diretório alvo a partir do TOML em var/"""
    caminho_toml = Path(__file__).parent.parent / "var" / "config_auditoria.toml"
    
    if not caminho_toml.exists():
        raise FileNotFoundError(f"Arquivo de configuração não encontrado: {caminho_toml}")
        
    with open(caminho_toml, "rb") as f:
        return tomllib.load(f)

def get_pasta_alvo() -> Path:
    """Retorna o objeto Path da pasta da auditoria"""
    config = ler_config_auditoria()
    pasta_str = config.get("workspace", {}).get("dir")
    if not pasta_str:
        raise ValueError("O campo [workspace] dir não foi encontrado no TOML.")
    
    pasta_alvo = Path(pasta_str)
    if not pasta_alvo.exists() or not pasta_alvo.is_dir():
        raise FileNotFoundError(f"A pasta alvo não existe: {pasta_alvo}")
        
    return pasta_alvo


# --- ROTAS DA API ---

@app.get("/", response_class=HTMLResponse)
def ler_index():
    """Entrega a interface frontend (index.html)"""
    caminho_index = Path(__file__).parent / "index.html"
    return caminho_index.read_text(encoding="utf-8")


@app.get("/api/relatorios")
def listar_relatorios():
    """Devolve a lista de arquivos .md disponíveis na auditoria atual"""
    try:
        pasta_alvo = get_pasta_alvo()
        arquivos_md = []
        
        # Pega todos os arquivos .md e ordena pelo nome
        for arquivo in sorted(pasta_alvo.glob("*.md")):
            arquivos_md.append({
                "nome": arquivo.name
            })
            
        return {"status": "ok", "relatorios": arquivos_md}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relatorios/{nome_arquivo}")
def ler_relatorio(nome_arquivo: str):
    """Devolve o conteúdo de um arquivo .md específico"""
    try:
        pasta_alvo = get_pasta_alvo()
        caminho_arquivo = pasta_alvo / nome_arquivo
        
        # Prevenção básica de segurança (evitar que usem ../../ para ler arquivos do sistema)
        if not caminho_arquivo.resolve().is_relative_to(pasta_alvo.resolve()):
            raise HTTPException(status_code=403, detail="Acesso negado fora do workspace.")
            
        if not caminho_arquivo.exists() or caminho_arquivo.suffix != '.md':
            raise HTTPException(status_code=404, detail="Relatório não encontrado.")
            
        # Lê o arquivo usando UTF-8, o padrão do VC
        conteudo = caminho_arquivo.read_text(encoding="utf-8")
        
        return {"status": "ok", "nome": nome_arquivo, "conteudo": conteudo}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- INICIALIZAÇÃO ---

def start_server(port: int):
    print(f"🚀 Iniciando VC sfiaweb na porta {port}...")
    # O reload=True é ótimo para desenvolver, se você alterar o server.py ele reinicia sozinho
    uvicorn.run("server:app", host="127.0.0.1", port=port, reload=True)