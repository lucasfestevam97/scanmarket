import os
import json
import datetime
import streamlit as st
import cv2
import numpy as np
import requests
import pandas as pd
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
        "compras": "🛍️ Compras",
        "perfil": "👤 Perfil",
        "config": "⚙️ Configurações",
        "saudacao": "Olá",
        "gasto_mensal": "Gasto no Período",
        "limite_definido": "Limite Definido",
        "alerta_limite": "⚠️ Você ultrapassou seu limite!",
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
        "carrinho_secao": "🛒 Carrinho de Compras",
        "carrinho_vazio": "Seu carrinho está vazio.",
        "total_compra": "Total da Compra",
        "finalizar": "Finalizar Compra",
        "compra_feita": "Compra finalizada com sucesso!",
        "historico_secao": "📜 Histórico de Compras",
        "historico_vazio": "Nenhuma compra finalizada até o momento.",
        "itens_label": "itens",
        "data_label": "Data",
        "tema": "Modo Visual",
        "claro": "Claro",
        "escuro": "Escuro",
        "idioma": "Idioma",
        "moeda": "Moeda Principal",
        "limite_label": "Ajustar Limite de Gastos:",
        "prazo_label": "Selecione o Prazo do Limite:",
        "salvar_limite": "Salvar Limite e Prazo",
        "zerar_gastos": "🔄 Zerar Gasto Acumulado",
        "gastos_zerados": "Gasto zerado com sucesso!",
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
        "limite_salvo": "Novo limite e prazo salvos com sucesso!",
        "ver_grafico": "📊 Ver Histórico Visual (Gráfico)",
        "voltar_historico": "⬅️ Voltar ao Histórico",
        "msg_sucesso": "Parabéns, você gastou menos que no período anterior",
        "msg_alerta": "Você gastou um pouco mais ultimamente."
    },
    "ES": {
        "escanear": "📷 Escanear",
        "compras": "🛍️ Compras",
        "perfil": "👤 Perfil",
        "config": "⚙️ Configuración",
        "saudacao": "Hola",
        "gasto_mensal": "Gasto del Período",
        "limite_definido": "Límite Definido",
        "alerta_limite": "⚠️ ¡Has superado tu límite!",
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
        "carrinho_secao": "🛒 Carrito de Compras",
        "carrinho_vazio": "Tu carrito está vacío.",
        "total_compra": "Total de la Compra",
        "finalizar": "Finalizar Compra",
        "compra_feita": "¡Compra finalizada con éxito!",
        "historico_secao": "📜 Historial de Compras",
        "historico_vazio": "No hay compras finalizadas por el momento.",
        "itens_label": "artículos",
        "data_label": "Fecha",
        "tema": "Modo Visual",
        "claro": "Claro",
        "escuro": "Oscuro",
        "idioma": "Idioma",
        "moeda": "Moneda Principal",
        "limite_label": "Ajustar Límite de Gastos:",
        "prazo_label": "Seleccione el Plazo del Límite:",
        "salvar_limite": "Guardar Límite y Plazo",
        "zerar_gastos": "🔄 Reiniciar Gasto Acumulado",
        "gastos_zerados": "¡Gasto reiniciado con éxito!",
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
        "limite_salvo": "¡Nuevo límite y plazo guardados!",
        "ver_grafico": "📊 Ver Historial Visual (Gráfico)",
        "voltar_historico": "⬅️ Volver al Historial",
        "msg_sucesso": "Felicitaciones, gastaste menos que en el período anterior",
        "msg_alerta": "Has gastado un poco más últimamente."
    },
    "EN": {
        "escanear": "📷 Scan",
        "compras": "🛍️ Purchases",
        "perfil": "👤 Profile",
        "config": "⚙️ Settings",
        "saudacao": "Hello",
        "gasto_mensal": "Period Spending",
        "limite_definido": "Set Limit",
        "alerta_limite": "⚠️ You have exceeded your limit!",
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
        "carrinho_secao": "🛒 Shopping Cart",
        "carrinho_vazio": "Your cart is empty.",
        "total_compra": "Purchase Total",
        "finalizar": "Checkout",
        "compra_feita": "Purchase completed successfully!",
        "historico_secao": "📜 Purchase History",
        "historico_vazio": "No completed purchases yet.",
        "itens_label": "items",
        "data_label": "Date",
        "tema": "Visual Mode",
        "claro": "Light",
        "escuro": "Dark",
        "idioma": "Language",
        "moeda": "Main Currency",
        "limite_label": "Adjust Spending Limit:",
        "prazo_label": "Select Limit Period:",
        "salvar_limite": "Save Limit and Period",
        "zerar_gastos": "🔄 Reset Accumulated Spending",
        "gastos_zerados": "Spending reset successfully!",
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
        "limite_salvo": "New limit and period saved successfully!",
        "ver_grafico": "📊 View Visual History (Chart)",
        "voltar_historico": "⬅️ Back to History",
        "msg_sucesso": "Congratulations, you spent less than in the previous period",
        "msg_alerta": "You spent a bit more recently."
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
# 4. Estados da Sessão e Lógica do Ciclo
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
if "historico_compras" not in st.session_state:
    st.session_state.historico_compras = []

# Estado para controlar a navegação de telas (Ex: Visualização Gráfica)
if "tela_grafico" not in st.session_state:
    st.session_state.tela_grafico = False

# Configuração de Limite e Prazo
if "limite_mensal_brl" not in st.session_state:
    st.session_state.limite_mensal_brl = 500.00
if "prazo_dias" not in st.session_state:
    st.session_state.prazo_dias = 30
if "data_inicio_ciclo" not in st.session_state:
    st.session_state.data_inicio_ciclo = datetime.date.today()
if "gasto_atual_brl" not in st.session_state:
    st.session_state.gasto_atual_brl = 0.00

# Histórico de períodos anteriores para o gráfico
if "historico_periodos" not in st.session_state:
    st.session_state.historico_periodos = [
        {"periodo": "Período -2", "total_brl": 320.00},
        {"periodo": "Período -1", "total_brl": 410.00}
    ]

# Verificação e Reset Automático por Vencimento do Prazo
hoje = datetime.date.today()
dias_decorridos = (hoje - st.session_state.data_inicio_ciclo).days

if dias_decorridos >= st.session_state.prazo_dias:
    st.session_state.historico_periodos.append({
        "periodo": f"Período {st.session_state.data_inicio_ciclo.strftime('%d/%m')}",
        "total_brl": st.session_state.gasto_atual_brl
    })
    st.session_state.gasto_atual_brl = 0.00
    st.session_state.data_inicio_ciclo = hoje

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
# 5. Estilização CSS
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
    .product-card, .budget-card, .history-card {{
        background-color: {card_bg};
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 1px solid {border_color};
        margin-top: 10px;
        margin-bottom: 15px;
    }}
    .price-tag {{ font-size: 1.6rem; font-weight: 800; color: #2E7D32; margin: 4px 0; }}

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
# 6. Abas Inferiores Unificadas (4 Abas)
# ==========================================
tab_scanner, tab_compras, tab_perfil, tab_config = st.tabs([
    t["escanear"], 
    t["compras"], 
    t["perfil"], 
    t["config"]
])

# --- ABA 1: ESCANEAR ---
with tab_scanner:
    st.title("🛒 Scan Market")
    st.caption(f"{t['saudacao']}, **{st.session_state.usuario_atual}**!")
    
    porcentagem = min(st.session_state.gasto_atual_brl / st.session_state.limite_mensal_brl, 1.0)
    dias_restantes = max(0, st.session_state.prazo_dias - dias_decorridos)
    
    st.markdown('<div class="budget-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.caption(t["gasto_mensal"])
        st.markdown(f"**{fmt_moeda(st.session_state.gasto_atual_brl)}**")
    with c2:
        st.caption(t["limite_definido"])
        st.markdown(f"**{fmt_moeda(st.session_state.limite_mensal_brl)}**")
    
    st.progress(porcentagem)
    st.caption(f"📅 Renovação automática em **{dias_restantes} dias** ({st.session_state.prazo_dias} dias de prazo)")

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

# --- ABA 2: COMPRAS (CARRINHO + HISTÓRICO + TELA GRÁFICA) ---
with tab_compras:
    # SE A TELA GRÁFICA ESTIVER ATIVA, ABRE UMA NOVA TELA COMPLETA
    if st.session_state.tela_grafico:
        st.subheader("📊 Comparativo de Gastos por Período")
        
        dados_grafico = []
        for p in st.session_state.historico_periodos[-3:]:
            dados_grafico.append({"Período": p["periodo"], "Gasto": p["total_brl"] * cotacoes.get(st.session_state.moeda, 1.0)})
        dados_grafico.append({"Período": "Atual", "Gasto": st.session_state.gasto_atual_brl * cotacoes.get(st.session_state.moeda, 1.0)})

        df_grafico = pd.DataFrame(dados_grafico).set_index("Período")
        st.bar_chart(df_grafico, use_container_width=True)

        gasto_anterior = st.session_state.historico_periodos[-1]["total_brl"] if len(st.session_state.historico_periodos) > 0 else 0
        if st.session_state.gasto_atual_brl <= gasto_anterior:
            st.success(t["msg_sucesso"])
        else:
            st.warning(t["msg_alerta"])

        st.divider()
        if st.button(t["voltar_historico"], width="stretch"):
            st.session_state.tela_grafico = False
            st.rerun()

    else:
        # 1. SEÇÃO DO CARRINHO
        st.subheader(t["carrinho_secao"])
        
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
                agora = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
                st.session_state.gasto_atual_brl += total_brl
                
                st.session_state.historico_compras.insert(0, {
                    "data": agora,
                    "total_brl": total_brl,
                    "itens_qtd": sum(i["quantidade"] for i in st.session_state.carrinho)
                })
                
                st.session_state.carrinho = []
                st.success(t["compra_feita"])
                st.rerun()

        st.divider()

        # 2. SEÇÃO DO HISTÓRICO DE COMPRAS
        st.subheader(t["historico_secao"])
        
        # Botão para ABRIR A NOVA TELA DO GRÁFICO
        if st.button(t["ver_grafico"], width="stretch"):
            st.session_state.tela_grafico = True
            st.rerun()

        st.caption("")

        if len(st.session_state.historico_compras) == 0:
            st.caption(t["historico_vazio"])
        else:
            for idx_h, compra in enumerate(st.session_state.historico_compras):
                st.markdown('<div class="history-card">', unsafe_allow_html=True)
                col_h1, col_h2 = st.columns([2, 1])
                with col_h1:
                    st.markdown(f"🗓️ **{compra['data']}**")
                    st.caption(f"{compra['itens_qtd']} {t['itens_label']}")
                with col_h2:
                    st.markdown(f"**{fmt_moeda(compra['total_brl'])}**")
                st.markdown('</div>', unsafe_allow_html=True)

# --- ABA 3: PERFIL ---
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

# --- ABA 4: CONFIGURAÇÕES ---
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

    prazos_opcoes = [7, 15, 30]
    novo_prazo = st.selectbox(
        t["prazo_label"],
        options=prazos_opcoes,
        format_func=lambda x: f"{x} dias",
        index=prazos_opcoes.index(st.session_state.prazo_dias)
    )

    if st.button(t["salvar_limite"], width="stretch"):
        st.session_state.limite_mensal_brl = novo_limite
        st.session_state.prazo_dias = novo_prazo
        st.success(t["limite_salvo"])
        st.rerun()

    st.divider()

    if st.button(t["zerar_gastos"], width="stretch"):
        st.session_state.gasto_atual_brl = 0.00
        st.success(t["gastos_zerados"])
        st.rerun()
