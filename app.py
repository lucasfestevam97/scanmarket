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

# 2. Detector de Código de Barras do OpenCV
barcode_detector = cv2.barcode.BarcodeDetector()

# 3. Inicialização dos Estados do App (Session State)
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = "Visitante"
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"admin": "1234"}

if "ultimo_codigo" not in st.session_state:
    st.session_state.ultimo_codigo = None
if "carrinho" not in st.session_state:
    st.session_state.carrinho = []
if "limite_mensal" not in st.session_state:
    st.session_state.limite_mensal = 500.00
if "gasto_atual" not in st.session_state:
    st.session_state.gasto_atual = 145.80

# 4. Processamento de Vídeo da Câmera
class BarcodeScanner(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        ok, decoded_info, _, corners = barcode_detector.detectAndDecode(img)
        
        if ok and decoded_info:
            for info in decoded_info:
                if info and info != st.session_state.ultimo_codigo:
                    st.session_state.ultimo_codigo = info
                    
        if corners is not None:
            corners = corners.astype(int)
            for corner in corners:
                cv2.polylines(img, [corner], True, (0, 255, 0), 3)
                
        return frame.from_ndarray(img, format="bgr24")

# 5. Estilização CSS Mobile
st.markdown("""
    <style>
    .stApp {
        background-color: #F8F9FA;
        max-width: 480px;
        margin: 0 auto;
        padding-bottom: 90px;
    }
    
    header, footer { visibility: hidden; }

    /* Cards */
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

    .budget-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 12px 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 15px;
        border: 1px solid #E0E0E0;
    }

    /* Bottom Navigation Bar */
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

# 6. Navegação Inferior Principal
tab_scanner, tab_carrinho, tab_historico, tab_perfil = st.tabs(["📷 Escanear", "🛒 Carrinho", "📜 Histórico", "👤 Perfil"])

# --- ABA 1: ESCANEAR ---
with tab_scanner:
    st.title("🛒 Scan Market")
    st.caption(f"Olá, **{st.session_state.usuario_atual}**!")
    
    # BARRA DE LIMITE MENSAL
    porcentagem = min(st.session_state.gasto_atual / st.session_state.limite_mensal, 1.0)
    
    st.markdown('<div class="budget-card">', unsafe_allow_html=True)
    col_txt1, col_txt2 = st.columns(2)
    with col_txt1:
        st.caption("Gasto Mensal")
        st.markdown(f"**R$ {st.session_state.gasto_atual:.2f}**")
    with col_txt2:
        st.caption("Limite Definido")
        st.markdown(f"**R$ {st.session_state.limite_mensal:.2f}**")
    
    st.progress(porcentagem)
    
    if st.session_state.gasto_atual > st.session_state.limite_mensal:
        st.error("⚠️ Você ultrapassou seu limite mensal!")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # CÂMERA DE CÓDIGO DE BARRAS
    webrtc_streamer(
        key="scanner",
        mode=WebRtcMode.SENDRECV,
        video_processor_factory=BarcodeScanner,
        media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
        async_processing=True,
    )
    
    # PRODUTO DETECTADO
    if st.session_state.ultimo_codigo:
        codigo = st.session_state.ultimo_codigo
        
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
        
        if st.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
            st.session_state.carrinho.append({"codigo": codigo, "nome": "Produto Escaneado", "preco": 12.90})
            st.success("Item adicionado ao carrinho!")

# --- ABA 2: CARRINHO ---
with tab_carrinho:
    st.subheader("🛒 Seu Carrinho")
    
    if len(st.session_state.carrinho) == 0:
        st.info("Seu carrinho está vazio.")
    else:
        total_carrinho = sum(item["preco"] for item in st.session_state.carrinho)
        
        for idx, item in enumerate(st.session_state.carrinho):
            st.write(f"**{item['nome']}** — R$ {item['preco']:.2f}")
            st.caption(f"Código: {item['codigo']}")
            st.divider()
            
        st.metric(label="Total da Compra Atual", value=f"R$ {total_carrinho:.2f}")
        
        if st.button("Finalizar Compra", use_container_width=True, type="primary"):
            st.session_state.gasto_atual += total_carrinho
            st.session_state.carrinho = []
            st.success("Compra finalizada e adicionada ao gasto mensal!")

# --- ABA 3: HISTÓRICO ---
with tab_historico:
    st.subheader("📜 Histórico de Compras")
    st.caption("Em breve você verá suas compras passadas detalhadas aqui.")

# --- ABA 4: PERFIL & CONFIGURAÇÕES / LOGIN OPCIONAL ---
with tab_perfil:
    st.subheader("⚙️ Configurações & Conta")
    
    # Ajuste de Limite (Disponível para qualquer um)
    novo_limite = st.number_input(
        "Ajustar Limite Mensal (R$):", 
        min_value=50.0, 
        max_value=10000.0, 
        value=float(st.session_state.limite_mensal),
        step=50.0
    )
    
    if st.button("Salvar Limite", use_container_width=True):
        st.session_state.limite_mensal = novo_limite
        st.success("Novo limite mensal salvo com sucesso!")
        
    st.divider()
    
    # SE JÁ ESTIVER LOGADO
    if st.session_state.logado:
        st.write(f"Conectado como: **{st.session_state.usuario_atual}**")
        if st.button("🔴 Sair da Conta", use_container_width=True):
            st.session_state.logado = False
            st.session_state.usuario_atual = "Visitante"
            st.rerun()
            
    # SE FOR VISITANTE (Login Opcional)
    else:
        st.write("🔒 **Entrar na sua conta (Opcional)**")
        st.caption("Faça login para sincronizar suas compras e salvar seu histórico.")
        
        subtab_login, subtab_cad = st.tabs(["Entrar", "Criar Conta"])
        
        with subtab_login:
            u = st.text_input("Usuário", key="u_login")
            s = st.text_input("Senha", type="password", key="s_login")
            if st.button("Entrar", use_container_width=True, type="primary"):
                if u in st.session_state.usuarios and st.session_state.usuarios[u] == s:
                    st.session_state.logado = True
                    st.session_state.usuario_atual = u
                    st.success(f"Conectado como {u}!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        with subtab_cad:
            nu = st.text_input("Novo Usuário", key="u_cad")
            ns = st.text_input("Nova Senha", type="password", key="s_cad")
            cs = st.text_input("Confirme a Senha", type="password", key="c_cad")
            if st.button("Cadastrar", use_container_width=True):
                if not nu or not ns:
                    st.warning("Preencha todos os campos.")
                elif nu in st.session_state.usuarios:
                    st.error("Usuário já existe.")
                elif ns != cs:
                    st.error("As senhas não coincidem.")
                else:
                    st.session_state.usuarios[nu] = ns
                    st.success("Conta criada com sucesso! Você já pode entrar.")
