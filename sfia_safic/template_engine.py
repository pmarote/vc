"""
sfia_safic/template_engine.py
Motor de compilação do Literate Document (*.tmpl.md) - SFIA_TMPL_SPEC v0.3
"""
import re
import sqlite3
import yaml
import sys
import io
import os
import tempfile
from pathlib import Path

# Reutilizando a infraestrutura oficial do VC
from to_markdown import fmt_br
from reports._helpers import executar_e_formatar, set_debug

class SfiaHelper:
    """Classe utilitária injetada no namespace como 'sfia'"""
    def __init__(self, dbs_dir: Path):
        self.dbs_dir = dbs_dir

    def get_history_query(self, title: str) -> str:
        """Busca a query mais recente do histórico pelo título."""
        # print(f"[DEBUG]get_history_query.title='{title}'")  # debug
        hist_db = self.dbs_dir / "query_history.sqlite"
        if not hist_db.exists():
            return f"/* [Erro]: [Banco de Dados de Histórico não encontrado: '{hist_db}'] */"
        
        try:
            with sqlite3.connect(hist_db) as conn:
                cur = conn.cursor()
                cur.execute(f"SELECT sql_query FROM history WHERE title LIKE ? ORDER BY timestamp DESC LIMIT 1", (f"%{title}%",))
                row = cur.fetchone()
                # print(f"[DEBUG]  get_history_query.row={row}")  # debug
                if row:
                    # rstrip limpa do final da string: ponto e vírgula, vírgula e espaços em branco (inclusive \n)
                    return str(row[0]).rstrip(';,\r\n\t ')
                
                return f"/* /* [Erro]: [Histórico não encontrado: title='{title}'] */ */"
        except Exception as e:
            return f"/* Erro SQLite ao acessar histórico: {e} */"


class TemplateCompiler:
    def __init__(self, tmpl_path: Path, work_dir: Path, debug: bool = False):
        self.tmpl_path = Path(tmpl_path)
        self.work_dir = Path(work_dir)
        self.dbs_dir = self.work_dir / "_dbs"
        self.mds_dir = self.work_dir / "_mds"
        self.debug = debug
        set_debug(debug)
        
        self.namespace = {}
        self.conn = None
        self.cursor = None

    def resolve_inlines(self, text: str) -> str:
        """
        Passada única de resolução de Inlines {{ }}.
        Sem recursividade e utilizando o estado *atual* do namespace.
        """
        def replacer(match):
            expr = match.group(1).strip()
            # print(f"[DEBUG]expr={expr}")  # debug
            try:
                if expr.startswith("py:"):
                    py_expr = expr[3:].strip()
                    # print(f"[DEBUG]py_expr={py_expr}")  # debug
                    # print(f"[DEBUG]self.namespace={self.namespace}")  # debug
                    res = eval(py_expr, self.namespace)
                    # print(f"[DEBUG]res={res}")  # debug
                    # Removido fmt_br: Retorna texto CRU para não quebrar sintaxe SQL interpolada
                    return str(res) if res is not None else ""
                
                elif expr.startswith("sql:"):
                    sql_expr = expr[4:].strip()
                    self.cursor.execute(sql_expr)
                    row = self.cursor.fetchone()
                    val = row[0] if row else ""
                    return str(val) if val is not None else ""
                
                else:
                    # Interpolação de variável padrão do Namespace
                    res = eval(expr, self.namespace)
                    return str(res) if res is not None else ""
            except Exception as e:
                return f"`[ERRO INLINE: {e}]`"
        
        # re.sub executa de uma vez, impedindo recursividade acidental de retornos maliciosos
        return re.sub(r'\{\{\s*(.*?)\s*\}\}', replacer, text)

    def compile(self) -> Path | None:
        """Lê o template, compila as dinâmicas top-to-bottom e gera o artefato .md."""
        content = self.tmpl_path.read_text(encoding="utf-8")

        # 1. Isolar Frontmatter YAML
        fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if not fm_match:
            print(f"  [Ignorado] {self.tmpl_path.name}: Sem frontmatter (---) válido.")
            return None
        
        fm_text, body = fm_match.groups()
        
        try:
            fm = yaml.safe_load(fm_text)
        except yaml.YAMLError as e:
            print(f"  [Erro YAML] {self.tmpl_path.name}: {e}")
            return None

        if fm.get("type") != "sfia-template":
            return None

        # 2. Conexões e Preparação
        main_db_name = fm.get("main_db")
        if not main_db_name:
            print(f"  [Erro] 'main_db' ausente no frontmatter de {self.tmpl_path.name}.")
            return None

        main_db_path = self.dbs_dir / main_db_name
        if not main_db_path.exists():
            print(f"  [Erro] Banco principal '{main_db_path.name}' não localizado.")
            return None

        self.conn = sqlite3.connect(main_db_path)
        self.cursor = self.conn.cursor()
        
        attach_dbs = fm.get("attach_dbs", {})
        if isinstance(attach_dbs, dict):
            for alias, db_filename in attach_dbs.items():
                attach_path = self.dbs_dir / db_filename
                if attach_path.exists():
                    self.cursor.execute(f"ATTACH DATABASE '{attach_path}' AS {alias}")
                else:
                    print(f"  [Aviso] Banco de attach '{db_filename}' não encontrado.")

        # Construindo Namespace
        self.namespace = {
            "sfia": SfiaHelper(self.dbs_dir)
        }
        for k, v in fm.items():
            self.namespace[k] = v  # Injeção nativa
            # print(f"[DEBUG]injetando item do YAMLfm '{v}' no campo '{k}' de self.namespace")  # debug


        # 3. Processamento em Fluxo (Parser Linear Top-to-Bottom)
        output_parts = []
        pos = 0
        
        # Regex para fences: captura a linguagem no group(1) e o código no group(2)
        fence_pattern = re.compile(r'```(sql|python)\s+sfia\s*\n(.*?)```', re.DOTALL)
        
        for match in fence_pattern.finditer(body):
            start, end = match.span()
            lang = match.group(1)
            code = match.group(2)
            
            # 3.1. Processa o TEXTO MARKDOWN antes do Fence
            text_before = body[pos:start]
            if text_before:
                output_parts.append(self.resolve_inlines(text_before))
            
            # 3.2. Resolve Inlines DENTRO do Fence (antes de rodá-lo)
            resolved_code = self.resolve_inlines(code)
            
            # 3.3. Executa o Fence
            if lang == "python":
                old_stdout = sys.stdout
                redirected_output = sys.stdout = io.StringIO()
                try:
                    # Executa mudando o estado do Namespace e captura os prints
                    exec(resolved_code, self.namespace)
                    console_out = redirected_output.getvalue()
                    if console_out.strip():
                        # Outputs do print() viram texto injetado no Markdown
                        output_parts.append(console_out.strip() + "\n")
                except Exception as e:
                    output_parts.append(f"> ❌ **Erro Python:** `{e}`\n\n```python\n{resolved_code}\n```\n")
                finally:
                    sys.stdout = old_stdout
                    
            elif lang == "sql":
                query = resolved_code.strip()
                # print(f"[DEBUG]Bloco sql com query = {query}")  # debug
                
                # Resolução do Gargalo de Gravação (In-Memory para File e de volta para In-Memory)
                # Criamos um arquivo temporário seguro (mkstemp não entra em conflito de lock no Windows)
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".md", text=True)
                os.close(tmp_fd) # Fecha o descritor para que o VC possa abrí-lo livremente
                
                try:
                    # Chama o helper oficial do VC, que gravará as tabelas no tmp_path
                    executar_e_formatar(query, self.cursor, tmp_path, title="")
                    
                    # Lê o resultado recém-formatado e devolve para a nossa pipeline de memória
                    with open(tmp_path, 'r', encoding='utf-8') as f:
                        md_table = f.read()
                        # print(f"[DEBUG]Sql Query executado: {md_table}")  # debug
                        
                    output_parts.append(md_table + "\n")
                except Exception as e:
                    output_parts.append(f"> ❌ **Erro SQL:** `{e}`\n\n```sql\n{query}\n```\n")
                finally:
                    # Garbage Collector implacável do arquivo temporário
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
            
            pos = end
            
        # 3.4. Processa o restante do documento após o último fence
        text_after = body[pos:]
        if text_after:
            output_parts.append(self.resolve_inlines(text_after))
            
        self.conn.close()

        # 4. Materialização do Artefato Final
        out_filename = self.tmpl_path.name.replace(".tmpl.md", ".md")
        out_path = self.mds_dir / out_filename
        
        final_content = f"---\n{fm_text}\n---\n" + "".join(output_parts)
        out_path.write_text(final_content, encoding="utf-8")
        
        print(f"  [OK] Artefato gerado: {self.mds_dir}\\{out_filename}")
        return out_path


# --- Interface Pública do Módulo ---
def compilar_todos_templates(work_dir: Path, debug: bool = False):
    """Busca e compila Literate Documents (*.tmpl.md) na raiz do workspace."""
    work_dir = Path(work_dir)
    templates = list(work_dir.glob("*.tmpl.md"))
    
    if not templates:
        print("  Nenhum template *.tmpl.md encontrado na pasta de trabalho.")
        return

    print(f"🚀 Compilando {len(templates)} templates dinâmicos (Spec v0.3)...")
    for tmpl in templates:
        compiler = TemplateCompiler(tmpl, work_dir, debug)
        print(f"[INFO] Compilando agora template {tmpl}")
        compiler.compile()