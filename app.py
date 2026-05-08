import streamlit as st
import pandas as pd
from streamlit_drawable_canvas import st_canvas
import unicodedata
from fpdf import FPDF
import requests
import io
from datetime import datetime
import pytz  # Necessário para o fuso horário do Brasil

# --- CONFIGURAÇÃO PWA ---
st.markdown("""
    <head>
        <link rel="manifest" href="https://raw.githubusercontent.com/alexcostasilva2810-create/Rancho-Zion/main/manifest.json?v=100">
        <meta name="mobile-web-app-capable" content="yes">
    </head>
    """, unsafe_allow_html=True)

# =================================================================
# BLOCO 1 A 3 (ESTADOS, SUPORTE E LOGIN) - MANTIDOS
# =================================================================
# [O código anterior de login e menu permanece igual]

# =================================================================
# BLOCO 4: TABELA DE CONFERÊNCIA COM RODAPÉ DE DATA/HORA
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

    excedeu = (df_editado["CONFIRMA"] > df_editado["PREDEFINIDO"]).any()
    if excedeu:
        st.markdown("<p style='color: red; font-weight: bold; font-size: 20px; text-align: center;'>O limite foi excedido você não pode continuar</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    col_pdf, col_excel, col_btn_menu = st.columns([1,1,1])

    with col_btn_menu:
        if st.button("⬅️ MENU", use_container_width=True):
            st.session_state.pagina = "menu"
            st.rerun()

    if not excedeu:
        # [Código do Excel permanece igual]

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

                    # NOVO MÉTODO PARA A BORDA INFERIOR (RODAPÉ)
                    def footer(self):
                        self.set_y(-15) # Posiciona a 1.5 cm do fim da página
                        self.set_font("Arial", "I", 8)
                        # Obtém data e hora de Brasília
                        fuso_br = pytz.timezone('America/Sao_Paulo')
                        agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")
                        texto_rodape = f"Gerado em: {agora_br} | Página {self.page_no()}"
                        self.cell(0, 10, preparar(texto_rodape), 0, 0, "C")

                pdf = PDF_Checklist()
                pdf.set_auto_page_break(auto=True, margin=20) # Garante espaço para o rodapé
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
# BLOCO 5 A 9 (TRIPULAÇÃO, HISTÓRICO, ETC) - MANTIDOS
# =================================================================
