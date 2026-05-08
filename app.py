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

# --- BLOCO 1: CONFIGURAÇÕES ---
st.set_page_config(page_title="Zion Rancho App", layout="wide")
COLUNAS_PADRAO = ["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"]

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=COLUNAS_PADRAO)
if 'ultimo_pdf' not in st.session_state: st.session_state.ultimo_pdf = None

# --- BLOCO 2: USUÁRIOS ---
USUARIOS = {
    "ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"},
    "JATOBA": {"nome": "STEFANI", "senha": "2558"},
    "JACARANDA": {"nome": "GABRIEL", "senha": "6352"}
}

# --- BLOCO 3: TELA INICIAL ---
if st.session_state.pagina == "home":
    st.title("Zion Rancho App")
    if os.path.exists("zion_final.jpg"):
        st.image("zion_final.jpg")
    if st.button("ACESSAR SISTEMA"):
        st.session_state.pagina = "login"
        st.rerun()

# --- BLOCO 4: LOGIN ---
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

# --- BLOCO 5: MENU ---
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

# --- BLOCO 6: TABELA DE CONFERÊNCIA ---
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.title("Conferência de Estoque")
    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)
    
    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()
    if excedeu: st.markdown("<p style='color: red; font-weight: bold; font-size: 20px; text-align: center;'>O limite foi excedido você não pode continuar</p>", unsafe_allow_html=True)
    
    col_pdf, col_menu = st.columns([1,1])
    with col_menu:
        if st.button("⬅️ MENU", use_container_width=True): st.session_state.pagina = "menu"; st.rerun()
    
    if not excedeu:
        with col_pdf:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                class PDF_Rancho(FPDF):
                    def footer(self):
                        self.set_y(-15)
                        tz_br = pytz.timezone('America/Sao_Paulo')
                        agora = datetime.now(tz_br).strftime("%d/%m/%Y %H:%M:%S")
                        self.cell(0, 10, preparar(f"Gerado em: {agora}"), 0, 0, "C")
                
                pdf = PDF_Rancho(); pdf.add_page(); pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "LISTA DE RANCHO", ln=True, align="C")
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                if st.download_button("📄 GERAR PDF", data=pdf_bytes, file_name="rancho.pdf", use_container_width=True):
                    st.session_state.ultimo_pdf = pdf_bytes # Salva para o histórico e recebimento
                    st.session_state.df_lista['CONFIRMA'] = 0
                    st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

# --- BLOCO 7: DECLARAÇÃO / ASSINATURA ---
elif st.session_state.pagina == "tripulacao":
    st.title("📜 Assinatura da Declaração")
    st_canvas(stroke_width=3, background_color="#FFFFFF", height=150, key="canvas")
    if st.button("⬅️ VOLTAR"): st.session_state.pagina = "menu"; st.rerun()

# --- BLOCO 8: HISTÓRICO (APONTA O PDF GERADO) ---
elif st.session_state.pagina == "historico":
    st.title("🗄️ Histórico de Documentos")
    if st.session_state.ultimo_pdf:
        st.success(f"Último PDF gerado por: {st.session_state.cozinheiro}")
        st.download_button("📥 Baixar Cópia do Último PDF", data=st.session_state.ultimo_pdf, file_name="historico_rancho.pdf")
    else:
        st.info("Nenhum documento gerado nesta sessão.")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

# --- BLOCO 9: RANCHO RECEBIDO (CONFERÊNCIA DE CHEGADA) ---
elif st.session_state.pagina == "recebido":
    st.title("📦 Rancho Recebido")
    st.write("Utilize este campo para confirmar que os itens chegaram conforme a lista gerada.")
    if st.session_state.ultimo_pdf:
        st.warning("Verifique os itens recebidos com base no PDF abaixo:")
        st.download_button("📄 Abrir Lista para Conferência", data=st.session_state.ultimo_pdf, file_name="conferencia_recebimento.pdf")
        confirmado = st.checkbox("Confirmo que recebi o rancho conforme a lista gerada.")
        if confirmado: st.success("Recebimento registrado com sucesso!")
    else:
        st.error("Nenhuma lista foi gerada ainda. Vá em 'Tabela de Rancho' primeiro.")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()
