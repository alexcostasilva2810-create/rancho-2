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

# --- FUNÇÕES DE API ---
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
    except: pass
    return st.session_state.df_lista

def aplicar_estilo_azul():
    st.markdown("<style>.stApp { background-color: #4169E1 !important; } h1,h2,h3,p,label,span { color: white !important; } div.stButton > button { background-color: #FF8C00 !important; color: black !important; font-weight: 900; border-radius: 10px; }</style>", unsafe_allow_html=True)

# =================================================================
# BLOCO 3, 4 E 5: HOME, LOGIN E MENU
# =================================================================
if st.session_state.pagina == "home":
    st.title("Zion Rancho App")
    if os.path.exists("zion_final.jpg"): st.image("zion_final.jpg")
    if st.button("ACESSAR SISTEMA"): st.session_state.pagina = "login"; st.rerun()

elif st.session_state.pagina == "login":
    st.title("Acesso Restrito")
    navio_sel = st.selectbox("Selecione sua Embarcação", list(USUARIOS.keys()))
    senha_dig = st.text_input("Senha", type="password")
    if st.button("ENTRAR"):
        if USUARIOS[navio_sel]["senha"] == senha_dig:
            st.session_state.cozinheiro = USUARIOS[navio_sel]["nome"]
            st.session_state.navio = navio_sel
            st.session_state.pagina = "menu"; st.rerun()
        else: st.error("Senha incorreta")

elif st.session_state.pagina == "menu":
    aplicar_estilo_azul()
    st.title(f"Painel - {st.session_state.navio}")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📋 TABELA DE RANCHO", use_container_width=True): st.session_state.pagina = "lista"; st.rerun()
        if st.button("📦 RANCHO RECEBIDO", use_container_width=True): st.session_state.pagina = "recebido"; st.rerun()
    with c2:
        if st.button("📜 DECLARAÇÃO", use_container_width=True): st.session_state.pagina = "tripulacao"; st.rerun()
        if st.button("🗄️ HISTÓRICO", use_container_width=True): st.session_state.pagina = "historico"; st.rerun()
    if st.button("⬅️ SAIR"): st.session_state.pagina = "home"; st.rerun()

# =================================================================
# BLOCO 6: TABELA DE CONFERÊNCIA
# =================================================================
elif st.session_state.pagina == "lista":
    st.title("Conferência de Estoque")
    if st.button("🔄 ATUALIZAR DO NOTION"):
        st.session_state.df_lista = carregar_dados_do_notion()
        st.rerun()

    df_editado = st.data_editor(st.session_state.df_lista, hide_index=True, use_container_width=True)
    st.session_state.df_lista = df_editado

    st.markdown("---")
    col_pdf, col_menu = st.columns(2)
    with col_pdf:
        def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, preparar(f"RANCHO - {st.session_state.navio}"), ln=True)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        
        if st.download_button("📄 BAIXAR PDF", data=pdf_bytes, file_name="rancho.pdf", use_container_width=True):
            st.session_state.df_ultimo_pedido = df_editado[df_editado["CONFIRMA"] > 0].copy()
            st.session_state.ultimo_pdf_bytes = pdf_bytes

    with col_menu:
        if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 7: DECLARAÇÃO (RESTAURADO COMPLETO)
# =================================================================
elif st.session_state.pagina == "tripulacao":
    aplicar_estilo_azul()
    st.markdown("<h1 style='text-align: center;'>⚓ Declaração de Reabastecimento</h1>", unsafe_allow_html=True)
    
    col_esc, col_val = st.columns(2)
    with col_esc:
        escolta_sel = st.radio("O navio está com escolta?", ["NÃO", "SIM"], index=0, horizontal=True)
        dias_duracao = 12 if escolta_sel == "SIM" else 15
    with col_val:
        data_recebimento = st.date_input("Data prevista para o novo rancho:", datetime.now())
        data_validade = data_recebimento + timedelta(days=dias_duracao)
        st.info(f"📅 Validade: {data_validade.strftime('%d/%m/%Y')} ({dias_duracao} dias)")

    with st.form("form_declaracao"):
        c1, c2 = st.columns(2)
        with c1:
            resp_nome = st.text_input("Responsável", value=st.session_state.cozinheiro, disabled=True)
            navio_nome = st.text_input("Navio", value=st.session_state.navio, disabled=True)
            origem = st.text_input("Porto de Origem", value="Porto Velho")
            data_ultimo = st.date_input("Data do último rancho:")
        with c2:
            qtde_trip = st.number_input("Qtde Tripulante:", min_value=1, value=16)
            destino = st.text_input("Porto de Destino", value="Novo remanso")
        
        consideracoes = st.text_area("Considerações:", value="Consumo regular conforme escala.")
        st.write("Assinatura Digital:")
        canvas_result = st_canvas(stroke_width=3, stroke_color="#000000", background_color="#FFFFFF", height=120, key="canvas_decl")
        
        if st.form_submit_button("💾 SALVAR E GERAR PDF"):
            if canvas_result.image_data is not None:
                # Gerar PDF da Declaração
                pdf_d = FPDF(); pdf_d.add_page()
                def f(t): return unicodedata.normalize('NFKD', str(t or "")).encode('latin-1', 'ignore').decode('latin-1')
                pdf_d.set_font("Arial", "B", 16); pdf_d.cell(0, 10, f("DECLARAÇÃO DE RANCHO"), ln=True, align="C")
                pdf_d.set_font("Arial", "", 12)
                pdf_d.multi_cell(0, 10, f(f"Certifico que o navio {navio_nome} com {qtde_trip} tripulantes está abastecido por {dias_duracao} dias."))
                
                # Enviar para Notion (Histórico)
                headers_n = {"Authorization": f"Bearer {NOTION_TOKEN}", "Content-Type": "application/json", "Notion-Version": "2022-06-28"}
                payload = {
                    "parent": {"database_id": ID_HISTORICO_NOTION},
                    "properties": {
                        "Responsável": {"title": [{"text": {"content": resp_nome}}]},
                        "Navio": {"rich_text": [{"text": {"content": navio_nome}}]},
                        "Novo Rancho": {"date": {"start": data_recebimento.isoformat()}}
                    }
                }
                res = requests.post("https://api.notion.com/v1/pages", headers=headers_n, json=payload)
                if res.status_code == 200: st.success("✅ Enviado ao histórico!")
                st.download_button("📥 BAIXAR DECLARAÇÃO", data=pdf_d.output(dest='S').encode('latin-1'), file_name="Declaracao.pdf")

    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 9: RANCHO RECEBIDO
# =================================================================
elif st.session_state.pagina == "recebido":
    aplicar_estilo_azul()
    st.title("📦 Rancho Recebido")
    if not st.session_state.df_ultimo_pedido.empty:
        c_tab, c_btn = st.columns([0.85, 0.15])
        with c_tab:
            st.dataframe(st.session_state.df_ultimo_pedido, hide_index=True, use_container_width=True)
        with c_btn:
            st.write("PDF")
            if st.session_state.ultimo_pdf_bytes:
                st.download_button("📥", data=st.session_state.ultimo_pdf_bytes, file_name="Conferencia.pdf", use_container_width=True)
        
        if st.checkbox("Confirmo o recebimento"): st.success("Confirmado!")
    else: st.warning("Nenhum pedido gerado.")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 8: HISTÓRICO (MANTIDO)
# =================================================================
elif st.session_state.pagina == "historico":
    st.title("🗄️ Histórico")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()
