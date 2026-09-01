import streamlit as st
import pandas as pd
import cv2
import numpy as np
import json
import os
import bcrypt
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode

# ---------------------------------------------------------
# 1. Configuração da Página
# ---------------------------------------------------------
st.set_page_config(page_title="Scan Market", page_icon="🛒", layout="wide")

# ---------------------------------------------------------
# 2. Gerenciamento de Usuários (JSON + Bcrypt)
# ---------------------------------------------------------
USER_FILE = "usuarios.json"

def carregar_usuarios():
    if not os.path.exists(USER_FILE):
        senha_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        usuarios_padrao = {
            "admin": {"nome": "Administrador", "senha": senha_hash}
        }
        with open(USER_FILE, "w") as f:
            json.dump(usuarios_padrao, f, indent=4)
        return usuarios_padrao
    with open(USER_FILE, "r") as f:
        return json.load(f)

def salvar_usuario(username, nome, senha_plana):
    usuarios = carregar_usuarios()
    if username in usuarios:
        return False, "Nome de usuário já existe!"
    
    senha_hash = bcrypt.hashpw(senha_plana.encode(), bcrypt.gensalt()).decode()
    usuarios[username] = {"nome": nome, "senha": senha_hash}
    
    with open(USER_FILE, "w") as f:
        json.dump(usuarios, f, indent=4)
    return True, "Conta criada com sucesso!"

def verificar_login(username, senha_plana):
    usuarios = carregar_usuarios()
    if username in usuarios:
        hash_salvo = usuarios[username]["senha"].encode()
        if bcrypt.checkpw(senha_plana.encode(), hash_salvo):
            return True, usuarios[username]["nome"]
    return False, ""

# ---------------------------------------------------------
# 3. Estado de Sessão e Autenticação
# ---------------------------------------------------------
if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = None
if "nome_usuario" not in st.session_state:
    st.session_state.nome_usuario = ""

if st.session_state.usuario_logado is None:
    st.title("🛒 Scan Market - Acesso")
    
    tab_login, tab_cadastro = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
    
    with tab_login:
        st.subheader("Faça seu Login")
        user_input = st.text_input("Usuário:", key="login_user")
        pass_input = st.text_input("Senha:", type="password", key="login_pass")
        
        if st.button("Acessar Conta", use_container_width=True):
            sucesso, nome = verificar_login(user_input, pass_input)
            if sucesso:
                st.session_state.usuario_logado = user_input
                st.session_state.nome_usuario = nome
                st.success(f"Bem-vindo(a), {nome}!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

    with tab_cadastro:
        st.subheader("Cadastre-se")
        novo_nome = st.text_input("Seu Nome Completo:", key="cad_nome")
        novo_user = st.text_input("Nome de Usuário (login):", key="cad_user")
        nova_pass = st.text_input("Sua Senha:", type="password", key="cad_pass")
        confirma_pass = st.text_input("Confirme a Senha:", type="password", key="cad_pass_conf")
        
        if st.button("Criar Minha Conta", use_container_width=True):
            if not novo_nome or not novo_user or not nova_pass:
                st.warning("Preencha todos os campos!")
            elif nova_pass != confirma_pass:
                st.error("As senhas não coincidem.")
            else:
                ok, msg = salvar_usuario(novo_user.strip(), novo_nome.strip(), nova_pass)
                if ok:
                    st.success(f"{msg} Vá na aba 'Entrar' para acessar.")
                else:
                    st.error(msg)
                    
    st.stop()

# ---------------------------------------------------------
# 4. Dados Específicos do Usuário Logado
# ---------------------------------------------------------
user_key = st.session_state.usuario_logado

if f'carrinho_{user_key}' not in st.session_state:
    st.session_state[f'carrinho_{user_key}'] = []
if f'historico_{user_key}' not in st.session_state:
    st.session_state[f'historico_{user_key}'] = []
if f'limite_{user_key}' not in st.session_state:
    st.session_state[f'limite_{user_key}'] = 1000.00
if 'codigo_lido_camera' not in st.session_state:
    st.session_state.codigo_lido_camera = None

# ---------------------------------------------------------
# 5. Carregar Banco de Dados Excel
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
# 6. Leitor de Câmera (Barcode Detector)
# ---------------------------------------------------------
barcode_detector = cv2.barcode.BarcodeDetector()

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
# 7. Interface Principal e Barra Lateral
# ---------------------------------------------------------
with st.sidebar:
    st.title("🛒 Scan Market")
    st.write(f"👤 **{st.session_state.nome_usuario}** (`{user_key}`)")
    
    st.divider()
    st.subheader("💰 Seu Limite Mensal")
    st.session_state[f'limite_{user_key}'] = st.number_input(
        "Limite (R$):", 
        min_value=50.0, 
        value=st.session_state[f'limite_{user_key}'], 
        step=50.0
    )
    
    st.divider()
    if st.button("🚪 Sair da Conta", use_container_width=True):
        st.session_state.usuario_logado = None
        st.session_state.nome_usuario = ""
        st.rerun()

carrinho_atual = st.session_state[f'carrinho_{user_key}']
historico_atual = st.session_state[f'historico_{user_key}']
limite_atual = st.session_state[f'limite_{user_key}']

total_gasto_acumulado = sum(c['Total'] for c in historico_atual)
percentual_gasto = min(total_gasto_acumulado / limite_atual, 1.0) if limite_atual > 0 else 0.0

st.title("🛒 Painel de Compras")
col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Gasto Acumulado", f"R$ {total_gasto_acumulado:.2f}")
col_m2.metric("Saldo Restante", f"R$ {(limite_atual - total_gasto_acumulado):.2f}")
col_m3.metric("Limite Mensal", f"R$ {limite_atual:.2f}")

st.progress(percentual_gasto)

# ---------------------------------------------------------
# 8. Abas Compras / Histórico
# ---------------------------------------------------------
tab_compras, tab_historico = st.tabs(["🛒 Leitor & Compras", "📜 Meu Histórico"])

with tab_compras:
    c_esq, c_dir = st.columns([1, 1])
    with c_esq:
        st.subheader("📸 Leitor de Código de Barras")
        webrtc_streamer(
            key="scanner", 
            mode=WebRtcMode.SENDRECV, 
            video_transformer_factory=BarcodeScanner, 
            media_stream_constraints={"video": True, "audio": False}
        )
        
        # Entrada de código (via Câmera ou Digitação Manual)
        codigo_manual = st.text_input("Digitação Manual do Código:")
        codigo_ativo = st.session_state.codigo_lido_camera or codigo_manual
        
        # --- CONFIRMAÇÃO DO PRODUTO ESCANEADO ---
        if codigo_ativo:
            codigo_limpo = str(codigo_ativo).strip()
            prod = df_produtos[df_produtos['Código de Barras'] == codigo_limpo]
            
            if not prod.empty:
                nome_prod = prod.iloc[0]['Nome']
                preco_prod = float(prod.iloc[0]['Preço (R$)'])
                
                # Card de Confirmação Visual
                st.success(f"✅ **Produto Detectado!**")
                with st.container(border=True):
                    st.markdown(f"### 📦 {nome_prod}")
                    st.markdown(f"**Preço Unitário:** R$ {preco_prod:.2f}")
                    st.caption(f"Código: `{codigo_limpo}`")
                    
                    qtd = st.number_input("Quantidade desejava:", min_value=1, value=1, key="qtd_input")
                    total_item = preco_prod * qtd
                    st.write(f"**Subtotal:** R$ {total_item:.2f}")
                    
                    col_act1, col_act2 = st.columns(2)
                    if col_act1.button("➕ Adicionar ao Carrinho", use_container_width=True, type="primary"):
                        st.session_state[f'carrinho_{user_key}'].append({
                            "Nome": nome_prod, 
                            "Preço Un.": preco_prod, 
                            "Qtd": qtd, 
                            "Total": total_item
                        })
                        st.session_state.codigo_lido_camera = None
                        st.success(f"Adicionado {qtd}x {nome_prod}!")
                        st.rerun()
                        
                    if col_act2.button("❌ Cancelar", use_container_width=True):
                        st.session_state.codigo_lido_camera = None
                        st.rerun()
            else:
                st.error(f"❌ Código `{codigo_limpo}` não encontrado no banco de dados.")
                if st.button("Limpar Busca"):
                    st.session_state.codigo_lido_camera = None
                    st.rerun()

    with c_dir:
        st.subheader("🛍️ Seu Carrinho")
        total_carrinho = sum(i['Total'] for i in carrinho_atual)
        
        if not carrinho_atual:
            st.info("Seu carrinho está vazio no momento.")
        else:
            for idx, item in enumerate(carrinho_atual):
                col_item1, col_item2 = st.columns([3, 1])
                col_item1.write(f"**{item['Nome']}** ({item['Qtd']}x R$ {item['Preço Un.']:.2f}) = **R$ {item['Total']:.2f}**")
                if col_item2.button("❌", key=f"del_{idx}"):
                    st.session_state[f'carrinho_{user_key}'].pop(idx)
                    st.rerun()
            
            st.divider()
            st.write(f"### Total do Carrinho: R$ {total_carrinho:.2f}")
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.button("💳 Finalizar Compra", use_container_width=True):
                st.session_state[f'historico_{user_key}'].append({
                    "Data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Total": total_carrinho,
                    "Itens": len(carrinho_atual)
                })
                st.session_state[f'carrinho_{user_key}'] = []
                st.success("Compra registrada com sucesso no histórico!")
                st.rerun()
                
            if col_b2.button("🗑️ Limpar Carrinho", use_container_width=True):
                st.session_state[f'carrinho_{user_key}'] = []
                st.rerun()

with tab_historico:
    st.subheader("📜 Histórico de Sessões")
    if historico_atual:
        st.dataframe(pd.DataFrame(historico_atual), use_container_width=True)
    else:
        st.info("Nenhuma compra registrada até o momento.")
