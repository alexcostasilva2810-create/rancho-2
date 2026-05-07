import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from datetime import datetime
import unicodedata
from fpdf import FPDF
import os
import requests
import base64

# --- CONFIGURAÇÃO PWA ---
st.markdown("""
    <head>
        <link rel="manifest" href="https://raw.githubusercontent.com/alexcostasilva2810-create/Rancho-Zion/main/manifest.json?v=100">
        <meta name="mobile-web-app-capable" content="yes">
    </head>
    """, unsafe_allow_html=True)

# =================================================================
# BLOCO 1: CONFIGURAÇÕES E ESTADOS
# =================================================================
st.set_page_config(page_title="Zion Rancho App", layout="wide")

COLUNAS_PADRAO = ["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"]
NOTION_TOKEN = "ntn_jZ6353375938j9kJFqKWjD0N4ONt1rwP515tsIMwxtucHa"
DATABASE_ID = "2e3025de7b79803abe0efde74f87a2e1"

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'cozinheiro' not in st.session_state: st.session_state.cozinheiro = ""
if 'navio' not in st.session_state: st.session_state.navio = ""
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=COLUNAS_PADRAO)
if 'ultimo_pdf_dados' not in st.session_state: st.session_state.ultimo_pdf_dados = None

USUARIOS = {
    "JATOBA": {"nome": "STEFANI", "senha": "2558"},
    "JACARANDA": {"nome": "GABRIEL", "senha": "6352"},
    "ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"},
    "ANGELO": {"nome": "ELIOMAR", "senha": "7221"},
    "ENCARREGADO CATIANO": {"nome": "CATIANO", "senha": "8935"},
    "ENCARREGADO ERITON": {"nome": "ERITON", "senha": "1867"},
    "CUMARU": {"nome": "JULIO CESA", "senha": "8551"},
    "LUIZ FELIPE": {"nome": "IVAN SOARES", "senha": "8929"},
    "AROEIRA": {"nome": "SARA VIRGULINO", "senha": "5881"},
    "ANGICO": {"nome": "SARA ANACLETO", "senha": "6678"},
    "BRENO": {"nome": "JOHNNATAN", "senha": "2870"},
    "SAMAUMA": {"nome": "DANTAS MORAES", "senha": "7211"},
    "ENCARREGADO MANAUS EUCLIDES": {"nome": "Elcicley Dourado", "senha": "301003"},
    "ENCARREGADO MIRITITUBA JANARI": {"nome": "Janary Freitas", "senha": "303010"},
    "SUPERVISOR SANTARÉM": {"nome": "Rafael Artur", "senha": "103010"},
    "IPE": {"nome": "ALUIZO PEREIRA", "senha": "8419"},
    "TIMBORANA": {"nome": "ROGILEIA", "senha": "6300"},
    "CASTANHEIRA": {"nome": "ELEONILDE", "senha": "6300"}
}

# =================================================================
# BLOCO 2: FUNÇÕES
# =================================================================
def carregar_dados_do_notion():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    headers = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            results = response.json().get("results", [])
            dados = []
            for page in results:
                p = page.get("properties", {})
                dados.append({
                    "ITEM": p.get("ITEM", {}).get("title", [{}])[0].get("plain_text", ""),
                    "DESCRIÇÃO": p.get("DESCRIÇÃO", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                    "TIPO": p.get("TIPO", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                    "UNID MED": p.get("UNID MED", {}).get("rich_text", [{}])[0].get("plain_text", ""),
                    "PREDEFINIDO": p.get("PREDEFINIDO", {}).get("number", 0),
                    "CONFIRMA": 0
                })
            df = pd.DataFrame(dados)
            df['ITEM'] = pd.to_numeric(df['ITEM'], errors='coerce').fillna(0).astype(int) # Remove o .0
            return df.sort_values(by='ITEM').reset_index(drop=True)
        return st.session_state.df_lista
    except: return st.session_state.df_lista

def aplicar_estilo_azul():
    st.markdown("<style>.stApp { background-color: #4169E1 !important; } h1,h2,h3,p,label { color: white !important; } div.stButton > button { background-color: #FF8C00 !important; color: black !important; font-weight: 900; border-radius: 10px; }</style>", unsafe_allow_html=True)

# =================================================================
# BLOCO 3: NAVEGAÇÃO
# =================================================================
if st.session_state.pagina == "home":
    st.title("Zion Rancho App")
    if st.button("ACESSAR SISTEMA"):
        st.session_state.pagina = "login"
        st.rerun()

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

elif st.session_state.pagina == "menu":
    aplicar_estilo_azul()
    st.title(f"Painel - {st.session_state.navio}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 TABELA DE RANCHO", use_container_width=True): 
            st.session_state.pagina = "lista"; st.rerun()
    with col2:
        if st.button("📦 RANCHO RECEBIDO", use_container_width=True): 
            st.session_state.pagina = "rancho_recebido"; st.rerun()
    if st.button("⬅️ LOGOUT"): 
        st.session_state.pagina = "home"; st.rerun()

# =================================================================
# BLOCO 4: TABELA E GERAÇÃO DE PDF (COM CORRIGENDAS)
# =================================================================
elif st.session_state.pagina == "lista":
    st.title("Conferência de Estoque")
    
    if st.button("🔄 CARREGAR ITENS DO NOTION"):
        st.session_state.df_lista = carregar_dados_do_notion()
        st.rerun()

    df_editado = st.data_editor(st.session_state.df_lista, column_config={
        "ITEM": st.column_config.NumberColumn("COD", format="%d", disabled=True),
        "CONFIRMA": st.column_config.NumberColumn("NECESSIDADE", min_value=0),
    }, hide_index=True, use_container_width=True)

    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

    try:
        def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
        
        class PDF_Checklist(FPDF):
            def header(self):
                # Título 1: ZION TECNOLOGIA em Azul Marinho (R=0, G=0, B=128)
                self.set_text_color(0, 0, 128)
                self.set_font("Arial", "B", 18)
                self.cell(0, 10, "ZION TECNOLOGIA", ln=True, align="C")
                
                # Título 2: Lista de Rancho
                self.set_text_color(0, 0, 0) # Volta para preto
                self.set_font("Arial", "B", 12)
                self.cell(0, 8, preparar(f"Lista de Rancho do Empurrador: {st.session_state.navio}"), ln=True, align="C")
                
                # Título 3: Solicitante (Nome do usuário logado)
                self.set_font("Arial", "", 11)
                self.cell(0, 8, preparar(f"Solicitante: {st.session_state.cozinheiro}"), ln=True, align="C")
                
                self.ln(5)
                # Cabeçalho da Tabela
                self.set_fill_color(230, 230, 230)
                self.set_font("Arial", "B", 8)
                self.cell(10, 7, "COD", 1, 0, "C", True)
                self.cell(25, 7, "TIPO", 1, 0, "C", True)
                self.cell(12, 7, "UNID", 1, 0, "C", True)
                self.cell(85, 7, "DESCRICAO", 1, 0, "C", True)
                self.cell(15, 7, "LIMITE", 1, 0, "C", True)
                self.cell(15, 7, "SOLIC.", 1, 0, "C", True)
                self.cell(18, 7, "CHECK", 1, 1, "C", True)

        pdf = PDF_Checklist()
        pdf.add_page()
        pdf.set_font("Arial", "", 8)
        
        for _, r in df_editado.iterrows():
            # Removemos o .0 forçando o ITEM para int no PDF também
            codigo_limpo = str(int(float(r["ITEM"])))
            
            pdf.cell(10, 6, codigo_limpo, 1, 0, "C")
            pdf.cell(25, 6, preparar(r["TIPO"]), 1, 0, "L")
            pdf.cell(12, 6, preparar(r["UNID MED"]), 1, 0, "C")
            pdf.cell(85, 6, preparar(r["DESCRIÇÃO"]), 1, 0, "L")
            pdf.cell(15, 6, str(r["PREDEFINIDO"]), 1, 0, "C")
            pdf.cell(15, 6, str(r["CONFIRMA"]), 1, 0, "C")
            
            x_pos, y_pos = pdf.get_x(), pdf.get_y()
            pdf.cell(18, 6, "", 1, 1, "C") 
            pdf.rect(x_pos + 7, y_pos + 1, 4, 4) 

        pdf_output = pdf.output(dest='S').encode('latin-1')
        st.download_button("📄 GERAR E BAIXAR PDF", data=pdf_output, file_name=f"Rancho_{st.session_state.navio}.pdf", use_container_width=True)
        st.session_state.ultimo_pdf_dados = pdf_output

    except Exception as e: st.error(f"Erro ao gerar PDF: {e}")

elif st.session_state.pagina == "rancho_recebido":
    aplicar_estilo_azul()
    st.title("📦 Recebimento")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()
    if st.session_state.ultimo_pdf_dados:
        st.download_button("📥 BAIXAR PDF PARA CONFERÊNCIA", data=st.session_state.ultimo_pdf_dados, file_name="Conferencia.pdf")
