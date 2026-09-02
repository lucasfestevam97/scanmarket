@app.get("/produto/{codigo}")
def buscar_produto(codigo: str):
    codigo_busca = str(codigo).strip()
    
    # Garante que a coluna do Excel vire texto limpo sem casas decimais (.0)
    coluna_codigos = df_produtos['Código de Barras'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    
    resultado = df_produtos[coluna_codigos == codigo_busca]
    
    if not resultado.empty:
        prod = resultado.iloc[0]
        return {
            "encontrado": True,
            "nome": str(prod['Nome']),
            "preco_brl": float(prod['Preço (R$)'])
        }
    return {"encontrado": False}
