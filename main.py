from fastapi import FastAPI
import pandas as pd

app = FastAPI()

# Carrega o banco de dados
df_produtos = pd.read_excel("banco_de_dados_app.xlsx")
df_produtos['Código de Barras'] = df_produtos['Código de Barras'].astype(str).str.strip()

@app.get("/produto/{codigo}")
def buscar_produto(codigo: str):
    resultado = df_produtos[df_produtos['Código de Barras'] == codigo.strip()]
    if not resultado.empty:
        prod = resultado.iloc[0]
        return {
            "encontrado": True,
            "nome": prod['Nome'],
            "preco_brl": float(prod['Preço (R$)'])
        }
    return {"encontrado": False}
