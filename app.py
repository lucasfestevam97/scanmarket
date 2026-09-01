import cv2
import numpy as np
from pyzbar.pyzbar import decode

def ler_codigo_de_barras_robusto(caminho_imagem):
    """
    Tenta ler códigos de barras de uma imagem aplicando múltiplos métodos 
    de pré-processamento sequencialmente.
    """
    # 1. Carregar a imagem original
    img = cv2.imread(caminho_imagem)
    if img is None:
        print(f"Erro: Não foi possível carregar a imagem em '{caminho_imagem}'.")
        return None

    print(f"--- Processando: {caminho_imagem} ---")

    # MÉTODOS DE PRÉ-PROCESSAMENTO A SEREM TESTADOS EM SEQUÊNCIA
    
    # Tentativa 1: Imagem Original
    barcodes = decode(img)
    if barcodes:
        print("[SUCESSO] Detectado na Imagem Original.")
        return _extrair_resultados(barcodes)

    # Tentativa 2: Escala de Cinza (Gray)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    barcodes = decode(gray)
    if barcodes:
        print("[SUCESSO] Detectado em Escala de Cinza.")
        return _extrair_resultados(barcodes)

    # Tentativa 3: Redimensionamento / Escala (Zoom 2x) - Útil para barras muito pequenas
    resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    barcodes = decode(resized)
    if barcodes:
        print("[SUCESSO] Detectado após Redimensionamento (Zoom 2x).")
        return _extrair_resultados(barcodes)

    # Tentativa 4: Aumento de Contraste usando CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast_img = clahe.apply(gray)
    barcodes = decode(contrast_img)
    if barcodes:
        print("[SUCESSO] Detectado após Ajuste de Contraste (CLAHE).")
        return _extrair_resultados(barcodes)

    # Tentativa 5: Binarização / Threshold Adaptativo (Preto e Branco puro)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
    )
    barcodes = decode(thresh)
    if barcodes:
        print("[SUCESSO] Detectado após Threshold Adaptativo.")
        return _extrair_resultados(barcodes)

    # Tentativa 6: Suavização/Filtro Gaussiano + Threshold (Remoção de ruído)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    barcodes = decode(thresh_otsu)
    if barcodes:
        print("[SUCESSO] Detectado após Desenfoque Gaussiano + Otsu Threshold.")
        return _extrair_resultados(barcodes)

    print("[FALHA] Não foi possível ler o código de barras após todas as tentativas.")
    return []

def _extrair_resultados(barcodes):
    resultados = []
    for barcode in barcodes:
        dado = barcode.data.decode("utf-8")
        tipo = barcode.type
        resultados.append({"conteudo": dado, "tipo": tipo})
        print(f"  -> Conteúdo: {dado} | Tipo: {tipo}")
    return resultados


# --- EXEMPLO DE USO ---
if __name__ == "__main__":
    # Substitua pelo caminho da sua imagem rotacionada
    caminho = "sua_imagem_rotacionada.jpg" 
    
    resultados = ler_codigo_de_barras_robusto(caminho)
    
    if resultados:
        print("\nCódigos encontrados:")
        for r in resultados:
            print(f"Tipo: {r['tipo']} | Valor: {r['conteudo']}")
    else:
        print("\nNenhum código lido.")
