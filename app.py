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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Zion Rancho App", layout="wide")

# =================================================================
# BLOCO 1: ESTADOS E VARIÁVEIS
# =================================================================
COLUNAS_PADRAO = ["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"]

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'df_lista' not in st.session_state: 
    st.session_state.df_lista = pd.DataFrame(columns=COLUNAS_PADRAO)

USUARIOS = {
    "ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"},
    "JATOBA": {"nome": "STEFANI", "senha": "2558"},
    "JACARANDA": {"nome": "GABRIEL", "senha": "6352"}
}

# =================================================================
# BLOCO 2: TELA INICIAL (COM LOGO ZION)
# =================================================================
if st.session_state.pagina == "home":
    st.markdown("<h1 style='text-align: center;'>Zion Rancho App</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Verifica se a imagem existe para evitar erro de execução
        if os.path.exists("image_729ad1.jpg"):
            st.image("image_729ad1.jpg", use_container_width=True)
        else:
            st.warning("Logotipo não encontrado. Continuando sem imagem...")
            
        if st.button("🚀 ACESSAR SISTEMA", use_container_width=True):
            st.session_state.pagina = "login"
            st.rerun()

# =================================================================
# BLOCO 3: LOGIN
# =================================================================
elif st.session_state.pagina == "login":
    st.markdown("<h2 style='text-align: center;'>Acesso ao Sistema</h2>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        navio_sel = st.selectbox("Selecione sua Embarcação", list(USUARIOS.keys()))
        senha_dig = st.text_input("Senha de Acesso", type="password")
        if st.button("ENTRAR"):
            dados = USUARIOS.get(navio_sel)
            if dados and senha_dig == dados["senha"]:
                st.session_state.cozinheiro = dados["nome"]
                st.session_state.navio = navio_sel
                st.session_state.pagina = "lista" # Vai direto para a lista
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")

# =================================================================
# BLOCO 4: TABELA (FUNDO CINZA + BLOQUEIO + DATA/HORA BRASIL)
# =================================================================
elif st.session_state.pagina == "lista":
    # Fundo cinza para conferência
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.title(f"Conferência: {st.session_state.navio}")

    # Carregar dados iniciais se estiver vazio
    if st.session_state.df_lista.empty:
        # Aqui você pode manter sua função de carregar do Notion
        st.session_state.df_lista = pd.DataFrame([
            {"ITEM": 1, "DESCRIÇÃO": "Carne Moída", "TIPO": "PROTEÍNAS", "UNID MED": "kg", "PREDEFINIDO": 12, "CONFIRMA": 0},
            {"ITEM": 2, "DESCRIÇÃO": "Alcatra", "TIPO": "PROTEÍNAS", "UNID MED": "kg", "PREDEFINIDO": 10, "CONFIRMA": 0}
        ])

    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)

    # TRAVA DE SEGURANÇA
    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()

    if excedeu:
        st.markdown("<p style='color: red; font-weight: bold; font-size: 22px; text-align: center;'>⚠️ O limite foi excedido você não pode continuar</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_pdf, col_btn_menu = st.columns([1,1])

    with col_btn_menu:
        if st.button("⬅️ VOLTAR"):
            st.session_state.pagina = "home"
            st.rerun()

    # Só mostra o botão de PDF se o valor estiver correto
    if not excedeu:
        with col_pdf:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                
                class PDF_Zion(FPDF):
                    def header(self):
                        self.set_font("Arial", "B", 15)
                        self.cell(0, 10, "ZION TECNOLOGIA", ln=True, align="C")
                        self.set_font("Arial", "B", 11)
                        self.cell(0, 8, preparar(f"Lista de Rancho: {st.session_state.navio}"), ln=True, align="C")
                    
                    def footer(self):
                        self.set_y(-15)
                        self.set_font("Arial", "I", 8)
                        # Data/Hora Brasil no rodapé
                        br_tz = pytz.timezone('America/Sao_Paulo')
                        data_hora = datetime.now(br_tz).strftime("%d/%m/%Y %H:%M:%S")
                        self.cell(0, 10, preparar(f"Gerado em: {data_hora} | Zion Tecnologia"), 0, 0, "C")

                pdf = PDF_Zion()
                pdf.add_page()
                # (Aqui entraria o loop para desenhar as linhas do PDF...)
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                if st.download_button("📄 GERAR E BAIXAR PDF", data=pdf_output, file_name=f"Rancho_{st.session_state.navio}.pdf", use_container_width=True):
                    st.session_state.df_lista['CONFIRMA'] = 0 # Limpa após baixar
                    st.rerun()
            except Exception as e:
                st.error(f"Erro no relatório: {e}")

# Rodapé padrão em todas as páginas
if st.session_state.pagina != "home":
    st.markdown("---")
    st.caption(f"Operador: {st.session_state.cozinheiro if 'cozinheiro' in st.session_state else '---'} | © Zion Tecnologia 2026")
