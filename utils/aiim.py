import os
import sqlite3
import argparse
import requests
from bs4 import BeautifulSoup
from pathlib import Path

class ExtratorAIIM:
    def __init__(self, db_path="var/tit_aiims.sqlite", storage_path="var/www"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.base_url = "https://www.fazenda.sp.gov.br/epat/extratoprocesso/ExtratoDetalhe.aspx?num_aiim="
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aiim (
                    numero_aiim TEXT PRIMARY KEY, 
                    drt TEXT, 
                    autuado TEXT,
                    advogado TEXT, 
                    assunto TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS andamentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_aiim TEXT,
                    data_evento TEXT,
                    descricao TEXT,
                    FOREIGN KEY(numero_aiim) REFERENCES aiim(numero_aiim)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS decisoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero_aiim TEXT,
                    data_publicacao TEXT,
                    recurso TEXT,
                    pdf_path TEXT,
                    pdf_url TEXT,
                    FOREIGN KEY(numero_aiim) REFERENCES aiim(numero_aiim)
                )
            """)
            conn.commit()

    def baixar_pdf(self, url_pdf, numero_aiim, recurso):
        """Acessa a URL da decisão e baixa o arquivo PDF físico."""
        recurso_limpo = recurso.replace(" ", "_").replace("/", "-").lower()
        numero_limpo = numero_aiim.replace('.', '').replace('-', '')
        nome_arquivo = f"{numero_limpo}_{recurso_limpo}.pdf"
        
        pdf_path = self.storage_path / nome_arquivo
        
        print(f"  -> Baixando PDF para o recurso '{recurso}'...")
        try:
            # Em alguns sites governamentais (sp.gov.br), o certificado SSL pode falhar.
            # Se você receber erros de SSL, pode tentar usar: requests.get(url_pdf, timeout=60, verify=False)
            resp = requests.get(url_pdf, timeout=60)
            
            if resp.status_code == 200:
                with open(pdf_path, "wb") as f:
                    f.write(resp.content)
                print(f"  -> PDF salvo com sucesso: {nome_arquivo}")
                return str(pdf_path)
            else:
                print(f"  -> Erro HTTP {resp.status_code} ao tentar baixar o PDF.")
                
        except Exception as e:
            print(f"  -> Erro ao baixar PDF {url_pdf}: {e}")
        
        return ""

    def processar_aiim(self, numero):
        url = f"{self.base_url}{numero}"
        try:
            response = requests.get(url, timeout=30)
            if response.status_code != 200:
                print(f"[{numero}] Erro HTTP {response.status_code} ao acessar a página principal.")
                return False
                
            html_content = response.text
            
            html_path = self.storage_path / f"{numero}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            lbl_aiim = soup.find(id="ConteudoPagina_lblAIIM")
            if not lbl_aiim:
                print(f"[{numero}] Ignorado: Nenhum AIIM encontrado nesta página.")
                return False
                
            numero_aiim = lbl_aiim.text.strip()
            
            lbl_drt = soup.find(id="ConteudoPagina_lblDRT")
            drt = lbl_drt.text.strip() if lbl_drt else ""
            
            lbl_autuado = soup.find(id="ConteudoPagina_lblNomeAutuado")
            autuado = lbl_autuado.text.strip() if lbl_autuado else ""
            
            lbl_adv = soup.find(id="ConteudoPagina_lblNomeAdvogado")
            advogado = lbl_adv.text.strip() if lbl_adv else ""
            
            pnl_assunto = soup.find(id="ConteudoPagina_pnlAssunto")
            assunto = " | ".join(pnl_assunto.stripped_strings) if pnl_assunto else ""

            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO aiim (numero_aiim, drt, autuado, advogado, assunto)
                    VALUES (?, ?, ?, ?, ?)
                """, (numero_aiim, drt, autuado, advogado, assunto))

                pnl_eventos = soup.find(id="ConteudoPagina_pnlEventos")
                if pnl_eventos:
                    for tr in pnl_eventos.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) >= 2:
                            data_evento = tds[0].text.strip()
                            descricao = tds[1].text.strip()
                            
                            cursor.execute("SELECT 1 FROM andamentos WHERE numero_aiim = ? AND data_evento = ? AND descricao = ?", 
                                         (numero_aiim, data_evento, descricao))
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO andamentos (numero_aiim, data_evento, descricao)
                                    VALUES (?, ?, ?)
                                """, (numero_aiim, data_evento, descricao))

                pnl_arquivos = soup.find(id="ConteudoPagina_pnlArquivos")
                if pnl_arquivos:
                    for tr in pnl_arquivos.find_all('tr'):
                        tds = tr.find_all('td')
                        if len(tds) >= 3:
                            data_pub = tds[0].text.strip()
                            recurso = tds[1].text.strip()
                            
                            link_tag = tds[2].find('a')
                            pdf_url = link_tag['href'] if link_tag else ""
                            pdf_path = ""
                            
                            # Agora sim ele entra aqui e invoca o download real
                            if pdf_url:
                                pdf_path = self.baixar_pdf(pdf_url, numero_aiim, recurso)
                            
                            cursor.execute("SELECT 1 FROM decisoes WHERE numero_aiim = ? AND data_publicacao = ? AND recurso = ?", 
                                         (numero_aiim, data_pub, recurso))
                            if not cursor.fetchone():
                                cursor.execute("""
                                    INSERT INTO decisoes (numero_aiim, data_publicacao, recurso, pdf_path, pdf_url)
                                    VALUES (?, ?, ?, ?, ?)
                                """, (numero_aiim, data_pub, recurso, pdf_path, pdf_url))
                
                conn.commit()
                print(f"[{numero}] AIIM {numero_aiim} processado e banco atualizado.")
                return True

        except Exception as e:
            print(f"[{numero}] Erro durante o processamento: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Scraper de dados de AIIMs do portal da Fazenda e integração no SQLite."
    )
    parser.add_argument(
        "--inicial", 
        type=int, 
        required=True, 
        help="Número inicial da faixa de AIIMs a baixar"
    )
    parser.add_argument(
        "--final", 
        type=int, 
        required=True, 
        help="Número final da faixa de AIIMs a baixar"
    )
    parser.add_argument(
        "--pasta", 
        type=str, 
        default="var/www", 
        help="Pasta onde os arquivos HTML e PDFs serão salvos (padrão: var/www)"
    )
    
    args = parser.parse_args()
    
    extrator = ExtratorAIIM(db_path="var/tit_aiims.sqlite", storage_path=args.pasta)
    
    print(f"\nIniciando raspagem de AIIMs do número {args.inicial} até {args.final}...\n")
    
    for numero in range(args.inicial, args.final + 1):
        extrator.processar_aiim(numero)

if __name__ == "__main__":
    main()