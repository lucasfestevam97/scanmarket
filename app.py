import streamlit as st
import pandas as pd
import cv2
import numpy as np
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode

# Inicializa o detector de código de barras nativo do OpenCV
barcode_detector = cv2.barcode.BarcodeDetector()

# ---------------------------------------------------------
# 1. Configuração da Página
# ---------------------------------------------------------
st.set_page_config(page_title="Scan Market", page_icon="🛒", layout="wide")

# ---------------------------------------------------------
# 2. Carregar Banco de Dados Excel
# ---------------------------------------------------------
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_excel('banco_de_dados_app.xlsx')
        df['Código de Barras'] = df['Código de Barras'].astype(str).str.strip()
        return df
    except Exception as e:
        return pd.DataFrame(columns=["Nome", "Preço (R$)", "Código de Barras"])

df_produtos = carregar_dados()

# ---------------------------------------------------------
# 3. Estado da Sessão
# ---------------------------------------------------------
if 'carrinho' not in st.session_state:
    st.session_state.carrinho = []
if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'limite_mensal' not in st.session_state:
    st.session_state.limite_mensal = 1000.00
if 'codigo_lido_camera' not in st.session_state:
    st.session_state.codigo_lido_camera = None

# ---------------------------------------------------------
# 4. Leitor de Câmera
# ---------------------------------------------------------
class BarcodeScanner(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        ok, decoded_info, _, corners = barcode_detector.detectAndDecode(img)
        if ok and decoded_info:
            for info in decoded_info:
                if info:
                    st.session_state.codigo_lido_camera = info
        if corners is not None:
            corners = corners.astype(int)
            for corner in corners:
                cv2.polylines(img, [corner], True, (0, 255, 0), 3)
        return img

# ---------------------------------------------------------
# 5. Painel Lateral e Orçamento
# ---------------------------------------------------------
with st.sidebar:
    st.title("🛒 Scan Market")
    st.subheader("💰 Limite Mensal")
    st.session_state.limite_mensal = st.number_input("Limite (R$):", min_value=50.0, value=st.session_state.limite_mensal, step=50.0)

total_gasto_acumulado = sum(c['Total'] for c in st.session_state.historico)
percentual_gasto = min(total_gasto_acumulado / st.session_state.limite_mensal, 1.0) if st.session_state.limite_mensal > 0 else 0.0

st.title("🛒 Scan Market")
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Gasto Acumulado", f"R$ {total_gasto_acumulado:.2f}")
col_m2.metric("Saldo Restante", f"R$ {(st.session_state.limite_mensal - total_gasto_acumulado):.2f}")
col_m3.metric("Limite Mensal", f"R$ {st.session_state.limite_mensal:.2f}")

st.progress(percentual_gasto)

# ---------------------------------------------------------
# 6. Abas Compras / Histórico
# ---------------------------------------------------------
tab_compras, tab_historico = st.tabs(["🛒 Compras", "📜 Histórico"])

with tab_compras:
    c_esq, c_dir = st.columns([1, 1])
    with c_esq:
        st.subheader("📸 Leitor")
        webrtc_streamer(key="scanner", mode=WebRtcMode.SENDRECV, video_transformer_factory=BarcodeScanner, media_stream_constraints={"video": True, "audio": False})
        
        codigo = st.session_state.codigo_lido_camera or st.text_input("Código Manual:")
        if codigo:
            prod = df_produtos[df_produtos['Código de Barras'] == str(codigo)]
            if not prod.empty:
                nome = prod.iloc[0]['Nome']
                preco = float(prod.iloc[0]['Preço (R$)'])
                qtd = st.number_input("Qtd:", min_value=1, value=1)
                if st.button("➕ Adicionar"):
                    st.session_state.carrinho.append({"Nome": nome, "Preço Un.": preco, "Qtd": qtd, "Total": preco * qtd})
                    st.session_state.codigo_lido_camera = None
                    st.rerun()

    with c_dir:
        st.subheader("🛍️ Carrinho")
        total_carrinho = sum(i['Total'] for i in st.session_state.carrinho)
        for i in st.session_state.carrinho:
            st.write(f"**{i['Nome']}** - {i['Qtd']}x R$ {i['Preço Un.']:.2f} = R$ {i['Total']:.2f}")
        st.write(f"### Total: R$ {total_carrinho:.2f}")
        if st.button("💳 Finalizar Compra") and st.session_state.carrinho:
            st.session_state.historico.append({"Data": datetime.now().strftime("%d/%m/%Y %H:%M"), "Total": total_carrinho})
            st.session_state.carrinho = []
            st.rerun()

with tab_historico:
    st.subheader("📜 Histórico")
    if st.session_state.historico:
        st.dataframe(pd.DataFrame(st.session_state.historico))