"""
sfia_safic/template_engine.py
Motor de compilação do Literate Document (*.tmpl.md)
"""
import re
import sqlite3
import yaml
from pathlib import Path

# Reutilizando a infraestrutura oficial do VC
from to_markdown import fmt_br
from reports._helpers import executar_e_formatar, set_debug

class TemplateCompiler:
    def __init__(self, tmpl_path: Path, work_dir: Path, debug: bool = False):
        self.tmpl_path = Path(tmpl_path)
        self.work_dir = Path(work_dir)
        self.dbs_dir = self.work_dir / "_dbs"
        self.mds_dir = self.work_dir / "_mds"
        self.debug = debug
        
        self.context = {}
        self.conn = None
        self.cursor = None

    def compile(self) -> Path | None:
        """Lê o template, compila as dinâmicas e gera o artefato .md final."""
        content = self.tmpl_path.read_text(encoding="utf-8")

        # 1. Isolar Frontmatter YAML
        fm_match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if not fm_match:
            print(f"  [Ignorado] {self.tmpl_path.name}: Sem frontmatter (---) válido.")
            return None

        yaml_content, body = fm_match.groups()
        
        try:
            self.context = yaml.safe_load(yaml_content) or {}
        except yaml.YAMLError as e:
            print(f"  [Erro] Falha ao ler YAML em {self.tmpl_path.name}: {e}")
            return None

        if self.context.get("type") != "sfia-template":
            print(f"  [Ignorado] {self.tmpl_path.name}: type não é 'sfia-template'.")
            return None

        # Preparar caminhos de saída
        self.mds_dir.mkdir(parents=True, exist_ok=True)
        out_name = self.tmpl_path.name.replace(".tmpl.md", ".md")
        out_path = self.mds_dir / out_name

        # 2. Iniciar conexão e ambiente de dados
        try:
            self._setup_db()
            
            # Sincroniza o modo debug com o módulo de helpers
            set_debug(self.debug)
            
            # 3. Interpolar Variáveis Documentais: {{ var }}
            body = re.sub(r"\{\{\s*([\w\.]+)\s*\}\}", self._repl_var, body)

            # 4. Executar Mutações: ```sfia ... ```
            body = re.sub(r"```sfia\n(.*?)\n```", self._repl_sfia_block, body, flags=re.DOTALL)

            # 5. Executar SQL Inline: `sfia-sql ... `
            body = re.sub(r"`sfia-sql\s+(.+?)`", self._repl_inline_sql, body)

            # 6. Gravação Sequencial (O "Pulo do Gato" para usar o _helpers.py)
            
            # Limpa o arquivo de saída (inicia em branco)
            out_path.write_text("", encoding="utf-8")
            
            # Fatiar o body preservando os blocos SQL usando regex com grupos de captura
            pattern = re.compile(r"(```sfia-sql\n.*?\n```)", re.DOTALL)
            parts = pattern.split(body)
            
            for part in parts:
                if part.startswith("```sfia-sql"):
                    # Extrai a query removendo a tag inicial e final
                    query = part[12:-3].strip()
                    
                    # Chama o helper oficial. 
                    # Passamos title="" pois o template assume que o auditor já escreveu
                    # os títulos (ex: ## Meus Dados) no próprio texto Markdown.
                    executar_e_formatar(query, self.cursor, str(out_path), title="")
                else:
                    # Se for texto em prosa, faz o append físico no arquivo
                    if part:
                        with open(out_path, "a", encoding="utf-8") as f:
                            f.write(part)
            
        except Exception as e:
            print(f"  [Erro Fatal] Falha ao compilar {self.tmpl_path.name}: {e}")
            return None
        finally:
            if self.conn:
                self.conn.close()

        return out_path

    # ==========================================
    # HELPERS DE SUBSTITUIÇÃO EM MEMÓRIA
    # ==========================================
    def _setup_db(self):
        main_db = self.context.get("main_db")
        if not main_db:
            raise ValueError("Chave obrigatória 'main_db' ausente no frontmatter.")

        db_path = self.dbs_dir / main_db
        if not db_path.exists():
            db_path = self.work_dir / main_db

        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        for attach in self.context.get("attach_dbs", []):
            att_path = self.dbs_dir / attach
            if not att_path.exists():
                att_path = self.work_dir / attach
                
            alias = att_path.stem
            self.cursor.execute(f"ATTACH DATABASE '{att_path.as_posix()}' AS {alias}")

    def _repl_var(self, match):
        var_name = match.group(1)
        return str(self.context.get(var_name, f"{{{{ {var_name} }}}}"))

    def _repl_sfia_block(self, match):
        content = match.group(1)
        try:
            cmds = yaml.safe_load(content) or {}
            if "sql.exec" in cmds:
                self.cursor.execute(cmds["sql.exec"])
            
            for k, v in cmds.items():
                if not k.startswith("sql.") and not k.startswith("py."):
                    self.context[k] = v
            return ""
        except Exception as e:
            return f"\n> [!error] Falha no Mutador SFIA\n> `{e}`\n"

    def _repl_inline_sql(self, match):
        sql = match.group(1).strip()
        try:
            self.cursor.execute(sql)
            row = self.cursor.fetchone()
            val = row[0] if row else ""
            return str(fmt_br(val))
        except Exception as e:
            return f"`[ERRO SQL: {e}]`"

# --- Interface Pública do Módulo ---
def compilar_todos_templates(work_dir: Path, debug: bool = False):
    """Busca e compila Literate Documents (*.tmpl.md) na raiz do workspace."""
    work_dir = Path(work_dir)
    # se um dia quiser buscar também nas subpastas, não somente na raiz, troque o glob abaixo por rglob
    templates = list(work_dir.glob("*.tmpl.md"))
    
    if not templates:
        print("  Nenhum template *.tmpl.md encontrado na pasta de trabalho.")
        return

    for tmpl in templates:
        print(f" ➔ Compilando artefato: {tmpl.name} ...")
        compiler = TemplateCompiler(tmpl, work_dir, debug=debug)
        out_file = compiler.compile()
        if out_file:
            print(f"    ✅ Materializado em: {out_file.relative_to(work_dir)}")