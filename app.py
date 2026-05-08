import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import unicodedata
from fpdf import FPDF
import requests
import io
from datetime import datetime
import pytz

# =================================================================
# BLOCO 0: CONFIGURAÇÕES DE PÁGINA E ESTILOS
# =================================================================
st.set_page_config(page_title="Zion Rancho App", layout="wide")

# CSS para centralizar imagem e botões na Home
st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .main-logo { display: block; margin-left: auto; margin-right: auto; width: 60%; border-radius: 20px; }
    .stButton > button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# BLOCO 1: ESTADOS E VARIÁVEIS
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
# BLOCO 2: TELA INICIAL (COM IMAGEM ZION)
# =================================================================
if st.session_state.pagina == "home":
    # Centraliza a imagem do logo Zion
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("image_729ad1.jpg", use_container_width=True)
        st.markdown("<h2 style='text-align: center; color: #333;'>Sistema de Rancho</h2>", unsafe_allow_html=True)
        
        # Botão que aparece automaticamente
        if st.button("🚀 ACESSAR SISTEMA"):
            st.session_state.pagina = "login"
            st.rerun()

# =================================================================
# BLOCO 3: LOGIN
# =================================================================
elif st.session_state.pagina == "login":
    st.markdown("<h1 style='text-align: center;'>Identificação</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        navio_sel = st.selectbox("Selecione sua Embarcação", list(USUARIOS.keys()))
        senha_dig = st.text_input("Senha", type="password")
        if st.button("ENTRAR"):
            user_data = USUARIOS.get(navio_sel)
            if user_data and senha_dig == user_data["senha"]:
                st.session_state.cozinheiro = user_data["nome"]
                st.session_state.navio = navio_sel
                st.session_state.pagina = "menu"
                st.rerun()
            else:
                st.error("Senha inválida")

# =================================================================
# BLOCO 4: TABELA (FUNDO CINZA + BLOQUEIO + RODAPÉ BRASIL)
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.title(f"Conferência - {st.session_state.navio}")
    
    # Simulação de carregamento de dados
    if st.session_state.df_lista.empty:
        st.session_state.df_lista = pd.DataFrame([
            {"ITEM": 1, "DESCRIÇÃO": "Carne Moída", "TIPO": "PROTEÍNAS", "UNID MED": "kg", "PREDEFINIDO": 12, "CONFIRMA": 0},
            {"ITEM": 2, "DESCRIÇÃO": "Alcatra", "TIPO": "PROTEÍNAS", "UNID MED": "kg", "PREDEFINIDO": 10, "CONFIRMA": 0},
        ])

    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)

    # Regra de Bloqueio: CONFIRMA não pode ser > PREDEFINIDO
    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()
    
    if excedeu:
        st.markdown("<p style='color: red; font-weight: bold; font-size: 20px; text-align: center;'>O limite foi excedido você não pode continuar</p>", unsafe_allow_html=True)
    
    col_pdf, col_menu = st.columns([1, 1])
    
    with col_menu:
        if st.button("⬅️ MENU"):
            st.session_state.pagina = "menu"
            st.rerun()

    if not excedeu:
        with col_pdf:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                
                class PDF_Zion(FPDF):
                    def header(self):
                        self.set_font("Arial", "B", 16)
                        self.cell(0, 10, "ZION TECNOLOGIA", ln=True, align="C") #
                        self.set_font("Arial", "", 10)
                        self.cell(0, 10, preparar(f"Embarcação: {st.session_state.navio}"), ln=True, align="C")
                    
                    def footer(self):
                        self.set_y(-15)
                        self.set_font("Arial", "I", 8)
                        # Data e Hora Brasil no Rodapé
                        tz_br = pytz.timezone('America/Sao_Paulo')
                        agora = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
                        self.cell(0, 10, preparar(f"Gerado em: {agora} - Zion App"), 0, 0, "C")

                pdf = PDF_Zion()
                pdf.add_page()
                pdf.set_font("Arial", "", 9)
                # (Lógica de preenchimento da tabela no PDF aqui...)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                if st.download_button("📄 GERAR PDF", data=pdf_output, file_name="rancho.pdf"):
                    # Zera a coluna após o download
                    st.session_state.df_lista["CONFIRMA"] = 0
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao gerar relatório: {e}")

# Adicione as outras páginas (menu, tripulacao) conforme necessário...
