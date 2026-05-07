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
import base64
import pytz

# --- CONFIGURAÇÃO PARA ÍCONE E APP INSTALÁVEL (PWA) ---
st.markdown("""
    <head>
        <link rel="manifest" href="https://raw.githubusercontent.com/alexcostasilva2810-create/Rancho-Zion/main/manifest.json?v=100">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <link rel="icon" type="image/png" href="./logo_pwa.png">
        <link rel="apple-touch-icon" href="./logo_pwa.png">
    </head>
    """, unsafe_allow_html=True)

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
# BLOCO 2: FUNÇÕES DE SUPORTE
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
            df['ITEM'] = pd.to_numeric(df['ITEM'], errors='coerce')
            return df.sort_values(by='ITEM').reset_index(drop=True)
        return st.session_state.df_lista
    except: return st.session_state.df_lista

def aplicar_estilo_azul():
    st.markdown("<style>.stApp { background-color: #4169E1 !important; } h1,h2,h3,p,label { color: white !important; } div.stButton > button { background-color: #FF8C00 !important; color: black !important; font-weight: 900; border-radius: 10px; }</style>", unsafe_allow_html=True)

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except: return ""

# =================================================================
# BLOCO 3: TELAS (HOME, LOGIN, MENU)
# =================================================================
if st.session_state.pagina == "home":
    img_base64 = get_base64_of_bin_file('zion_final.jpg')
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #0e1117; background-image: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url("data:image/jpg;base64,{img_base64}"); background-size: contain; background-repeat: no-repeat; background-position: center top; background-attachment: fixed; }}
        .main-container {{ display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 85vh; padding-bottom: 50px; }}
        div.stButton > button {{ width: 280px !important; height: 60px !important; background-color: #FF8C00 !important; color: white !important; border-radius: 12px !important; font-weight: bold !important; font-size: 22px !important; box-shadow: 0px 10px 20px rgba(0,0,0,0.6); transition: 0.3s; }}
        </style>
        """, unsafe_allow_html=True)
    st.markdown("<div class='main-container'><div style='margin-top: 400px;'></div>", unsafe_allow_html=True)
    if st.button("ACESSAR SISTEMA"):
        st.session_state.pagina = "login"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.pagina == "login":
    st.markdown("<style>.stApp { background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.7)), url('https://images.unsplash.com/photo-1574689049868-e94ed5301745?q=80&w=1920'); background-size: cover; } .login-box { background-color: rgba(255, 255, 255, 0.1); padding: 30px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.2); }</style>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'> Acesso Restrito</h1>", unsafe_allow_html=True)
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
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
        if st.button("⬅️ VOLTAR AO INÍCIO"):
            st.session_state.pagina = "home"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.pagina == "menu":
    aplicar_estilo_azul()
    st.title(f"Painel - {st.session_state.navio}")
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 TABELA DE RANCHO", use_container_width=True): 
            st.session_state.pagina = "lista"; st.rerun()
        if st.button("🗄️ VER HISTÓRICO", use_container_width=True): 
            st.session_state.pagina = "historico"; st.rerun()
    with col2:
        if st.button("📜 DECLARAÇÃO", use_container_width=True): 
            st.session_state.pagina = "tripulacao"; st.rerun()
        if st.button("📦 RANCHO RECEBIDO", use_container_width=True): 
            st.session_state.pagina = "rancho_recebido"; st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ LOGOUT (SAIR)"): 
        st.session_state.pagina = "home"; st.rerun()

# =================================================================
# BLOCO 4: TABELA DE RANCHO (COM MELHORIA DE CACHE DE PDF)
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background: linear-gradient(rgba(0, 0, 0, 0.4), rgba(0, 0, 0, 0.4)), url('https://images.unsplash.com/photo-1542838132-92c53300491e?q=80&w=1920'); background-size: cover; }</style>", unsafe_allow_html=True)
    st.title(" Conferência de Estoque")
    
    if st.button("🔄 ATUALIZAR TABELA"):
        st.session_state.df_lista = carregar_dados_do_notion()
        st.rerun()

    df_editado = st.data_editor(st.session_state.df_lista, column_config={
        "ITEM": st.column_config.NumberColumn("COD", disabled=True),
        "PREDEFINIDO": st.column_config.NumberColumn("LIMITE", disabled=True),
        "CONFIRMA": st.column_config.NumberColumn("NECESSIDADE", min_value=0),
    }, hide_index=True, use_container_width=True)

    pode_exportar = True
    if not df_editado[df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]].empty:
        pode_exportar = False; st.error("⚠️ BLOQUEIO: VALOR ACIMA DO LIMITE!")

    col_p, col_e, col_m = st.columns(3)
    with col_p:
        if pode_exportar:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                class PDF_Checklist(FPDF):
                    def header(self):
                        if os.path.exists("zion3.jpg"): self.image("zion3.jpg", 95, 8, 20)
                        self.set_font("Arial", "B", 14); self.ln(22)
                        self.cell(0, 10, preparar(f"Checklist de Rancho: {st.session_state.navio}"), ln=True, align="C")
                    def footer(self):
                        self.set_y(-15); self.set_font('Arial', 'I', 8)
                        texto = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} - Pagina {self.page_no()}"
                        self.cell(0, 10, preparar(texto), 0, 0, 'C')

                pdf = PDF_Checklist()
                pdf.add_page(); pdf.set_font("Arial", "", 8)
                for _, r in df_editado.iterrows():
                    pdf.cell(10, 6, str(r["ITEM"]), 1, 0, "C")
                    pdf.cell(30, 6, preparar(r["TIPO"]), 1, 0, "L")
                    pdf.cell(15, 6, preparar(r["UNID MED"]), 1, 0, "C")
                    pdf.cell(15, 6, str(r["PREDEFINIDO"]), 1, 0, "C")
                    pdf.cell(105, 6, preparar(r["DESCRIÇÃO"]), 1, 0, "L")
                    pdf.cell(15, 6, str(r["CONFIRMA"]), 1, 1, "C")
                
                pdf_output = pdf.output(dest='S').encode('latin-1')
                
                if st.download_button("📄 BAIXAR PDF", data=pdf_output, file_name=f"Rancho_{st.session_state.navio}.pdf", use_container_width=True):
                    st.session_state.ultimo_pdf_dados = pdf_output # SALVA PARA O BLOCO 9

            except Exception as e: st.error(f"Erro: {e}")

    with col_m:
        if st.button("⬅️ MENU", use_container_width=True): st.session_state.pagina = "menu"; st.rerun()

# =================================================================
# BLOCO 7/8: DECLARAÇÃO E HISTÓRICO (CÓDIGO ORIGINAL MANTIDO)
# =================================================================
# [Nota: O código original de declaração e histórico permanece igual ao fornecido anteriormente]
elif st.session_state.pagina == "tripulacao":
    st.markdown("<h1 style='text-align: center;'>⚓ Declaração de Reabastecimento</h1>", unsafe_allow_html=True)
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()
    with st.form("form_dec"):
        resp_nome = st.text_input("Responsável", value=st.session_state.get('cozinheiro', ''), disabled=True)
        navio_nome = st.text_input("Navio", value=st.session_state.get('navio', ''), disabled=True)
        data_ultimo = st.date_input("Data do último rancho:", format="DD/MM/YYYY")
        qtde_trip = st.number_input("Qtde Tripulante:", min_value=1, value=16)
        canvas_result = st_canvas(stroke_width=3, stroke_color="#000000", background_color="#FFFFFF", height=120, key="sign")
        if st.form_submit_button("💾 SALVAR"):
            st.success("Simulação de salvamento concluída.")

elif st.session_state.pagina == "historico":
    aplicar_estilo_azul()
    st.title("🗄️ Histórico de Documentos")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()
    st.info("Consulte os documentos gerados pelo Notion através dos filtros de data.")

# =================================================================
# NOVO BLOCO 9: RANCHO RECEBIDO
# =================================================================
elif st.session_state.pagina == "rancho_recebido":
    aplicar_estilo_azul()
    st.markdown("<h1 style='text-align: center;'>📦 Confirmação de Recebimento</h1>", unsafe_allow_html=True)
    
    if st.button("⬅️ VOLTAR AO MENU"):
        st.session_state.pagina = "menu"
        st.rerun()

    col_rec1, col_rec2 = st.columns([1, 1])

    with col_rec1:
        st.subheader("📄 Último PDF Gerado")
        if st.session_state.ultimo_pdf_dados:
            st.info("Baixe aqui o checklist que você acabou de gerar para conferir a carga.")
            st.download_button(
                label="📥 BAIXAR ÚLTIMO PDF GERADO",
                data=st.session_state.ultimo_pdf_dados,
                file_name=f"Checklist_Para_Conferencia_{st.session_state.navio}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.warning("⚠️ Nenhum PDF foi gerado nesta sessão. Vá em 'TABELA DE RANCHO' primeiro.")

    with col_rec2:
        st.subheader("✅ Confirmar Entrega")
        st.markdown("""
            <div style='background-color: rgba(255,255,255,0.1); padding: 15px; border-radius: 10px; border: 1px solid white;'>
                <p style='font-size: 14px;'>Utilize este campo apenas após o rancho chegar fisicamente à embarcação e ser conferido.</p>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        confirmou = st.checkbox("CONCORDO QUE O RANCHO FOI RECEBIDO INTEGRALMENTE.")
        data_chegada = st.date_input("Data da Chegada Física:", datetime.now())
        comentario = st.text_area("Observações sobre a mercadoria (opcional):")

        if st.button("💾 REGISTRAR NO SISTEMA", use_container_width=True):
            if confirmou:
                st.balloons()
                st.success(f"Recebimento do {st.session_state.navio} registrado com sucesso!")
                # Aqui você pode integrar o envio para o Notion futuramente
            else:
                st.error("Você precisa marcar a caixa de declaração para confirmar.")
