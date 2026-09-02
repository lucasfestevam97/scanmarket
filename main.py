from fastapi import FastAPI
import pandas as pd
import os

app = FastAPI()

# Caminho e leitura do arquivo
ARQUIVO_EXCEL = "banco_de_dados_app.xlsx"

@app.get("/")
def home():
    if os.path.exists(ARQUIVO_EXCEL):
        return {"status": "API online", "excel_encontrado": True}
    return {"status": "API online", "excel_encontrado": False, "erro": f"Arquivo {ARQUIVO_EXCEL} nao encontrado na raiz"}

@app.get("/produto/{codigo}")
def buscar_produto(codigo: str):
    if not os.path.exists(ARQUIVO_EXCEL):
        return {"encontrado": False, "erro": "Arquivo Excel nao encontrado"}
        
    df_produtos = pd.read_excel(ARQUIVO_EXCEL)
    codigo_busca = str(codigo).strip()
    
    # Tratamento simples de colunas
    codigos_excel = df_produtos['Código de Barras'].astype(str).apply(lambda x: x.split('.')[0].strip())
    resultado = df_produtos[codigos_excel == codigo_busca]
    
    if not resultado.empty:
        prod = resultado.iloc[0]
        return {
            "encontrado": True,
            "nome": str(prod['Nome']),
            "preco_brl": float(prod['Preço (R$)'])
        }
        
    return {"encontrado": False}
