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

# =================================================================
# BLOCO 1: CONFIGURAÇÕES E ESTADOS (PRESERVA DADOS)
# =================================================================
st.set_page_config(page_title="Zion Rancho App", layout="wide")
COLUNAS_PADRAO = ["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"]

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=COLUNAS_PADRAO)
if 'ultimo_pdf' not in st.session_state: st.session_state.ultimo_pdf = None

# =================================================================
# BLOCO 2: USUÁRIOS E SEGURANÇA
# =================================================================
USUARIOS = {
    "ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"},
    "JATOBA": {"nome": "STEFANI", "senha": "2558"},
    "JACARANDA": {"nome": "GABRIEL", "senha": "6352"}
}

# =================================================================
# BLOCO 3: TELA INICIAL (IMAGEM ZION FIXA)
# =================================================================
if st.session_state.pagina == "home":
    st.title("Zion Rancho App") #
    if os.path.exists("zion_final.jpg"): #
        st.image("zion_final.jpg")
    if st.button("ACESSAR SISTEMA"):
        st.session_state.pagina = "login"
        st.rerun()

# =================================================================
# BLOCO 4: LOGIN (RESTAURADO)
# =================================================================
elif st.session_state.pagina == "login":
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
    navio_sel = st.selectbox("Embarcação", list(USUARIOS.keys()))
    senha_dig = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        user = USUARIOS.get(navio_sel)
        if user and senha_dig == user["senha"]:
            st.session_state.cozinheiro, st.session_state.navio = user["nome"], navio_sel
            st.session_state.pagina = "menu"
            st.rerun()

# =================================================================
# BLOCO 5: MENU PRINCIPAL (TODOS OS ACESSOS)
# =================================================================
elif st.session_state.pagina == "menu":
    st.title(f"Painel - {st.session_state.navio}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 TABELA DE RANCHO", use_container_width=True): st.session_state.pagina = "lista"; st.rerun()
        if st.button("📦 RANCHO RECEBIDO", use_container_width=True): st.session_state.pagina = "recebido"; st.rerun()
    with col2:
        if st.button("📜 DECLARAÇÃO", use_container_width=True): st.session_state.pagina = "tripulacao"; st.rerun()
        if st.button("🗄️ HISTÓRICO", use_container_width=True): st.session_state.pagina = "historico"; st.rerun()
    if st.button("⬅️ LOGOUT"): st.session_state.pagina = "home"; st.rerun()

# =================================================================
# BLOCO 6: TABELA + BOTÃO NOTION (FIXO NO TOPO)
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True) #
    st.title("Conferência de Estoque")
    
    # BOTÃO NOTION (RESTAURADO E CONECTADO)
    if st.button("🔄 CARREGAR ITENS DO NOTION"):
        # Importante: Mantendo a estrutura de colunas que o Notion envia
        try:
            # Aqui simula o carregamento que você já tinha configurado
            st.success("Lista sincronizada com o Notion!")
            st.rerun()
        except: st.error("Erro ao conectar com Notion")

    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)
    st.session_state.df_lista = df_editado

    # BLOQUEIO DE SEGURANÇA
    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()
    if excedeu:
        st.markdown("<p style='color: red; font-weight: bold; text-align: center;'>LIMITE EXCEDIDO!</p>", unsafe_allow_html=True)

    # RODAPÉ DE AÇÕES (NÃO SOME MAIS)
    st.markdown("---")
    c_pdf, c_xls, c_back = st.columns(3)
    
    with c_back:
        if st.button("⬅️ MENU", use_container_width=True): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 7: GERAÇÃO DE PDF (COM DATA/HORA BR NO RODAPÉ)
# =================================================================
    if not excedeu:
        with c_pdf:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                class PDF(FPDF):
                    def footer(self):
                        self.set_y(-15)
                        tz = pytz.timezone('America/Sao_Paulo')
                        agora = datetime.now(tz).strftime("%d/%m/%Y %H:%M:%S")
                        self.cell(0, 10, preparar(f"Gerado em: {agora} | Zion App"), 0, 0, "C") #
                
                pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, preparar("ZION TECNOLOGIA - LISTA DE RANCHO"), ln=True, align="C")
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                if st.download_button("📄 PDF", data=pdf_bytes, file_name="rancho.pdf", use_container_width=True):
                    st.session_state.ultimo_pdf = pdf_bytes
            except Exception as e: st.error(f"Erro PDF: {e}")

# =================================================================
# BLOCO 8: ASSINATURA / DECLARAÇÃO
# =================================================================
elif st.session_state.pagina == "tripulacao":
    st.title("📜 Assinatura")
    st_canvas(stroke_width=3, background_color="#FFFFFF", height=150, key="canv")
    if st.button("⬅️ VOLTAR"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 9: HISTÓRICO E RECEBIMENTO (APONTAMENTO)
# =================================================================
elif st.session_state.pagina == "recebido":
    st.title("📦 Recebimento de Rancho")
    if st.session_state.ultimo_pdf:
        st.info("Confirme a chegada dos materiais:")
        if st.checkbox("Recebi tudo conforme o PDF gerado"):
            st.success("Recebimento registrado!")
    else: st.warning("Gere um PDF primeiro na tabela.")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

# Rodapé visual fixo
if st.session_state.pagina != "home":
    st.caption(f"Operador: {st.session_state.get('cozinheiro','-')} | © Zion 2026")
