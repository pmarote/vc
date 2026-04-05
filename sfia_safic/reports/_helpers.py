"""
Funções auxiliares compartilhadas entre os módulos de reports.
"""
import sys
from pathlib import Path

# Garante que to_markdown seja encontrado (está um nível acima)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from to_markdown import export_markdown


def executar_e_formatar(query, cursor, out_path, title):
    """Executa a query e faz o append do resultado formatado no arquivo MD."""
    try:
        cursor.execute(query)
        export_markdown(
            cursor=cursor,
            out_path=out_path,
            sql_query=query,
            title=title,
            mode="a"
        )
    except Exception as e:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"## {title}\n\n**Erro na consulta:** `{e}`\n\n")


def iniciar_relatorio(out_path, titulo):
    """Cria o arquivo do relatório com o título e o link para o menu."""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n\n")
        f.write("#### Link para o menu de relatórios: [Menu de relatórios](menu_relatorios.html)\n\n")
