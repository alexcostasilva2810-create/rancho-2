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

# --- CONFIGURAÇÃO PWA ---
st.markdown("""
    <head>
        <link rel="manifest" href="https://raw.githubusercontent.com/alexcostasilva2810-create/Rancho-Zion/main/manifest.json?v=100">
        <meta name="mobile-web-app-capable" content="yes">
    </head>
    """, unsafe_allow_html=True)

# =================================================================
# BLOCO 1: ESTADOS E VARIÁVEIS (MANTIDO)
# =================================================================
COLUNAS_PADRAO = ["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"]

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=COLUNAS_PADRAO)

USUARIOS = {
    "ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"},
    "JATOBA": {"nome": "STEFANI", "senha": "2558"},
    "JACARANDA": {"nome": "GABRIEL", "senha": "6352"}
}

# =================================================================
# BLOCO 2: TELA INICIAL (RESTAURADA COM SUA IMAGEM)
# =================================================================
if st.session_state.pagina == "home":
    st.title("Zion Rancho App") # Título original
    
    # Exibe a imagem que está na sua pasta
    if os.path.exists("zion_final.jpg"):
        st.image("zion_final.jpg", width=300) # Tamanho padrão para não quebrar o layout
    
    if st.button("ACESSAR SISTEMA"):
        st.session_state.pagina = "login"
        st.rerun()

# =================================================================
# BLOCO 3: LOGIN (MANTIDO ORIGINAL)
# =================================================================
elif st.session_state.pagina == "login":
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        navio_sel = st.selectbox("Selecione sua Embarcação", list(USUARIOS.keys()))
        senha_dig = st.text_input("Senha de Acesso", type="password")
        if st.button("ENTRAR"):
            dados = USUARIOS.get(navio_sel)
            if dados and senha_dig == dados["senha"]:
                st.session_state.cozinheiro = dados["nome"]
                st.session_state.navio = navio_sel
                st.session_state.pagina = "menu"
                st.rerun()
            else: st.error("❌ Senha incorreta!")

# =================================================================
# BLOCO 4: TABELA DE CONFERÊNCIA (LAYOUT ORIGINAL + DATA NO PDF)
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.title("Conferência de Estoque")
    
    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)

    # Regra de bloqueio solicitada anteriormente
    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()
    if excedeu:
        st.markdown("<p style='color: red; font-weight: bold; font-size: 20px; text-align: center;'>O limite foi excedido você não pode continuar</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_pdf, col_excel, col_btn_menu = st.columns([1,1,1]) # Layout original de botões

    with col_btn_menu:
        if st.button("⬅️ MENU", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()

    if not excedeu:
        with col_pdf:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                
                class PDF_Checklist(FPDF):
                    def header(self):
                        self.set_text_color(0, 0, 128)
                        self.set_font("Arial", "B", 18)
                        self.cell(0, 10, "ZION TECNOLOGIA", ln=True, align="C")
                        self.set_text_color(0, 0, 0)
                        self.set_font("Arial", "B", 12)
                        self.cell(0, 8, preparar(f"Lista de Rancho: {st.session_state.navio}"), ln=True, align="C")

                    # RODAPÉ COM DATA/HORA BRASIL
                    def footer(self):
                        self.set_y(-15)
                        self.set_font("Arial", "I", 8)
                        fuso_br = pytz.timezone('America/Sao_Paulo')
                        agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                        self.cell(0, 10, preparar(f"Gerado em: {agora_br} | Página {self.page_no()}"), 0, 0, "C")

                pdf = PDF_Checklist()
                pdf.add_page()
                # ... (Lógica de preenchimento da tabela igual à original)
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button("📄 PDF", data=pdf_bytes, file_name=f"Rancho_{st.session_state.navio}.pdf", use_container_width=True)
            except Exception as e: st.error(f"Erro PDF: {e}")

# =================================================================
# RESTANTE DO CÓDIGO (MENU, TRIPULACAO, ETC) PERMANECE IGUAL
# =================================================================
