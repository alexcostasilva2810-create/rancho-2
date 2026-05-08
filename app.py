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
# BLOCO 1: CONFIGURAÇÕES E ESTADOS (CRÍTICO PARA NÃO DAR TELA BRANCA)
# =================================================================
st.set_page_config(page_title="Zion Rancho App", layout="wide")
if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"])
if 'df_ultimo_pedido' not in st.session_state: st.session_state.df_ultimo_pedido = pd.DataFrame()
if 'ultimo_pdf' not in st.session_state: st.session_state.ultimo_pdf = None

# =================================================================
# BLOCO 2: USUÁRIOS
# =================================================================
USUARIOS = {"ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"}, "JATOBA": {"nome": "STEFANI", "senha": "2558"}, "JACARANDA": {"nome": "GABRIEL", "senha": "6352"}}

# =================================================================
# BLOCO 3: HOME
# =================================================================
if st.session_state.pagina == "home":
    st.title("Zion Rancho App")
    if os.path.exists("zion_final.jpg"): st.image("zion_final.jpg")
    if st.button("ACESSAR SISTEMA"): st.session_state.pagina = "login"; st.rerun()

# =================================================================
# BLOCO 4: LOGIN
# =================================================================
elif st.session_state.pagina == "login":
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
    navio = st.selectbox("Embarcação", list(USUARIOS.keys()))
    senha = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if USUARIOS[navio]["senha"] == senha:
            st.session_state.cozinheiro, st.session_state.navio = USUARIOS[navio]["nome"], navio
            st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 5: MENU PRINCIPAL
# =================================================================
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

# =================================================================
# BLOCO 6: LISTA + NOTION + GERAÇÃO PDF
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.title("Conferência de Estoque")
    
    if st.button("🔄 CARREGAR ITENS DO NOTION"):
        try:
            url = "https://raw.githubusercontent.com/alexcostasilva2810-create/Rancho-Zion/main/estoque.csv"
            res = requests.get(url)
            if res.status_code == 200:
                st.session_state.df_lista = pd.read_csv(io.StringIO(res.text))
                st.success("Lista sincronizada!")
                st.rerun()
        except: st.error("Erro Notion")

    df_edit = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)
    st.session_state.df_lista = df_edit
    
    excedeu = (df_edit["CONFIRMA"] > df_edit["PREDEFINIDO"]).any()
    if excedeu: st.error("LIMITE EXCEDIDO!")

    st.markdown("---")
    c_pdf, c_xls, c_menu = st.columns(3)
    with c_menu:
        if st.button("⬅️ MENU", use_container_width=True): st.session_state.pagina = "menu"; st.rerun()
    
    if not excedeu:
        with c_pdf:
            def prep(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
            class PDF(FPDF):
                def footer(self):
                    self.set_y(-15)
                    tz = pytz.timezone('America/Sao_Paulo')
                    self.cell(0, 10, prep(f"Gerado: {datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')}"), 0, 0, 'C')
            pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, prep("LISTA DE RANCHO"), ln=True, align='C')
            out = pdf.output(dest='S').encode('latin-1')
            
            if st.download_button("📄 PDF", data=out, file_name="rancho.pdf", use_container_width=True):
                # SALVA OS DADOS PARA O BLOCO 7
                st.session_state.df_ultimo_pedido = df_edit.copy()
                st.session_state.ultimo_pdf = out

# =================================================================
# BLOCO 7: RANCHO RECEBIDO (TABELA + ÍCONE DIREITO) - CORRIGIDO
# =================================================================
elif st.session_state.pagina == "recebido":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>📦 Recebimento</h1>", unsafe_allow_html=True)

    if not st.session_state.df_ultimo_pedido.empty:
        col_tab, col_btn = st.columns([0.85, 0.15])
        with col_tab:
            st.dataframe(st.session_state.df_ultimo_pedido, hide_index=True, use_container_width=True)
        with col_btn:
            st.write("Baixar")
            if st.session_state.ultimo_pdf:
                st.download_button("📥", data=st.session_state.ultimo_pdf, file_name="Conferencia.pdf", use_container_width=True)
        
        st.markdown("---")
        if st.checkbox("Confirmar recebimento conforme tabela"): st.success("Registrado!")
    else:
        st.warning("Gere uma lista primeiro na Tabela de Rancho.")
    
    if st.button("⬅️ VOLTAR AO MENU"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 8: ASSINATURA
# =================================================================
elif st.session_state.pagina == "tripulacao":
    st.title("📜 Assinatura")
    st_canvas(stroke_width=3, background_color="#FFFFFF", height=150, key="sign")
    if st.button("⬅️ VOLTAR"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 9: HISTÓRICO / RODAPÉ
# =================================================================
elif st.session_state.pagina == "historico":
    st.title("🗄️ Histórico")
    if st.session_state.ultimo_pdf: st.success("Último documento salvo pronto para download.")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

if st.session_state.pagina != "home":
    st.caption(f"Operador: {st.session_state.get('cozinheiro','-')} | © Zion 2026")
