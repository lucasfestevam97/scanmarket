import os
import json
import streamlit as st
import cv2
import numpy as np
import requests
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, WebRtcMode
from streamlit_google_auth import Authenticate

# ==========================================
# 1. Configuração do Streamlit e Secrets Google
# ==========================================
st.set_page_config(
    page_title="Scan Market",
    page_icon="🛒",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Cria dinamicamente o client_secret.json caso as secrets existam
SECRET_PATH = "client_secret.json"
if "google_credentials" in st.secrets:
    credenciais = {
        "web": {
            "client_id": st.secrets["google_credentials"]["client_id"],
            "project_id": st.secrets["google_credentials"]["project_id"],
            "auth_uri": st.secrets["google_credentials"]["auth_uri"],
            "token_uri": st.secrets["google_credentials"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_credentials"]["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["google_credentials"]["client_secret"],
            "redirect_uris": list(st.secrets["google_credentials"]["redirect_uris"])
        }
    }
    with open(SECRET_PATH, "w", encoding="utf-8") as f:
        json.dump(credenciais, f)

REDIRECT_URI = st.secrets["google_credentials"]["redirect_uris"][0] if "google_credentials" in st.secrets else "https://scanmarket-jpkpuzxo5wwmdqnfeyjssk.streamlit.app/"

authenticator = Authenticate(
    secret_credentials_path=SECRET_PATH,
    cookie_name='scanmarket_google_cookie',
    cookie_key='chave_secreta_scanmarket_123',
    cookie_expiry_days=30,
    redirect_uri=REDIRECT_URI
)

# Verifica autenticação existente
try:
    authenticator.check_authenticity()
except Exception:
    pass

# ==========================================
# 2. Cotações e Traduções
# ==========================================
@st.cache_data(ttl=3600)
def obter_cotacoes():
    try:
        url = "https://open.er-api.com/v6/latest/BRL"
        res = requests.get(url, timeout=5).json()
        if res.get("result") == "success":
            rates = res.get("rates", {})
            return {"BRL": 1.0, "USD": rates.get("USD", 0.18), "ARS": rates.get("ARS", 175.0)}
    except Exception:
        pass
    return {"BRL": 1.0, "USD": 0.18, "ARS": 175.0}

cotacoes = obter_cotacoes()

TRADUCOES = {
    "PT": {
        "escanear": "📷 Escanear",
        "carrinho": "🛒 Carrinho",
        "historico": "📜 Histórico",
        "perfil": "👤 Perfil",
        "config": "⚙️ Configurações",
        "saudacao": "Olá",
        "gasto_mensal": "Gasto Mensal",
        "limite_definido": "Limite Definido",
        "alerta_limite": "⚠️ Você ultrapassou seu limite mensal!",
        "apontar_camera": "📷 Aponte a câmera para o código de barras",
        "voltar": "❌ Voltar sem Escanear",
        "abrir_camera": "📷 Abrir Câmera para Escanear",
        "digitar_manual": "⌨️ Digitar Código Manualmente",
        "digitar_placeholder": "Insira o código de barras ou ID do produto...",
        "buscar_codigo": "Buscar Produto",
        "prod_escaneado": "Produto Escaneado",
        "quantidade": "Quantidade:",
        "add_carrinho": "➕ Adicionar ao Carrinho",
        "item_add": "Item(ns) adicionado(s) ao carrinho!",
        "carrinho_vazio": "Seu carrinho está vazio.",
        "total_compra": "Total da Compra",
        "finalizar": "Finalizar Compra",
        "compra_feita": "Compra finalizada com sucesso!",
        "historico_vazio": "Suas compras finalizadas aparecerão listadas aqui.",
        "tema": "Modo Visual",
        "claro": "Claro",
        "escuro": "Escuro",
        "idioma": "Idioma",
        "moeda": "Moeda Principal",
        "limite_label": "Ajustar Limite Mensal:",
        "salvar_limite": "Salvar Limite",
        "login_opcional": "🔒 Acessar Conta",
        "entrar_aba": "Entrar",
        "criar_aba": "Criar Conta",
        "usuario": "Usuário",
        "senha": "Senha",
        "conf_senha": "Confirmar Senha",
        "entrar_btn": "Entrar",
        "cadastrar_btn": "Cadastrar",
        "ou_social": "Ou entre com",
        "sair": "🔴 Sair da Conta",
        "conectado": "Conectado como",
        "limite_salvo": "Novo limite mensal salvo com sucesso!"
    },
    "ES": {
        "escanear": "📷 Escanear",
        "carrinho": "🛒 Carrito",
        "historico": "📜 Historial",
        "perfil": "👤 Perfil",
        "config": "⚙️ Configuración",
        "saudacao": "Hola",
        "gasto_mensal": "Gasto Mensual",
        "limite_definido": "Límite Definido",
        "alerta_limite": "⚠️ ¡Has superado tu límite mensual!",
        "apontar_camera": "📷 Apunta la cámara al código de barras",
        "voltar": "❌ Volver sin Escanear",
        "abrir_camera": "📷 Abrir Cámara para Escanear",
        "digitar_manual": "⌨️ Ingresar Código Manualmente",
        "digitar_placeholder": "Ingrese el código de barras o ID...",
        "buscar_codigo": "Buscar Producto",
        "prod_escaneado": "Producto Escaneado",
        "quantidade": "Cantidad:",
        "add_carrinho": "➕ Añadir al Carrito",
        "item_add": "¡Artículo(s) añadido(s) al carrito!",
        "carrinho_vazio": "Tu carrito está vacío.",
        "total_compra": "Total de la Compra",
        "finalizar": "Finalizar Compra",
        "compra_feita": "¡Compra finalizada con éxito!",
        "historico_vazio": "Tus compras finalizadas aparecerán aquí.",
        "tema": "Modo Visual",
        "claro": "Claro",
        "escuro": "Oscuro",
        "idioma": "Idioma",
        "moeda": "Moneda Principal",
        "limite_label": "Ajustar Límite Mensual:",
        "salvar_limite": "Guardar Límite",
        "login_opcional": "🔒 Acceder a la Cuenta",
        "entrar_aba": "Iniciar Sesión",
        "criar_aba": "Crear Cuenta",
        "usuario": "Usuario",
        "senha": "Contraseña",
        "conf_senha": "Confirmar Contraseña",
        "entrar_btn": "Entrar",
        "cadastrar_btn": "Registrarse",
        "ou_social": "O ingresa con",
        "sair": "🔴 Cerrar Sesión",
        "conectado": "Conectado como",
        "limite_salvo": "¡Nuevo límite mensual guardado!"
    },
    "EN": {
        "escanear": "📷 Scan",
        "carrinho": "🛒 Cart",
        "historico": "📜 History",
        "perfil": "👤 Profile",
        "config": "⚙️ Settings",
        "saudacao": "Hello",
        "gasto_mensal": "Monthly Spending",
        "limite_definido": "Set Limit",
        "alerta_limite": "⚠️ You have exceeded your monthly limit!",
        "apontar_camera": "📷 Point the camera at the barcode",
        "voltar": "❌ Back without Scanning",
        "abrir_camera": "📷 Open Camera to Scan",
        "digitar_manual": "⌨️ Enter Code Manually",
        "digitar_placeholder": "Enter barcode or product ID...",
        "buscar_codigo": "Search Product",
        "prod_escaneado": "Scanned Product",
        "quantidade": "Quantity:",
        "add_carrinho": "➕ Add to Cart",
        "item_add": "Item(s) added to cart!",
        "carrinho_vazio": "Your cart is empty.",
        "total_compra": "Purchase Total",
        "finalizar": "Checkout",
        "compra_feita": "Purchase completed successfully!",
        "historico_vazio": "Your completed purchases will appear here.",
        "tema": "Visual Mode",
        "claro": "Light",
        "escuro": "Dark",
        "idioma": "Language",
        "moeda": "Main Currency",
        "limite_label": "Adjust Monthly Limit:",
        "salvar_limite": "Save Limit",
        "login_opcional": "🔒 Account Access",
        "entrar_aba": "Login",
        "criar_aba": "Sign Up",
        "usuario": "Username",
        "senha": "Password",
        "conf_senha": "Confirm Password",
        "entrar_btn": "Log In",
        "cadastrar_btn": "Sign Up",
        "ou_social": "Or continue with",
        "sair": "🔴 Log Out",
        "conectado": "Connected as",
        "limite_salvo": "New monthly limit saved successfully!"
    }
}

SIMBOLOS = {"BRL": "R$", "USD": "$", "ARS": "$"}

# ==========================================
# 3. Processador de Vídeo OpenCV
# ==========================================
barcode_detector = cv2.barcode.BarcodeDetector()

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
        return frame.from_ndarray(img, format="bgr24")

# ==========================================
# 4. Estados da Sessão
# ==========================================
if "logado" not in st.session_state:
    st.session_state.logado = False
if "usuario_atual" not in st.session_state:
    st.session_state.usuario_atual = "Visitante"
if "usuarios" not in st.session_state:
    st.session_state.usuarios = {"admin": "1234"}

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

def fmt_moeda(valor_brl):
    m = st.session_state.moeda
    taxa = cotacoes.get(m, 1.0)
    simbolo = SIMBOLOS.get(m, "$")
    return f"{simbolo} {valor_brl * taxa:,.2f}"

t = TRADUCOES[st.session_state.idioma]

if st.session_state.get("connected"):
    user_info = st.session_state.get("user_info", {})
    st.session_state.usuario_atual = user_info.get("name", user_info.get("email", "Usuário Google"))
    st.session_state.logado = True

# ==========================================
# 5. Estilização CSS com Alinhamento Horizontal nas Abas
# ==========================================
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
    .price-tag {{ font-size: 1.6rem; font-weight: 800; color: #2E7D32; margin: 4px 0; }}

    /* Estilização da Navegação Inferior (Bottom Nav Bar) */
    div[data-baseweb="tab-list"] {{
        position: fixed;
        bottom: 0; left: 50%;
        transform: translateX(-50%);
        width: 100%; max-width: 480px;
        background-color: {card_bg};
        z-index: 99999;
        display: flex; 
        justify-content: space-around;
        padding: 8px 0;
        border-top: 1px solid {border_color};
        box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
    }}
    
    /* Força o alinhamento horizontal (ícone ao lado do texto) */
    div[data-baseweb="tab"] {{
        flex-grow: 1;
        text-align: center;
        padding: 6px 0;
        font-size: 0.85rem;
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
    }}
    
    /* Garante alinhamento inline dos nós internos de texto/ícone */
    div[data-baseweb="tab"] > div {{
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 4px !important;
    }}
    </style>
""", unsafe_allow_html=True)

def reproduzir_bip():
    sound_js = """<audio autoplay><source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg"></audio>"""
    st.components.v1.html(sound_js, height=0)

# ==========================================
# 6. Abas Inferiores
# ==========================================
tab_scanner, tab_carrinho, tab_historico, tab_perfil, tab_config = st.tabs([
    t["escanear"], 
    t["carrinho"], 
    t["historico"], 
    t["perfil"], 
    t["config"]
])

# --- ABA 1: ESCANEAR / DADOS MANUAIS ---
with tab_scanner:
    st.title("🛒 Scan Market")
    st.caption(f"{t['saudacao']}, **{st.session_state.usuario_atual}**!")
    
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

    if st.session_state.abrir_camera:
        st.subheader(t["apontar_camera"])
        
        webrtc_streamer(
            key="scanner",
            mode=WebRtcMode.SENDRECV,
            video_processor_factory=BarcodeScanner,
            media_stream_constraints={"video": {"facingMode": "environment"}, "audio": False},
            async_processing=True,
        )
        
        if st.button(t["voltar"], width="stretch"):
            st.session_state.abrir_camera = False
            st.rerun()
    else:
        if st.button(t["abrir_camera"], width="stretch", type="primary"):
            st.session_state.abrir_camera = True
            st.rerun()

        st.divider()

        # Opção de Inserção Manual de Código de Barras
        with st.expander(t["digitar_manual"], expanded=False):
            codigo_manual = st.text_input(t["digitar_placeholder"], key="input_manual")
            if st.button(t["buscar_codigo"], width="stretch"):
                if codigo_manual.strip():
                    st.session_state.ultimo_codigo = codigo_manual.strip()
                    st.rerun()
                else:
                    st.warning("Por favor, digite um código válido.")

        if st.session_state.ultimo_codigo:
            codigo = st.session_state.ultimo_codigo
            preco_base_brl = 12.90
            
            st.markdown('<div class="product-card">', unsafe_allow_html=True)
            col_img, col_info = st.columns([1, 2])
            with col_img:
                st.image("https://images.unsplash.com/photo-1588964895597-cfccd6e2dbf9?w=300", width="stretch")
            with col_info:
                st.markdown(f"<h4 style='margin:0;'>{t['prod_escaneado']}</h4>", unsafe_allow_html=True)
                st.markdown(f"<div class='price-tag'>{fmt_moeda(preco_base_brl)}</div>", unsafe_allow_html=True)
                st.caption(f"Cód: {codigo}")
                
            qtd = st.number_input(t["quantidade"], min_value=1, max_value=99, value=1, step=1)
            st.markdown('</div>', unsafe_allow_html=True)
            
            if st.button(t["add_carrinho"], width="stretch", type="primary"):
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
                st.write(f"**{item['quantidade']}x {item['nome']}** — {fmt_moeda(item['preco_brl'] * item['quantidade'])}")
                st.caption(f"Cód: {item['codigo']}")
            with col_btn:
                if st.button("🗑️", key=f"del_{idx}"):
                    st.session_state.carrinho.pop(idx)
                    st.rerun()
            st.divider()
            
        st.metric(label=t["total_compra"], value=fmt_moeda(total_brl))
        
        if st.button(t["finalizar"], width="stretch", type="primary"):
            st.session_state.gasto_atual_brl += total_brl
            st.session_state.carrinho = []
            st.success(t["compra_feita"])
            st.rerun()

# --- ABA 3: HISTÓRICO ---
with tab_historico:
    st.subheader(t["historico"])
    st.caption(t["historico_vazio"])

# --- ABA 4: PERFIL ---
with tab_perfil:
    st.subheader(t["perfil"])
    
    if st.session_state.get("connected"):
        user_info = st.session_state.get("user_info", {})
        col_pic, col_details = st.columns([1, 3])
        with col_pic:
            if "picture" in user_info:
                st.image(user_info["picture"], width=70)
        with col_details:
            st.markdown(f"**{user_info.get('name', 'Usuário')}**")
            st.caption(user_info.get('email', ''))

        st.divider()
        if st.button(t["sair"], width="stretch"):
            authenticator.logout()
            st.rerun()

    elif st.session_state.logado:
        st.write(f"{t['conectado']}: **{st.session_state.usuario_atual}**")
        if st.button(t["sair"], width="stretch"):
            st.session_state.logado = False
            st.session_state.usuario_atual = "Visitante"
            st.rerun()

    else:
        st.write(f"**{t['login_opcional']}**")
        
        st.write(f"**{t['ou_social']}**")
        try:
            authenticator.login()
        except Exception:
            st.info("Login social temporariamente indisponível. Use o acesso por usuário abaixo.")
            
        st.divider()
        
        sub_entrar, sub_criar = st.tabs([t["entrar_aba"], t["criar_aba"]])
        
        with sub_entrar:
            u = st.text_input(t["usuario"], key="u_login")
            s = st.text_input(t["senha"], type="password", key="s_login")
            if st.button(t["entrar_btn"], width="stretch", type="primary"):
                if u in st.session_state.usuarios and st.session_state.usuarios[u] == s:
                    st.session_state.logado = True
                    st.session_state.usuario_atual = u
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")
                    
        with sub_criar:
            nu = st.text_input(t["usuario"], key="u_cad")
            ns = st.text_input(t["senha"], type="password", key="s_cad")
            cs = st.text_input(t["conf_senha"], type="password", key="c_cad")
            
            if st.button(t["cadastrar_btn"], width="stretch", type="primary"):
                if not nu or not ns:
                    st.warning("Preencha todos os campos.")
                elif nu in st.session_state.usuarios:
                    st.error("Usuário já existe.")
                elif ns != cs:
                    st.error("As senhas não coincidem.")
                else:
                    st.session_state.usuarios[nu] = ns
                    st.success("Conta criada com sucesso! Faça login para continuar.")

# --- ABA 5: CONFIGURAÇÕES ---
with tab_config:
    st.subheader(t["config"])
    
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
    
    novo_limite = st.number_input(
        t["limite_label"], 
        min_value=10.0, 
        max_value=100000.0, 
        value=float(st.session_state.limite_mensal_brl),
        step=50.0
    )
    if st.button(t["salvar_limite"], width="stretch"):
        st.session_state.limite_mensal_brl = novo_limite
        st.success(t["limite_salvo"])
        st.rerun()
