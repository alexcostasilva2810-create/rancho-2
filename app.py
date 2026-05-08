import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import unicodedata
from fpdf import FPDF
import requests
import io
import os
from datetime import datetime
import pytz

# BLOCO 1: CONFIGS E ESTADOS
st.set_page_config(page_title="Zion Rancho App", layout="wide")
COLUNAS = ["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"]

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=COLUNAS)
if 'ultimo_pdf' not in st.session_state: st.session_state.ultimo_pdf = None

# BLOCO 2: USUÁRIOS
USUARIOS = {"ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"}, "JATOBA": {"nome": "STEFANI", "senha": "2558"}, "JACARANDA": {"nome": "GABRIEL", "senha": "6352"}}

# BLOCO 3: HOME
if st.session_state.pagina == "home":
    st.title("Zion Rancho App") #
    if os.path.exists("zion_final.jpg"): st.image("zion_final.jpg") #
    if st.button("ACESSAR SISTEMA"): st.session_state.pagina = "login"; st.rerun()

# BLOCO 4: LOGIN
elif st.session_state.pagina == "login":
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
    navio = st.selectbox("Embarcação", list(USUARIOS.keys()))
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if USUARIOS[navio]["senha"] == senha:
            st.session_state.cozinheiro, st.session_state.navio = USUARIOS[navio]["nome"], navio
            st.session_state.pagina = "menu"; st.rerun()

# BLOCO 5: MENU
elif st.session_state.pagina == "menu":
    st.title(f"Painel - {st.session_state.navio}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📋 TABELA DE RANCHO", use_container_width=True): st.session_state.pagina = "lista"; st.rerun()
        if st.button("📦 RANCHO RECEBIDO", use_container_width=True): st.session_state.pagina = "recebido"; st.rerun()
    with c2:
        if st.button("📜 DECLARAÇÃO", use_container_width=True): st.session_state.pagina = "tripulacao"; st.rerun()
        if st.button("🗄️ HISTÓRICO", use_container_width=True): st.session_state.pagina = "historico"; st.rerun()
    if st.button("⬅️ LOGOUT"): st.session_state.pagina = "home"; st.rerun()

# BLOCO 6: LISTA + NOTION (CONECTADO)
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True) #
    st.title("Conferência de Estoque")
    
    # O BOTÃO QUE PUXA A LISTA DO NOTION
    if st.button("🔄 CARREGAR ITENS DO NOTION"):
        try:
            # Coloque sua URL de integração aqui
            url = "https://raw.githubusercontent.com/alexcostasilva2810-create/Rancho-Zion/main/estoque.csv"
            response = requests.get(url)
            if response.status_code == 200:
                st.session_state.df_lista = pd.read_csv(io.StringIO(response.text))
                st.success("Lista sincronizada!") #
                st.rerun()
        except: st.error("Erro ao conectar com Notion")

    st.session_state.df_lista = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)
    
    excedeu = (st.session_state.df_lista["CONFIRMA"] > st.session_state.df_lista["PREDEFINIDO"]).any()
    if excedeu: st.error("LIMITE EXCEDIDO!")

    st.markdown("---")
    col1, col2, col3 = st.columns(3) #
    
    with col3:
        if st.button("⬅️ MENU", use_container_width=True): st.session_state.pagina = "menu"; st.rerun()

# BLOCO 7: PDF COM RODAPÉ DATA/HORA
    if not excedeu:
        with col1:
            try:
                def prep(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                class PDF(FPDF):
                    def footer(self):
                        self.set_y(-15)
                        tz = pytz.timezone('America/Sao_Paulo')
                        self.cell(0, 10, prep(f"Gerado: {datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')}"), 0, 0, 'C') #
                pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, prep(f"RANCHO: {st.session_state.navio}"), ln=True, align='C')
                # Loop dos itens...
                out = pdf.output(dest='S').encode('latin-1')
                if st.download_button("📄 PDF", data=out, file_name="lista.pdf", use_container_width=True):
                    st.session_state.ultimo_pdf = out
            except: st.error("Erro PDF")

# BLOCO 8: ASSINATURA
elif st.session_state.pagina == "tripulacao":
    st.title("📜 Assinatura")
    st_canvas(stroke_width=3, background_color="#FFFFFF", height=150, key="sign")
    if st.button("⬅️ VOLTAR"): st.session_state.pagina = "menu"; st.rerun()

# BLOCO 9: HISTÓRICO / RECEBIMENTO
elif st.session_state.pagina == "recebido" or st.session_state.pagina == "historico":
    st.title("📦 Controle de Documentos")
    if st.session_state.ultimo_pdf:
        st.download_button("📥 Baixar Último PDF Gerado", data=st.session_state.ultimo_pdf, file_name="historico.pdf")
        if st.session_state.pagina == "recebido":
            st.checkbox("Confirmo que recebi o rancho desta lista")
    else: st.warning("Nenhum registro encontrado.")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

# Rodapé Operador
if st.session_state.pagina != "home":
    st.caption(f"Operador: {st.session_state.get('cozinheiro','-')} | © Zion 2026")
