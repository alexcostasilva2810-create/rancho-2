import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import unicodedata
from fpdf import FPDF
import requests
import io

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
    "ADMINISTRADOR": {"nome": "ALEX", "senha": "2463"},
    "JATOBA": {"nome": "STEFANI", "senha": "2558"},
    "JACARANDA": {"nome": "GABRIEL", "senha": "6352"}
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
            df['ITEM'] = pd.to_numeric(df['ITEM'], errors='coerce').fillna(0).astype(int)
            return df[COLUNAS_PADRAO].sort_values(by='ITEM').reset_index(drop=True)
        return st.session_state.df_lista
    except: return st.session_state.df_lista

def aplicar_estilo_azul():
    st.markdown("<style>.stApp { background-color: #4169E1 !important; } h1,h2,h3,p,label { color: white !important; } div.stButton > button { background-color: #FF8C00 !important; color: black !important; font-weight: 900; border-radius: 10px; }</style>", unsafe_allow_html=True)

# =================================================================
# BLOCO 3: TELAS INICIAIS (HOME/LOGIN/MENU)
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
        if st.button("📜 DECLARAÇÃO", use_container_width=True): 
            st.session_state.pagina = "tripulacao"; st.rerun()
    with col2:
        if st.button("📦 RANCHO RECEBIDO", use_container_width=True): 
            st.session_state.pagina = "rancho_recebido"; st.rerun()
        if st.button("🗄️ VER HISTÓRICO", use_container_width=True): 
            st.session_state.pagina = "historico"; st.rerun()
    if st.button("⬅️ LOGOUT"): 
        st.session_state.pagina = "home"; st.rerun()

# =================================================================
# BLOCO 4: TABELA DE CONFERÊNCIA (TRAVA DE LIMITE + FUNDO CINZA)
# =================================================================
elif st.session_state.pagina == "lista":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; } .stDataFrame { background-color: white !important; border-radius: 10px; }</style>", unsafe_allow_html=True)
    st.title("Conferência de Estoque")
    
    if st.button("🔄 CARREGAR ITENS DO NOTION"):
        st.session_state.df_lista = carregar_dados_do_notion()
        st.rerun()

    df_editado = st.data_editor(
        st.session_state.df_lista,
        hide_index=True,
        use_container_width=True
    )

    # LÓGICA DE VALIDAÇÃO DE LIMITE
    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()

    if excedeu:
        st.markdown("<p style='color: red; font-weight: bold; font-size: 20px; text-align: center;'>O limite foi excedido você não pode continuar</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_pdf, col_excel, col_btn_menu = st.columns([1,1,1])

    with col_btn_menu:
        if st.button("⬅️ MENU", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()

    # BLOQUEIO DOS BOTÕES SE O LIMITE FOR EXCEDIDO
    if not excedeu:
        with col_excel:
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_editado.to_excel(writer, index=False, sheet_name='Rancho')
            if st.download_button(label="excel EXCEL", data=output_excel.getvalue(), file_name=f"Rancho_{st.session_state.navio}.xlsx", use_container_width=True):
                st.session_state.df_lista['CONFIRMA'] = 0
                st.rerun()

        with col_pdf:
            try:
                def preparar(t): return unicodedata.normalize('NFKD', str(t)).encode('latin-1', 'ignore').decode('latin-1')
                class PDF_Checklist(FPDF):
                    def header(self):
                        self.set_text_color(0, 0, 128)
                        self.set_font("Arial", "B", 18)
                        self.cell(0, 10, "ZION TECNOLOGIA", ln=True, align="C")
                        self.set_text_color(0, 0, 0)
                        self.set_font("Arial", "B", 12)
                        self.cell(0, 8, preparar(f"Lista de Rancho: {st.session_state.navio}"), ln=True, align="C")
                        self.set_font("Arial", "", 11)
                        self.cell(0, 8, preparar(f"Solicitante: {st.session_state.cozinheiro}"), ln=True, align="C")
                        self.ln(5)
                        self.set_fill_color(230, 230, 230)
                        self.set_font("Arial", "B", 8)
                        self.cell(10, 7, "COD", 1, 0, "C", True)
                        self.cell(75, 7, "DESCRICAO", 1, 0, "C", True)
                        self.cell(35, 7, "TIPO", 1, 0, "C", True)
                        self.cell(15, 7, "UNID", 1, 0, "C", True)
                        self.cell(15, 7, "PRED.", 1, 0, "C", True)
                        self.cell(15, 7, "SOLIC.", 1, 0, "C", True)
                        self.cell(25, 7, "CHECK", 1, 1, "C", True)

                pdf = PDF_Checklist()
                pdf.add_page()
                pdf.set_font("Arial", "", 8)
                for _, r in df_editado.iterrows():
                    pdf.cell(10, 6, str(int(r["ITEM"])), 1, 0, "C")
                    pdf.cell(75, 6, preparar(r["DESCRIÇÃO"]), 1, 0, "L")
                    pdf.cell(35, 6, preparar(r["TIPO"]), 1, 0, "C")
                    pdf.cell(15, 6, preparar(r["UNID MED"]), 1, 0, "C")
                    pdf.cell(15, 6, str(r["PREDEFINIDO"]), 1, 0, "C")
                    pdf.cell(15, 6, str(r["CONFIRMA"]), 1, 0, "C")
                    x_pos, y_pos = pdf.get_x(), pdf.get_y()
                    pdf.cell(25, 6, "", 1, 1, "C")
                    pdf.rect(x_pos + 10.5, y_pos + 1, 4, 4)

                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                if st.download_button("📄 PDF", data=pdf_bytes, file_name=f"Rancho_{st.session_state.navio}.pdf", use_container_width=True):
                    st.session_state.df_lista['CONFIRMA'] = 0
                    st.session_state.ultimo_pdf_dados = pdf_bytes
                    st.rerun()
            except Exception as e: st.error(f"Erro PDF: {e}")

# =================================================================
# BLOCO 5: TRIPULAÇÃO / DECLARAÇÃO
# =================================================================
elif st.session_state.pagina == "tripulacao":
    st.markdown("<h1 style='text-align: center;'>⚓ Declaração de Reabastecimento</h1>", unsafe_allow_html=True)
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()
    with st.form("form_dec"):
        st.text_input("Responsável", value=st.session_state.cozinheiro, disabled=True)
        st.text_input("Navio", value=st.session_state.navio, disabled=True)
        st.date_input("Data do último rancho:", format="DD/MM/YYYY")
        st.number_input("Qtde Tripulante:", min_value=1, value=16)
        st_canvas(stroke_width=3, stroke_color="#000000", background_color="#FFFFFF", height=120, key="sign")
        if st.form_submit_button("💾 SALVAR"): st.success("Dados salvos.")

# =================================================================
# BLOCO 6: HISTÓRICO
# =================================================================
elif st.session_state.pagina == "historico":
    aplicar_estilo_azul()
    st.title("🗄️ Histórico de Documentos")
    if st.button("⬅️ MENU"): st.session_state.pagina = "menu"; st.rerun()
    st.info("Consulte os documentos gerados.")

# =================================================================
# BLOCO 7: RANCHO RECEBIDO (EXIBIÇÃO DA TABELA + DOWNLOAD)
# =================================================================
elif st.session_state.pagina == "recebido":
    st.markdown("<style>.stApp { background-color: #D3D3D3 !important; }</style>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>📦 Rancho Recebido</h1>", unsafe_allow_html=True) #

    # Verifica se existe a lista do último rancho gerado pelo usuário
    if 'df_ultimo_pedido' in st.session_state and not st.session_state.df_ultimo_pedido.empty:
        st.write("### Conferência do Último Rancho Gerado")
        
        # Layout: Tabela à esquerda (85%) e Botão/Ícone à direita (15%)
        col_tabela, col_download = st.columns([0.85, 0.15])
        
        with col_tabela:
            # Apresenta a lista como uma tabela de consulta
            st.dataframe(st.session_state.df_ultimo_pedido, hide_index=True, use_container_width=True)
        
        with col_download:
            st.markdown("<p style='text-align: center; font-weight: bold;'>PDF</p>", unsafe_allow_html=True)
            if st.session_state.ultimo_pdf:
                # Botão de download com ícone posicionado à direita
                st.download_button(
                    label="📥", 
                    data=st.session_state.ultimo_pdf, 
                    file_name=f"Rancho_{st.session_state.navio}_Conferencia.pdf",
                    key="btn_down_bloco7",
                    use_container_width=True
                )

        st.markdown("---")
        # Campo para o usuário apontar que recebeu conforme a lista
        if st.checkbox("Confirmar recebimento total conforme tabela acima"):
            st.success("✅ Recebimento registrado com sucesso!")
            
    else:
        st.error("❌ Nenhuma lista encontrada. Você precisa gerar um PDF na Tabela de Rancho primeiro.")

    if st.button("⬅️ VOLTAR AO MENU", use_container_width=True):
        st.session_state.pagina = "menu"
        st.rerun()

# --- NOTA TÉCNICA PARA O BLOCO 6 ---
# Para que a tabela apareça aqui no Bloco 7, no Bloco 6 (Lista), 
# quando o usuário clicar em "GERAR PDF", você deve incluir:
# st.session_state.df_ultimo_pedido = df_editado.copy()

# =================================================================
# BLOCO 8 E 9: ESTILOS E RODAPÉ
# =================================================================
if st.session_state.pagina != "home":
    st.markdown("---")
    st.caption(f"Logado: {st.session_state.cozinheiro} | {st.session_state.navio} | © Zion Tecnologia 2026")
