import streamlit as st
import cv2
import numpy as np
import requests
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode

# 1. Configuração Mobile da Página
st.set_page_config(
    page_title="Scan Market",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 2. Busca Cotação Diária das Moedas em Relação ao BRL (API Externa)
@st.cache_data(ttl=3600)  # Atualiza a cotação a cada 1 hora
def obter_cotacoes():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        res = requests.get(url, timeout=5).json()
        if res.get("result") == "success":
            rates = res.get("rates", {})
            return {
                "BRL": 1.0,
                "USD": rates.get("USD", 0.18),
                "ARS": rates.get("ARS", 175.0)
            }
    except Exception:
        pass
    # Valores de fallback em caso de falha de conexão
    return {"BRL": 1.0, "USD": 0.18, "ARS": 175.0}

cotacoes = obter_cotacoes()

# 3. Dicionário de Idiomas
TRADUCOES = {
    "PT": {
        "escanear": "📷 Escanear",
        "carrinho": "🛒 Carrinho",
        "historico": "📜 Histórico",
        "perfil": "👤 Perfil",
        "config": "⚙️ Configurações",
        "gasto_mensal": "Gasto Mensal",
        "limite_definido": "Limite Definido",
        "alerta_limite": "⚠️ Você ultrapassou seu limite mensal!",
        "apontar_camera": "📷 Aponte a câmera para o código de barras",
        "voltar": "❌ Voltar sem Escanear",
        "abrir_camera": "📷 Abrir Câmera para Escanear",
        "prod_escaneado": "Produto Escaneado",
        "quantidade": "Quantidade:",
        "add_carrinho": "➕ Adicionar ao Carrinho",
        "item_add": "Item(ns) adicionado(s) ao carrinho!",
        "carrinho_vazio": "Seu carrinho está vazio.",
        "total_compra": "Total da Compra",
        "finalizar": "Finalizar Compra",
        "compra_feita": "Compra finalizada com sucesso!",
        "tema": "Modo Visual",
        "claro": "Claro",
        "escuro": "Escuro",
        "idioma": "Idioma",
        "moeda": "Moeda Principal",
        "limite_label": "Ajustar Limite Mensal:",
        "salvar_limite": "Salvar Limite",
        "login_opcional": "🔒 Login (Opcional)",
        "usuario": "Usuário",
        "senha": "Senha",
        "entrar": "Entrar",
        "sair": "🔴 Sair da Conta",
        "conectado": "Conectado como"
    },
    "ES": {
        "escanear": "📷 Escanear",
        "carrinho": "🛒 Carrito",
        "historico": "📜 Historial",
        "perfil": "👤 Perfil",
        "config": "⚙️ Configuración",
        "gasto_mensal": "Gasto Mensual",
        "limite_definido": "Límite Definido",
        "alerta_limite": "⚠️ ¡Has superado tu límite mensual!",
        "apontar_camera": "📷 Apunta la cámara al código de barras",
        "voltar": "❌ Volver sin Escanear",
        "abrir_camera": "📷 Abrir Cámara para Escanear",
        "prod_escaneado": "Producto Escaneado",
        "quantidade": "Cantidad:",
        "add_carrinho": "➕ Añadir al Carrito",
        "item_add": "¡Artículo(s) añadido(s) al carrito!",
        "carrinho_vazio": "Tu carrito está vacío.",
        "total_compra": "Total de la Compra",
        "finalizar": "Finalizar Compra",
        "compra_feita": "¡Compra finalizada con éxito!",
        "tema": "Modo Visual",
        "claro": "Claro",
        "escuro": "Oscuro",
        "idioma": "Idioma",
        "moeda": "Moneda Principal",
        "limite_label": "Ajustar Límite Mensual:",
        "salvar_limite": "Guardar Límite",
        "login_opcional": "🔒 Iniciar Sesión (Opcional)",
        "usuario": "Usuario",
        "senha": "Contraseña",
        "entrar": "Entrar",
        "sair": "🔴 Cerrar Sesión",
        "conectado": "Conectado como"
    },
    "EN": {
        "escanear": "📷 Scan",
        "carrinho": "🛒 Cart",
        "historico": "📜 History",
        "perfil": "👤 Profile",
        "config": "⚙️ Settings",
        "gasto_mensal": "Monthly Spending",
        "limite_definido": "Set Limit",
        "alerta_limite": "⚠️ You have exceeded your monthly limit!",
        "apontar_camera": "📷 Point the camera at the barcode",
        "voltar": "❌ Back without Scanning",
        "abrir_camera": "📷 Open Camera to Scan",
        "prod_escaneado": "Scanned Product",
        "quantidade": "Quantity:",
        "add_carrinho": "➕ Add to Cart",
        "item_add": "Item(s) added to cart!",
        "carrinho_vazio": "Your cart is empty.",
        "total_compra": "Purchase Total",
        "finalizar": "Checkout",
        "compra_feita": "Purchase completed successfully!",
        "tema": "Visual Mode",
        "claro": "Light",
        "escuro": "Dark",
        "idioma": "Language",
        "moeda": "Main Currency",
        "limite_label": "Adjust Monthly Limit:",
        "salvar_limite": "Save Limit",
        "login_opcional": "🔒 Login (Optional)",
        "usuario": "Username",
        "senha": "Password",
        "entrar": "Login",
        "sair": "🔴 Log Out",
        "conectado": "Connected as"
    }
}

# Símbolos das moedas
SIMBOLOS = {"BRL": "R$", "USD": "$", "ARS": "$"}

# 4. Detector de Código de Barras do OpenCV
barcode_detector = cv2.barcode.BarcodeDetector()

# 5. Inicialização dos Estados do App (Session State)
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = "Visitante"
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"admin": "1234"}

# Preferências
if "tema" not in st.session_state:
    st.session_state.tema = "Claro"
if "idioma" not in st.session_state:
    st.session_state.idioma = "PT"
if "moeda" not in st.session_state:
    st.session_state.moeda = "BRL"

if "ultimo_codigo" not in st.session_state:
    st.session_state.ultimo_codigo = None
if "abrir_camera" not in st.session_state:
    st.session_state.abrir_camera = False
if "tocar_som" not in st.session_state:
    st.session_state.tocar_som = False

if "carrinho" not in st.session_state:
    st.session_state.carrinho = []
if "limite_mensal_brl" not in st.session_state:
    st.session_state.limite_mensal_brl = 500.00
if "gasto_atual_brl" not in st.session_state:
    st.session_state.gasto_atual_brl = 145.80

# Função Auxiliar de Formatação de Valor
def fmt_moeda(valor_brl):
    m = st.session_state.moeda
    taxa = cotacoes.get(m, 1.0)
    simbolo = SIMBOLOS.get(m, "$")
    valor_convertido = valor_brl * taxa
    return f"{simbolo} {valor_convertido:,.2f}"

t = TRADUCOES[st.session_state.idioma]

# 6. Processamento de Vídeo
class BarcodeScanner(VideoProcessorBase):
    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        ok, decoded_info, _, corners = barcode_detector.detectAndDecode(img)
        
        if ok and decoded_info:
            for info in decoded_info:
                if info and info != st.session_state.ultimo_codigo:
                    st.session_state.ultimo_codigo = info
                    st.session_state.abrir_camera = False
                    st.session_state.tocar_som = True
                    
        if corners is not None:
            corners = corners.astype(int)
            for corner in corners:
                cv2.polylines(img, [corner], True, (0, 255, 0), 3)
                
        return frame.from_ndarray(img, format="bgr24")

# 7. Estilização CSS Dinâmica (Modo Claro vs Modo Escuro)
is_dark = st.session_state.tema == "Escuro"

bg_color = "#121212" if is_dark else "#F8F9FA"
card_bg = "#1E1E1E" if is_dark else "#FFFFFF"
text_color = "#E0E0E0" if is_dark else "#212529"
border_color = "#333333" if is_dark else "#E0E0E0"

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {bg_color};
        color: {text_color};
        max-width: 480px;
        margin: 0 auto;
        padding-bottom: 90px;
    }}
    
    header, footer {{ visibility: hidden; }}

    .product-card, .budget-card {{
        background-color: {card_bg};
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid {border_color};
        margin-top: 10px;
        margin-bottom: 15px;
    }}
    
    .price-tag {{
        font-size: 1.6rem;
        font-weight: 800;
        color: #2E7D32;
        margin: 4px 0;
    }}

    /* Bottom Bar Fixa */
    div[data-baseweb="tab-list"] {{
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 100%;
        max-width: 480px;
        background-color: {card_bg};
        box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
        z-index: 99999;
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        border-top: 1px solid {border_color};
    }}

    div[data-baseweb="tab"] {{
        flex-grow: 1;
        text-align: center;
    }}
    </style>
""", unsafe_allow_html=True)

# Som Bip
def reproduzir_bip():
    sound_js = """
    <audio autoplay>
        <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    st.components.v1.html(sound_js, height=0)

# 8. Navegação Por Abas Inferiores
tab_scanner, tab_carrinho, tab_historico, tab_perfil, tab_config = st.tabs([
    t["escanear"], t["carrinho"], t["historico"], t["perfil"], t["config"]
])

# --- ABA 1: ESCANEAR ---
with tab_scanner:
    st.title("🛒 Scan Market")
    st.caption(f"Olá, **{st.session_state.usuario_atual}**!")
    
    # Barra de Limite Mensal
    porcentagem = min(st.session_state.gasto_atual_brl / st.session_state.limite_mensal_brl, 1.0)
    st.markdown('<div class="budget-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.caption(t["gasto_mensal"])
        st.markdown(f"**{fmt_moeda(st.session_state.gasto_atual_brl)}**")
    with c2:
        st.caption(t["limite_definido"])
        st.markdown(f"**{fmt_moeda(st.session_state.limite_mensal_brl)}**")
    st.progress(porcentagem)
    
    if st.session_state.gasto_atual_brl > st.session_state.limite_mensal_brl:
        st.error(t["alerta_limite"])
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.tocar_som:
        reproduzir_bip()
        st.session_state.tocar_som = False

    # Leitor / Menu
    if st.session_state.abrir_camera:
        st.subheader(t["apontar_camera"])
        webrtc_streamer(
            key="scanner",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=BarcodeScanner,
            media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
            async_processing=True,
        )
        if st.button(t["voltar"], use_container_width=True):
            st.session_state.abrir_camera = False
            st.rerun()
    else:
        if st.button(t["abrir_camera"], use_container_width=True, type="primary"):
            st.session_state.abrir_camera = True
            st.rerun()

        if st.session_state.ultimo_codigo:
            codigo = st.session_state.ultimo_codigo
            preco_base_brl = 12.90
            
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            col_img, col_info = st.columns([1, 2])
            with col_img:
                st.image("https://images.unsplash.com/photo-1588964895597-cfccd6e2dbf9?w=300", use_container_width=True)
            with col_info:
                st.markdown(f"<h4 style='margin:0;'>{t['prod_escaneado']}</h4>", unsafe_allow_html=True)
                st.markdown(f"<div class='price-tag'>{fmt_moeda(preco_base_brl)}</div>", unsafe_allow_html=True)
                st.caption(f"Cód: {codigo}")
                
            qtd = st.number_input(t["quantidade"], min_value=1, max_value=99, value=1, step=1)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button(t["add_carrinho"], use_container_width=True, type="primary"):
                st.session_state.carrinho.append({
                    "codigo": codigo,
                    "nome": t["prod_escaneado"],
                    "preco_brl": preco_base_brl,
                    "quantidade": qtd
                })
                st.session_state.ultimo_codigo = None
                st.success(t["item_add"])
                st.rerun()

# --- ABA 2: CARRINHO ---
with tab_carrinho:
    st.subheader(t["carrinho"])
    
    if len(st.session_state.carrinho) == 0:
        st.info(t["carrinho_vazio"])
    else:
        total_brl = sum(item["preco_brl"] * item["quantidade"] for item in st.session_state.carrinho)
        
        for idx, item in enumerate(st.session_state.carrinho):
            col_item, col_btn = st.columns([3, 1])
            with col_item:
                subtotal = item["preco_brl"] * item["quantidade"]
                st.write(f"**{item['quantidade']}x {item['nome']}** — {fmt_moeda(subtotal)}")
                st.caption(f"Cód: {item['codigo']}")
            with col_btn:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.carrinho.pop(idx)
                    st.rerun()
            st.divider()
            
        st.metric(label=t["total_compra"], value=fmt_moeda(total_brl))
        
        if st.button(t["finalizar"], use_container_width=True, type="primary"):
            st.session_state.gasto_atual_brl += total_brl
            st.session_state.carrinho = []
            st.success(t["compra_feita"])
            st.rerun()

# --- ABA 3: HISTÓRICO ---
with tab_historico:
    st.subheader(t["historico"])
    st.caption("Suas compras finalizadas aparecerão listadas aqui.")

# --- ABA 4: PERFIL ---
with tab_perfil:
    st.subheader(t["perfil"])
    
    if st.session_state.logado:
        st.write(f"{t['conectado']}: **{st.session_state.usuario_atual}**")
        if st.button(t["sair"], use_container_width=True):
            st.session_state.logado = False
            st.session_state.usuario_atual = "Visitante"
            st.rerun()
    else:
        st.write(f"**{t['login_opcional']}**")
        u = st.text_input(t["usuario"], key="u_login")
        s = st.text_input(t["senha"], type="password", key="s_login")
        if st.button(t["entrar"], use_container_width=True, type="primary"):
            if u in st.session_state.usuarios and st.session_state.usuarios[u] == s:
                st.session_state.logado = True
                st.session_state.usuario_atual = u
                st.rerun()
            else:
                st.error("Erro ao conectar.")

# --- ABA 5: CONFIGURAÇÕES (Nova Aba) ---
with tab_config:
    st.subheader(t["config"])
    
    # Modo Claro / Escuro
    tema_sel = st.radio(
        t["tema"], 
        options=["Claro", "Escuro"], 
        index=0 if st.session_state.tema == "Claro" else 1,
        horizontal=True
    )
    if tema_sel != st.session_state.tema:
        st.session_state.tema = tema_sel
        st.rerun()
        
    st.divider()
    
    # Seleção de Idioma
    idioma_sel = st.selectbox(
        t["idioma"], 
        options=["PT", "ES", "EN"], 
        format_func=lambda x: {"PT": "Português 🇧🇷", "ES": "Español 🇪🇸", "EN": "English 🇺🇸"}[x],
        index=["PT", "ES", "EN"].index(st.session_state.idioma)
    )
    if idioma_sel != st.session_state.idioma:
        st.session_state.idioma = idioma_sel
        st.rerun()

    st.divider()

    # Seleção de Moeda
    moeda_sel = st.selectbox(
        t["moeda"], 
        options=["BRL", "USD", "ARS"], 
        format_func=lambda x: {"BRL": "Real (BRL - R$)", "USD": "Dólar (USD - $)", "ARS": "Peso Argentino (ARS - $)"}[x],
        index=["BRL", "USD", "ARS"].index(st.session_state.moeda)
    )
    if moeda_sel != st.session_state.moeda:
        st.session_state.moeda = moeda_sel
        st.rerun()
        
    st.divider()
    
    # Ajustar Limite Mensal
    novo_limite = st.number_input(
        t["limite_label"], 
        min_value=10.0, 
        max_value=100000.0, 
        value=float(st.session_state.limite_mensal_brl),
        step=50.0
    )
    if st.button(t["salvar_limite"], use_container_width=True):
        st.session_state.limite_mensal_brl = novo_limite
        st.success("OK!")
