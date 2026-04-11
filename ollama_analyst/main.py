import argparse
import sys
from pathlib import Path
import ollama

def analisar_prompt(arquivo_prompt: Path, arquivo_saida: Path, modelo: str):
    """Lê o prompt, envia para o Ollama e salva a resposta."""
    
    if not arquivo_prompt.exists():
        print(f"❌ Erro: O arquivo de prompt '{arquivo_prompt}' não foi encontrado.")
        sys.exit(1)

    print(f"📄 Lendo prompt de: {arquivo_prompt.name}")
    conteudo_prompt = arquivo_prompt.read_text(encoding="utf-8")

    print(f"🤖 Enviando para o Ollama (Modelo: {modelo})... aguarde, isso pode levar um tempo.")
    
    try:
        # Usamos o ollama.generate pois é um tiro único (prompt -> resposta), sem histórico de chat
        resposta = ollama.generate(
            model=modelo,
            prompt=conteudo_prompt
        )
        
        conteudo_resposta = resposta['response']
        
        # Garante que a pasta de saída exista, caso tenha passado um caminho complexo
        arquivo_saida.parent.mkdir(parents=True, exist_ok=True)
        
        # Grava a resposta da IA
        arquivo_saida.write_text(conteudo_resposta, encoding="utf-8")
        
        print(f"✅ Análise concluída! Resposta salva em: {arquivo_saida}")

    except Exception as e:
        print(f"❌ Erro ao comunicar com o Ollama: {e}")
        print("💡 Dica: Certifique-se de que o aplicativo Ollama está rodando no background e o modelo foi baixado.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="VC - Analista de Relatórios via Ollama Local")
    
    # Argumentos da linha de comando
    parser.add_argument("--prompt", required=True, help="Caminho para o arquivo .md com o prompt")
    parser.add_argument("--out", required=True, help="Caminho para salvar a resposta em .md")
    parser.add_argument("--model", default="gemma4:latest", help="Nome do modelo no Ollama (padrão: gemma4:latest)")
    
    args = parser.parse_args()

    caminho_prompt = Path(args.prompt)
    caminho_saida = Path(args.out)

    analisar_prompt(caminho_prompt, caminho_saida, args.model)

if __name__ == "__main__":
    main()