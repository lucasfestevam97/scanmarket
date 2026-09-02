from fastapi import FastAPI
import pandas as pd
import os
import re

app = FastAPI()

ARQUIVO_EXCEL = "banco_de_dados_app.xlsx"

def limpar_codigo(val):
    if pd.isna(val):
        return ""
    # Converte para string e remove o ".0" do Excel se houver
    s = str(val).split('.')[0].strip()
    # Mantém apenas os dígitos numéricos
    return re.sub(r'\D', '', s)

@app.get("/")
def home():
    return {"status": "API online"}

@app.get("/produto/{codigo}")
def buscar_produto(codigo: str):
    if not os.path.exists(ARQUIVO_EXCEL):
        return {"encontrado": False, "erro": "Arquivo Excel nao encontrado"}
        
    df_produtos = pd.read_excel(ARQUIVO_EXCEL)
    
    # Limpa o código pesquisado
    codigo_busca = limpar_codigo(codigo)
    
    # Aplica a limpeza em toda a coluna de Código de Barras do Excel
    codigos_excel = df_produtos['Código de Barras'].apply(limpar_codigo)
    
    # Procura a correspondência
    resultado = df_produtos[codigos_excel == codigo_busca]
    
    if not resultado.empty:
        prod = resultado.iloc[0]
        return {
            "encontrado": True,
            "nome": str(prod['Nome']),
            "preco_brl": float(prod['Preço (R$)'])
        }
    
    print(f"Código buscado: '{codigo}' (limpo: '{codigo_busca}') -> Não encontrado.")
    return {"encontrado": False, "codigo_recebido": codigo_busca}
