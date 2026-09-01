import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode

# 1. Configuração Mobile da Página
st.set_page_config(
    page_title="Scan Market",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Inicializa o detector de código de barras do OpenCV
barcode_detector = cv2.barcode.BarcodeDetector()

# 3. Estado do App (Session State) para guardar dados escaneados e carrinho
if "ultimo_codigo" not in st.session_state:
    st.session_state.ultimo_codigo = None
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []

# 4. Classe da Câmera (Processamento de Vídeo em Tempo Real)
class BarcodeScanner(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        ok, decoded_info, _, corners = barcode_detector.detectAndDecode(img)
        
        if ok and decoded_info:
            for info in decoded_info:
                if info and info != st.session_state.ultimo_codigo:
                    st.session_state.ultimo_codigo = info
                    
        # Desenha contorno verde no código quando detectado
        if corners is not None:
            corners = corners.astype(int)
            for corner in corners:
                cv2.polylines(img, [corner], True, (0, 255, 0), 3)
                
        return frame.from_ndarray(img, format="bgr24")

# 5. Estilização CSS Mobile (Interface + Abas Inferiores)
st.markdown("""
    <style>
    /* Estilo Geral da Tela */
    .stApp {
        background-color: #F8F9FA;
        max-width: 480px;
        margin: 0 auto;
        padding-bottom: 90px;
    }
    
    /* Oculta headers padrões */
    header, footer { visibility: hidden; }

    /* Card do Produto Escaneado */
    .product-card {
        background-color: #FFFFFF;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid #E9ECEF;
        margin-top: 10px;
        margin-bottom: 15px;
    }
    
    .price-tag {
        font-size: 1.6rem;
        font-weight: 800;
        color: #2E7D32;
        margin: 4px 0;
    }

    .market-badge {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
    }

    /* Transforma st.tabs em Navegação Inferior (Bottom Bar) */
    div[data-baseweb="tab-list"] {
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 480px;
        background-color: #FFFFFF;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 99999;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        border-top: 1px solid #E0E0E0;
    }

    div[data-baseweb="tab"] {
        flex-grow: 1;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# 6. Abas Principais no Rodapé
tab_scanner, tab_carrinho, tab_historico = st.tabs(["📷 Escanear", "🛒 Carrinho", "📜 Histórico"])

# --- ABA 1: ESCANEAR ---
with tab_scanner:
    st.title("🛒 Scan Market")
    
    # Câmera WebRTC
    webrtc_streamer(
        key="scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeScanner,
        media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
        async_processing=True,
    )
    
    # Se algum código foi lido pela câmera
    if st.session_state.ultimo_codigo:
        codigo = st.session_state.ultimo_codigo
        
        # Card com foto genérica e informações simuladas
        st.markdown('<div class="product-card">', unsafe_allow_html=True)
        col_img, col_info = st.columns([1, 2])
        
        with col_img:
            st.image(
                "https://images.unsplash.com/photo-1588964895597-cfccd6e2dbf9?w=300", 
                use_container_width=True
            )
            
        with col_info:
            st.markdown('<span class="market-badge">Supermercado Silva</span>', unsafe_allow_html=True)
            st.markdown("<h4 style='margin: 4px 0 0 0;'>Produto Escaneado</h4>", unsafe_allow_html=True)
            st.markdown("<div class='price-tag'>R$ 12,90</div>", unsafe_allow_html=True)
            st.caption(f"Cód: {codigo}")
            
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Botão para adicionar ao carrinho
        if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
            st.session_state.carrinho.append({"codigo": codigo, "nome": "Produto Escaneado", "preco": 12.90})
            st.success("Item adicionado ao carrinho!")

# --- ABA 2: CARRINHO ---
with tab_carrinho:
    st.subheader("🛒 Seu Carrinho")
    
    if len(st.session_state.carrinho) == 0:
        st.info("Seu carrinho está vazio.")
    else:
        total = sum(item["preco"] for item in st.session_state.carrinho)
        
        for idx, item in enumerate(st.session_state.carrinho):
            st.write(f"**{item['nome']}** — R$ {item['preco']:.2f}")
            st.caption(f"Código: {item['codigo']}")
            st.divider()
            
        st.metric(label="Total do Pedido", value=f"R$ {total:.2f}")
        st.button("Finalizar Compra", use_container_width=True, type="primary")

# --- ABA 3: HISTÓRICO ---
with tab_historico:
    st.subheader("📜 Histórico")
    st.caption("Em breve você verá suas compras passadas aqui.")
