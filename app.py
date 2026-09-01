import os
import cv2
import numpy as np
import pandas as pd
import streamlit as st
from pyzbar.pyzbar import decode
from PIL import Image

# Configuração inicial da página Streamlit
st.set_page_config(
    page_title="Scan Market - Leitor",
    page_icon="🛒",
    layout="centered"
)

# ---------------------------------------------------------
# Funções de Processamento de Imagem (OpenCV / PyZbar)
# ---------------------------------------------------------
def rotacionar_imagem(img, angulo):
    if angulo == 90:
        return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
    elif angulo == 180:
        return cv2.rotate(img, cv2.ROTATE_180)
    elif angulo == 270:
        return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return img

def aplicar_filtros(img_gray):
    variacoes = [("Original (Cinza)", img_gray)]
    
    # Zoom 2x
    resized = cv2.resize(img_gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    variacoes.append(("Zoom 2x", resized))
    
    # CLAHE (Contraste Adaptativo)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    variacoes.append(("Contraste CLAHE", clahe.apply(img_gray)))
    
    # Threshold Adaptativo
    thresh = cv2.adaptiveThreshold(
        img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
    )
    variacoes.append(("Threshold Adaptativo", thresh))
    
    # Blur + Otsu
    blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    _, thresh_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    variacoes.append(("Filtro Otsu", thresh_otsu))
    
    return variacoes

def decodificar_com_fallback(file_bytes):
    # Converter bytes da imagem recebida para OpenCV
    np_arr = np.frombuffer(file_bytes, np.uint8)
    img_original = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img_original is None:
        return None, "Erro ao carregar a imagem."

    angulos = [0, 90, 180, 270]
    for angulo in angulos:
        img_rot = rotacionar_imagem(img_original, angulo)
        img_gray = cv2.cvtColor(img_rot, cv2.COLOR_BGR2GRAY)
        
        for nome_filtro, img_proc in aplicar_filtros(img_gray):
            barcodes = decode(img_proc)
            if barcodes:
                res = []
                for b in barcodes:
                    res.append({
                        "codigo": b.data.decode("utf-8"),
                        "tipo": b.type,
                        "angulo": angulo,
                        "filtro": nome_filtro
                    })
                return res, None

    return None, "Nenhum código de barras identificado após tentar todas as rotações e filtros."

# ---------------------------------------------------------
# Interface do Usuário (Streamlit)
# ---------------------------------------------------------
st.title("🛒 Scan Market - Leitor de Código de Barras")

# Leitura de parâmetros repassados pela câmera JS
query_params = st.query_params
if "barcode" in query_params:
    st.success(f"✅ Código lido via Câmera: **{query_params['barcode']}**")

aba_camera, aba_upload = st.tabs(["📷 Câmera (Automática)", "📁 Upload de Imagem"])

# ABA 1: Câmera com Leitura Contínua e Rotação Automática (JS)
with aba_camera:
    st.write("Aponte a câmera para o código de barras. A leitura ocorre automaticamente assim que enquadrado.")
    
    scanner_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://unpkg.com/@zxing/library@latest"></script>
        <style>
            body { margin: 0; background: #000; color: #fff; text-align: center; font-family: sans-serif; }
            #container { position: relative; width: 100%; max-width: 500px; height: 280px; margin: 0 auto; overflow: hidden; border-radius: 10px; border: 2px solid #333; }
            video { width: 100%; height: 100%; object-fit: cover; }
            .line { position: absolute; top: 50%; left: 10%; right: 10%; height: 2px; background: red; box-shadow: 0 0 6px red; z-index: 10; }
            .rotate-msg { display: none; position: fixed; top:0; left:0; right:0; bottom:0; background: rgba(0,0,0,0.9); z-index: 99; color: #fff; padding-top: 20%; font-size: 1.2rem; }
            @media screen and (orientation: portrait) { .rotate-msg { display: block; } }
        </style>
    </head>
    <body>
        <div class="rotate-msg">🔄 Vire o celular na horizontal para alinhar a leitura.</div>
        <div id="container">
            <video id="video"></video>
            <div class="line"></div>
        </div>
        <script>
            const codeReader = new ZXing.BrowserMultiFormatReader();
            codeReader.decodeFromVideoDevice(null, 'video', (result, err) => {
                if (result) {
                    window.parent.location.href = window.parent.location.pathname + '?barcode=' + encodeURIComponent(result.text);
                }
            }).catch(err => console.error(err));
        </script>
    </body>
    </html>
    """
    st.components.v1.html(scanner_html, height=330)

# ABA 2: Upload com Pipeline Completo (OpenCV / PyZbar)
with aba_upload:
    st.write("Envie uma foto da sua galeria/computador caso o código esteja borrado ou em ângulo difícil.")
    
    arquivo = st.file_uploader("Selecione uma imagem", type=["jpg", "jpeg", "png", "webp"])
    
    if arquivo is not None:
        file_bytes = arquivo.read()
        st.image(file_bytes, caption="Imagem Enviada", use_container_width=True)
        
        if st.button("🔍 Processar e Ler Código", type="primary", use_container_width=True):
            with st.spinner("Analisando rotações e aplicando filtros de imagem..."):
                resultados, erro = decodificar_com_fallback(file_bytes)
                
                if resultados:
                    for res in resultados:
                        st.success(f"**Código Encontrado:** `{res['codigo']}`")
                        st.info(f"**Tipo:** {res['tipo']} | **Ajuste de Ângulo:** {res['angulo']}° | **Filtro Aplicado:** {res['filtro']}")
                else:
                    st.error(erro)
