"""
Funções auxiliares compartilhadas entre os módulos de reports.
Refatorado para utilizar as bibliotecas centrais do VC.
"""
from pathlib import Path

# IMPORTANTE: Importando as bibliotecas centrais (Namespaces isolados)
import core.lib.vccore as vc
import core.lib.to_markdown as vctm

# --- VARIÁVEL DE ESTADO GLOBAL DO MÓDULO ---
_DEBUG_ATIVO = False

def set_debug(ativo: bool):
    """Define o estado global de debug para a geração dos relatórios."""
    global _DEBUG_ATIVO
    _DEBUG_ATIVO = ativo

def executar_e_formatar(query, cursor, out_path, title):
    """Executa a query e faz o append do resultado formatado no arquivo MD."""
    try:
        cursor.execute(query)
        # Chama a exportação apontando para o namespace da biblioteca (vctm)
        vctm.export_markdown(
            cursor=cursor,
            out_path=out_path,
            sql_query=query,
            title=title,
            mode="a",
            show_meta=_DEBUG_ATIVO  # <--- Lê a variável global do módulo
        )
    except Exception as e:
        # Avisa no console padronizado e registra no corpo do relatório
        vc.log(f"Erro na consulta SQL ({title}): {e}", level="ERROR")
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"## {title}\n\n**Erro na consulta:** `{e}`\n\n")

def iniciar_relatorio(out_path, titulo, debug=False):
    """Cria o arquivo do relatório com o título e o link para o menu."""
    set_debug(debug) # Atualiza o estado automaticamente ao iniciar o relatório
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {titulo}\n\n")
        f.write("#### Link para o menu de relatórios: [Menu de relatórios](menu_relatorios.html)\n\n")