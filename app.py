import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
from datetime import datetime, timedelta
import unicodedata
from fpdf import FPDF
from PIL import Image
import os
import requests
import io
import pytz
import base64

# =================================================================
# BLOCO 1: CONFIGURAÇÕES, CONSTANTES E ESTADOS
# =================================================================
st.set_page_config(page_title="Zion Rancho App", layout="wide")

COLUNAS_PADRAO = ["ITEM", "DESCRIÇÃO", "TIPO", "UNID MED", "PREDEFINIDO", "CONFIRMA"]
NOTION_TOKEN = "ntn_jZ6353375938j9kJFqKWjD0N4ONt1rwP515tsIMwxtucHa"
DATABASE_ID = "2e3025de7b79803abe0efde74f87a2e1" 
ID_HISTORICO_NOTION = "2e5025de7b79803187a4d8b865179440"

if 'pagina' not in st.session_state: st.session_state.pagina = "home"
if 'cozinheiro' not in st.session_state: st.session_state.cozinheiro = ""
if 'navio' not in st.session_state: st.session_state.navio = ""
if 'df_lista' not in st.session_state: st.session_state.df_lista = pd.DataFrame(columns=COLUNAS_PADRAO)
# NOVOS ESTADOS PARA O RANCHO RECEBIDO
if 'df_ultimo_pedido' not in st.session_state: st.session_state.df_ultimo_pedido = pd.DataFrame()
if 'ultimo_pdf_bytes' not in st.session_state: st.session_state.ultimo_pdf_bytes = None

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

# [FUNÇÕES DE SUPORTE - MANTIDAS IGUAIS AO SEU ORIGINAL]
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
            df['ITEM'] = pd.to_numeric(df['ITEM'], errors='coerce')
            return df.sort_values(by='ITEM').reset_index(drop=True)
        return st.session_state.df_lista
    except: return st.session_state.df_lista

def aplicar_estilo_azul():
    st.markdown("<style>.stApp { background-color: #4169E1 !important; } h1,h2,h3,p,label { color: white !important; } div.stButton > button { background-color: #FF8C00 !important; color: black !important; font-weight: 900; border-radius: 10px; }</style>", unsafe_allow_html=True)

# =================================================================
# BLOCO 3, 4 E 5: HOME, LOGIN E MENU (MANTIDOS)
# =================================================================
# [Omitidos aqui para brevidade, mas devem permanecer no seu arquivo]
# ... (Seu código da Home e Login continua aqui) ...

if st.session_state.pagina == "home":
    # (Seu código da Home aqui)
    pass 

elif st.session_state.pagina == "login":
    # (Seu código do Login aqui)
    pass

elif st.session_state.pagina == "menu":
    aplicar_estilo_azul()
    st.title(f"Painel - {st.session_state.navio}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 TABELA DE RANCHO", use_container_width=True): st.session_state.pagina = "lista"; st.rerun()
        # BOTÃO PARA A NOVA PÁGINA
        if st.button("📦 RANCHO RECEBIDO", use_container_width=True): st.session_state.pagina = "recebido"; st.rerun()
    with col2:
        if st.button("📜 DECLARAÇÃO", use_container_width=True): st.session_state.pagina = "tripulacao"; st.rerun()
        if st.button("🗄️ HISTÓRICO", use_container_width=True): st.session_state.pagina = "historico"; st.rerun()
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ LOGOUT (SAIR)"): st.session_state.pagina = "home"; st.rerun()

# =================================================================
# BLOCO 6: TABELA DE RANCHO (COM MELHORIA DE SALVAMENTO)
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background: linear-gradient(rgba(0,0,0,0.4),rgba(0,0,0,0.4)), url('https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1920'); background-size: cover; }</style>", unsafe_allow_html=True)
    st.title("Conferência de Estoque")
    
    if st.button("🔄 ATUALIZAR TABELA"):
        st.session_state.df_lista = carregar_dados_do_notion()
        st.rerun()

    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True, key="ed_r")
    st.session_state.df_lista = df_editado # Mantém edição salva

    pode_exportar = not (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()
    if not pode_exportar: st.error("⚠️ BLOQUEIO: VALOR ACIMA DO LIMITE!")

    st.markdown("---")
    col_pdf, col_excel, col_menu = st.columns(3)
    
    with col_pdf:
        if pode_exportar:
            def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, preparar(f"Checklist: {st.session_state.navio}"), ln=True, align="C")
            # ... (Logica de preenchimento do PDF que você já tem) ...
            
            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            # MELHORIA: Quando clica no download, salva o estado para a tela de "Recebido"
            if st.download_button("📄 BAIXAR PDF", data=pdf_bytes, file_name="rancho.pdf", use_container_width=True):
                st.session_state.df_ultimo_pedido = df_editado[df_editado["CONFIRMA"] > 0].copy()
                st.session_state.ultimo_pdf_bytes = pdf_bytes

    with col_menu:
        if st.button("⬅️ MENU PRINCIPAL", use_container_width=True): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# NOVO BLOCO 9: RANCHO RECEBIDO (TABELA + DOWNLOAD À DIREITA)
# =================================================================
elif st.session_state.pagina == "recebido":
    aplicar_estilo_azul()
    st.markdown("<h1 style='text-align: center;'>📦 Rancho Recebido</h1>", unsafe_allow_html=True)

    if not st.session_state.df_ultimo_pedido.empty:
        st.write("### Itens a conferir no recebimento:")
        
        # LAYOUT: Tabela (85%) e Botão Download (15%)
        c_tab, c_btn = st.columns([0.85, 0.15])
        
        with c_tab:
            st.dataframe(st.session_state.df_ultimo_pedido, hide_index=True, use_container_width=True)
            
        with c_btn:
            st.markdown("<p style='text-align:center;'><b>PDF</b></p>", unsafe_allow_html=True)
            if st.session_state.ultimo_pdf_bytes:
                st.download_button("📥", 
                                   data=st.session_state.ultimo_pdf_bytes, 
                                   file_name="conferencia_recebimento.pdf",
                                   use_container_width=True,
                                   help="Baixar PDF do último rancho gerado")
        
        st.markdown("---")
        if st.checkbox("✅ Confirmo que recebi os itens acima corretamente."):
            st.success("Recebimento confirmado!")
    else:
        st.warning("Nenhuma lista de rancho foi gerada ainda nesta sessão.")

    if st.button("⬅️ VOLTAR AO MENU"):
        st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCOS RESTANTES (DECLARAÇÃO E HISTÓRICO - MANTIDOS)
# =================================================================
# ... (O restante do seu código permanece o mesmo) ...
