@app.get("/produto/{codigo}")
def buscar_produto(codigo: str):
    # Converte a coluna para string e remove espaços extras
    codigo_limpo = str(codigo).strip()
    
    # Faz o mesmo com a coluna do Excel
    df_produtos['Código de Barras'] = df_produtos['Código de Barras'].astype(str).str.replace('\.0$', '', regex=True).str.strip()
    
    resultado = df_produtos[df_produtos['Código de Barras'] == codigo_limpo]
    
    if not resultado.empty:
        prod = resultado.iloc[0]
        return {
            "encontrado": True,
            "nome": str(prod['Nome']),
            "preco_brl": float(prod['Preço (R$)'])
        }
    return {"encontrado": False}
