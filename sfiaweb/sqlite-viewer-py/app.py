import streamlit as st
import sqlite3
import pandas as pd
import tempfile
import os

# Configuração da página
st.set_page_config(page_title="SQLite Viewer", page_icon="🗄️", layout="wide")

st.title("🗄️ SQLite Viewer")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📂 Banco de Dados")
    uploaded_file = st.file_uploader("Abra um banco de dados SQLite", type=["db", "sqlite", "sqlite3"])

# --- ÁREA PRINCIPAL ---
if uploaded_file is not None:
    # O Streamlit recebe o arquivo na memória. O sqlite3 precisa de um caminho físico no disco.
    # Criamos um arquivo temporário para o sqlite3 conseguir ler.
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp.write(uploaded_file.getvalue())
        db_path = tmp.name

    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        
        # Busca a lista de tabelas do banco
        query_tables = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        df_tables = pd.read_sql_query(query_tables, conn)
        tabelas = df_tables['name'].tolist()
        
        # Mostra as tabelas na barra lateral
        with st.sidebar:
            st.subheader("📋 Tabelas")
            if not tabelas:
                st.info("Nenhuma tabela encontrada.")
            else:
                for tab in tabelas:
                    st.markdown(f"- `{tab}`")

        # Seção de Query
        st.subheader("💻 SQL Query")
        
        # Sugere uma query básica com a primeira tabela se ela existir
        default_query = f"SELECT * FROM {tabelas[0]} LIMIT 100;" if tabelas else "-- Escreva sua query aqui"
        
        query = st.text_area("Digite sua consulta SQL:", value=default_query, height=150)
        
        # Botão de Executar
        if st.button("▶️ Executar", type="primary"):
            try:
                # O pandas executa a query e já transforma num DataFrame bonitão
                df_resultados = pd.read_sql_query(query, conn)
                
                st.subheader("📊 Resultados")
                st.caption(f"Linhas retornadas: {len(df_resultados)}")
                
                # Exibe a tabela interativa
                st.dataframe(df_resultados, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"Erro na consulta SQL: {e}")

    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        
    finally:
        # Fecha a conexão e limpa o arquivo temporário
        if 'conn' in locals():
            conn.close()
        if os.path.exists(db_path):
            os.remove(db_path)

else:
    # Mensagem inicial quando não há arquivo carregado
    st.info("👈 Por favor, carregue um arquivo de banco de dados (.db, .sqlite) na barra lateral para começar.")