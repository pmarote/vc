# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///

import os
import sys
import json
import httpx
import hashlib
import zipfile
import argparse
from pathlib import Path

# Configurações - AJUSTE AQUI
API_URL = "https://www.pmarote.net/pmcloud/api.php" # Substitua pelo seu domínio real
API_TOKEN = "sua_chave_secreta_aqui_123" # Deve ser idêntica à do PHP

client = httpx.Client(headers={"X-VC-API-Token": API_TOKEN}, timeout=120.0)

def calcular_hash(caminho_arquivo):
    """Gera um hash MD5 rápido para identificar o arquivo unicamente."""
    hasher = hashlib.md5()
    with open(caminho_arquivo, 'rb') as f:
        # Lê em blocos para não engasgar com arquivos grandes (ex: PDFs ou Bancos locais pesados)
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def coletar_arquivos_locais(pasta_alvo):
    """Varre a pasta e calcula o hash de tudo."""
    caminho_base = Path(pasta_alvo)
    arquivos_info = []
    
    for filepath in caminho_base.rglob('*'):
        if filepath.is_file():
            caminho_relativo = str(filepath.relative_to(caminho_base)).replace('\\', '/')
            tamanho = filepath.stat().st_size
            hash_arq = calcular_hash(filepath)
            
            arquivos_info.append({
                "caminho_relativo": caminho_relativo,
                "hash": hash_arq,
                "tamanho": tamanho
            })
    return arquivos_info

def formatar_tamanho(tamanho_bytes):
    """Transforma bytes em MB, GB, etc., para ficar legível."""
    if tamanho_bytes is None: return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if tamanho_bytes < 1024.0:
            return f"{tamanho_bytes:.2f} {unit}"
        tamanho_bytes /= 1024.0
    return f"{tamanho_bytes:.2f} TB"

def comando_ls(pasta_alvo):
    print("Consultando a PMCloud...")
    
    # Se o argumento vier vazio (None), mandamos 'ALL' para o PHP
    alvo = pasta_alvo if pasta_alvo else 'ALL'
    
    resp = client.post(API_URL, json={"acao": "listar", "pasta_alvo": alvo})
    
    try:
        dados = resp.json()
    except Exception as e:
        print("Erro na resposta do servidor:", resp.text)
        return
        
    if dados.get("status") != "sucesso":
        print("Erro ao buscar dados na nuvem.")
        return
        
    if dados["tipo"] == "resumo":
        print("\n=== RESUMO DAS PASTAS NA NUVEM ===")
        if not dados["dados"]:
            print("Nenhum backup encontrado. A nuvem está vazia.")
        else:
            for p in dados["dados"]:
                print(f"📁 {p['pasta_alvo']}")
                print(f"   Backups: {p['total_backups']} | Última versão: {p['ultimo_backup']}")
        
        tam_total = dados.get("tamanho_total")
        print(f"\n💾 Tamanho real ocupado no cofre (desduplicado): {formatar_tamanho(tam_total)}")
        print("💡 Dica: Para ver o histórico de uma pasta, use: uv run pmcloud.py -ls NOME_DA_PASTA")
        
    elif dados["tipo"] == "historico":
        print(f"\n=== HISTÓRICO DA PASTA: {pasta_alvo} ===")
        historico = dados["dados"]
        if not historico:
            print("Nenhum backup encontrado para esta pasta.")
        else:
            for h in historico:
                print(f"🕒 Data: {h['data_criacao']} | 📄 Arquivos: {h['qtd_arquivos']}")
        print("\n💡 Dica: Para restaurar, use: uv run pmcloud.py -pull NOME_DA_PASTA --data 'YYYY-MM-DD HH:MM:SS'")

def comando_bk(pasta_alvo):
    print(f"[{pasta_alvo}] Iniciando análise local...")
    if not os.path.exists(pasta_alvo):
        print(f"Erro: A pasta '{pasta_alvo}' não existe localmente.")
        return

    arquivos_locais = coletar_arquivos_locais(pasta_alvo)
    
    # Etapa 1: Pergunta ao servidor o que falta
    print("Verificando desduplicação no servidor...")
    resp = client.post(API_URL, json={
        "acao": "verificar_arquivos",
        "arquivos": arquivos_locais
    })
    
    try:
        dados = resp.json()
    except Exception as e:
        print("Erro na resposta do servidor:", resp.text)
        return

    arquivos_faltantes = dados.get("arquivos_para_upload", [])
    
    zip_temp = "temp_upload.zip"
    
    # Etapa 2: Cria o ZIP SÓ com o que o servidor pediu
    if arquivos_faltantes:
        print(f"Preparando transporte de {len(arquivos_faltantes)} arquivos novos/modificados...")
        with zipfile.ZipFile(zip_temp, 'w', zipfile.ZIP_DEFLATED) as zf:
            for caminho_relativo in arquivos_faltantes:
                caminho_completo = Path(pasta_alvo) / caminho_relativo
                zf.write(caminho_completo, arcname=caminho_relativo)
    else:
        print("Todos os arquivos já estão na nuvem! Registrando nova fotografia...")
        # Cria um zip vazio só para manter o fluxo
        with zipfile.ZipFile(zip_temp, 'w') as zf: pass 

    # Etapa 3: Envia para o servidor finalizar
    print("Enviando dados para nuvem...")
    with open(zip_temp, "rb") as arquivo_zip:
        files = {"arquivo_zip": arquivo_zip}
        # Enviamos os metadados totais para o servidor criar os vínculos da fotografia
        data = {
            "acao": "upload_backup", 
            "pasta_alvo": pasta_alvo,
            "metadados": json.dumps(arquivos_locais)
        }
        resp_upload = client.post(API_URL, data=data, files=files)
        
    print("Resposta:", resp_upload.json().get("mensagem", "Concluído."))
    
    # Limpeza
    if os.path.exists(zip_temp):
        os.remove(zip_temp)

def comando_pull(pasta_alvo, data_alvo=None):
    print(f"[{pasta_alvo}] Solicitando fotografia da nuvem...")
    
    payload = {
        "acao": "solicitar_pull",
        "pasta_alvo": pasta_alvo
    }
    if data_alvo:
        payload["data_alvo"] = data_alvo
        print(f"Buscando versão do dia: {data_alvo}")

    resp = client.post(API_URL, json=payload)
    
    try:
        dados = resp.json()
    except:
        print("Erro do servidor:", resp.text)
        return

    if "erro" in dados:
        print("Atenção:", dados["erro"])
        return

    url_download = dados["download_url"]
    print(f"Fotografia montada ({dados['total_arquivos']} arquivos). Baixando...")
    
    # Baixa o ZIP usando Stream para economizar memória
    zip_temp = "temp_download.zip"
    with client.stream("GET", url_download) as r:
        r.raise_for_status()
        with open(zip_temp, "wb") as f:
            for chunk in r.iter_bytes(chunk_size=8192):
                f.write(chunk)
                
    print("Extraindo arquivos para a pasta local...")
    os.makedirs(pasta_alvo, exist_ok=True)
    with zipfile.ZipFile(zip_temp, 'r') as zf:
        zf.extractall(pasta_alvo)
        
    os.remove(zip_temp)
    print("Restauração concluída com sucesso!")

def comando_rm(pasta_alvo):
    print(f"⚠️  Atenção: Solicitando exclusão da pasta '{pasta_alvo}' na nuvem...")
    
    # Trava de segurança no terminal
    confirmacao = input(f"TEM CERTEZA que deseja apagar TODO o histórico de '{pasta_alvo}'? (s/N): ")
    if confirmacao.lower() != 's':
        print("Operação cancelada para sua segurança.")
        return

    resp = client.post(API_URL, json={"acao": "deletar", "pasta_alvo": pasta_alvo})
    
    try:
        dados = resp.json()
    except Exception as e:
        print("Erro na resposta do servidor:", resp.text)
        return
        
    if "erro" in dados:
        print("Erro:", dados["erro"])
    else:
        print(f"\n✅ {dados['mensagem']}")
        print(f"🧹 Arquivos órfãos removidos fisicamente: {dados['orfaos_removidos']}")
        print(f"💾 Espaço em disco liberado no servidor: {formatar_tamanho(dados['espaco_liberado'])}")


# Ponto de entrada do script via linha de comando
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PMCloud - Sincronizador de Arquivos")
    parser.add_argument('-bk', metavar='PASTA', help='Faz backup da pasta para a nuvem')
    parser.add_argument('-pull', metavar='PASTA', help='Traz a pasta da nuvem para o local')
    parser.add_argument('-ls', metavar='PASTA', nargs='?', const='ALL', help='Lista as pastas na nuvem ou o histórico de uma específica')
    parser.add_argument('-rm', metavar='PASTA', help='Exclui a pasta e todo o seu histórico da nuvem')
    parser.add_argument('--data', help='(Opcional para o -pull) Data no formato YYYY-MM-DD HH:MM:SS', default=None)
    
    args = parser.parse_args()
    
    if args.bk:
        comando_bk(args.bk)
    elif args.pull:
        comando_pull(args.pull, args.data)
    elif args.ls or args.ls == 'ALL':
        comando_ls(args.ls if args.ls != 'ALL' else None)
    elif args.rm:
        comando_rm(args.rm)
    else:
        parser.print_help()