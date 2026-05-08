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
# BLOCO 1: CONFIGURAÇÕES E ESTADOS
# =================================================================
st.set_page_config(page_title="Zion Rancho App", layout="wide")

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"])
if 'df_ultimo_pedido' not in st.session_state: st.session_state.df_ultimo_pedido = pd.DataFrame()
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
# BLOCO 3: HOME
# =================================================================
if st.session_state.pagina == "home":
    st.markdown("<h1 style='text-align: center;'>Zion Rancho App</h1>", unsafe_allow_html=True)
    if os.path.exists("zion_final.jpg"):
        st.image("zion_final.jpg", use_container_width=True)
    
    col_btn_home = st.columns([1, 1, 1])
    with col_btn_home[1]:
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            st.session_state.pagina = "login"
            st.rerun()

# =================================================================
# BLOCO 4: LOGIN
# =================================================================
elif st.session_state.pagina == "login":
    st.markdown("<h1 style='text-align: center;'>Acesso Restrito</h1>", unsafe_allow_html=True)
    navio_sel = st.selectbox("Embarcação", list(USUARIOS.keys()))
    senha_dig = st.text_input("Senha", type="password")
    
    if st.button("ENTRAR", use_container_width=True):
        user = USUARIOS.get(navio_sel)
        if user and senha_dig == user["senha"]:
            st.session_state.cozinheiro = user["nome"]
            st.session_state.navio = navio_sel
            st.session_state.pagina = "menu"
            st.rerun()
        else:
            st.error("Senha Incorreta")

# =================================================================
# BLOCO 5: MENU PRINCIPAL
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
    
    st.markdown("---")
    if st.button("⬅️ LOGOUT"):
        st.session_state.pagina = "home"
        st.rerun()

# =================================================================
# BLOCO 6: TABELA DE CONFERÊNCIA (NOTION)
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.title("Conferência de Estoque")
    
    # Botão de Carregamento Notion
    if st.button("🔄 CARREGAR ITENS DO NOTION"):
        try:
            url = "https://raw.githubusercontent.com/alexcostasilva2810-create/Rancho-Zion/main/estoque.csv"
            response = requests.get(url)
            if response.status_code == 200:
                st.session_state.df_lista = pd.read_csv(io.StringIO(response.text))
                st.success("Lista sincronizada com o Notion!")
                st.rerun()
        except:
            st.error("Erro ao carregar do Notion")

    # Editor da Tabela Cinza
    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)
    st.session_state.df_lista = df_editado
    
    # Trava de Segurança
    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()
    if excedeu:
        st.markdown("<p style='color: red; font-weight: bold; text-align: center;'>O LIMITE FOI EXCEDIDO!</p>", unsafe_allow_html=True)

    st.markdown("---")
    c_pdf, c_xls, c_menu = st.columns(3)
    
    with c_menu:
        if st.button("⬅️ MENU", use_container_width=True):
            st.session_state.pagina = "menu"; st.rerun()
    
    if not excedeu:
        with c_pdf:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                class PDF(FPDF):
                    def footer(self):
                        self.set_y(-15)
                        tz_br = pytz.timezone('America/Sao_Paulo')
                        self.cell(0, 10, preparar(f"Gerado em: {datetime.now(tz_br).strftime('%d/%m/%Y %H:%M:%S')}"), 0, 0, 'C')
                
                pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", "B", 14)
                pdf.cell(0, 10, preparar(f"ZION - {st.session_state.navio}"), ln=True, align='C')
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                if st.download_button("📄 GERAR PDF", data=pdf_bytes, file_name="rancho.pdf", use_container_width=True):
                    st.session_state.df_ultimo_pedido = df_editado.copy()
                    st.session_state.ultimo_pdf = pdf_bytes
            except: st.error("Erro PDF")

# =================================================================
# BLOCO 7: RANCHO RECEBIDO (TABELA + DOWNLOAD DIREITA)
# =================================================================
elif st.session_state.pagina == "recebido":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>📦 Rancho Recebido</h1>", unsafe_allow_html=True)

    if not st.session_state.df_ultimo_pedido.empty:
        col_tab, col_down = st.columns([0.85, 0.15])
        
        with col_tab:
            st.dataframe(st.session_state.df_ultimo_pedido, hide_index=True, use_container_width=True)
            
        with col_down:
            st.write("PDF")
            if st.session_state.ultimo_pdf:
                st.download_button("📥", data=st.session_state.ultimo_pdf, file_name="Conferencia.pdf", use_container_width=True)

        st.markdown("---")
        if st.checkbox("Confirmar recebimento total"): st.success("Registrado!")
    else:
        st.warning("Nenhum pedido gerado.")
    
    if st.button("⬅️ VOLTAR AO MENU"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 8: DECLARAÇÃO / ASSINATURA
# =================================================================
elif st.session_state.pagina == "tripulacao":
    st.title("📜 Assinatura da Declaração")
    st_canvas(stroke_width=3, background_color="#FFFFFF", height=150, key="sign_canvas")
    if st.button("⬅️ VOLTAR"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 9: HISTÓRICO
# =================================================================
elif st.session_state.pagina == "historico":
    st.title("🗄️ Histórico")
    if st.session_state.ultimo_pdf:
        st.download_button("Baixar Cópia do Último PDF", data=st.session_state.ultimo_pdf, file_name="historico_rancho.pdf")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

# Rodapé Operador
if st.session_state.pagina != "home":
    st.caption(f"Operador: {st.session_state.get('cozinheiro','-')} | © Zion Tecnologia 2026")
