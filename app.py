import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
import tkinter as tk
from tkinter import filedialog, messagebox

# Configuração do tema da interface
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class LeitorCodigoBarrasApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Leitor de Código de Barras Avançado")
        self.geometry("900x650")
        self.resizable(False, False)

        self.caminho_imagem = None
        self.codigo_detectado = None

        self._criar_interface()

    def _criar_interface(self):
        # --- TÍTULO ---
        self.lbl_titulo = ctk.CTkLabel(
            self, text="Leitor & Processador de Código de Barras", font=("Arial", 22, "bold")
        )
        self.lbl_titulo.pack(pady=15)

        # --- PAINEL PRINCIPAL ---
        self.frame_conteudo = ctk.CTkFrame(self)
        self.frame_conteudo.pack(fill="both", expand=True, padx=20, pady=10)

        # Esquerda: Visualização da Imagem
        self.frame_imagem = ctk.CTkFrame(self.frame_conteudo, width=450, height=400)
        self.frame_imagem.pack(side="left", padx=15, pady=15, fill="both", expand=True)

        self.lbl_preview = ctk.CTkLabel(
            self.frame_imagem, text="Nenhuma imagem carregada", font=("Arial", 14)
        )
        self.lbl_preview.pack(expand=True)

        # Direita: Controles e Resultados
        self.frame_controles = ctk.CTkFrame(self.frame_conteudo, width=350)
        self.frame_controles.pack(side="right", padx=15, pady=15, fill="both", expand=True)

        self.btn_carregar = ctk.CTkButton(
            self.frame_controles, text="📁 Selecionar Imagem", command=self.carregar_imagem, height=40
        )
        self.btn_carregar.pack(fill="x", padx=15, pady=15)

        self.btn_processar = ctk.CTkButton(
            self.frame_controles,
            text="🔍 Ler Código de Barras",
            command=self.processar_imagem,
            height=40,
            fg_color="green",
            hover_color="darkgreen",
            state="disabled"
        )
        self.btn_processar.pack(fill="x", padx=15, pady=5)

        self.lbl_status = ctk.CTkLabel(
            self.frame_controles, text="Aguardando imagem...", font=("Arial", 12), text_color="gray"
        )
        self.lbl_status.pack(pady=15)

        # Resultados
        self.lbl_resultado_titulo = ctk.CTkLabel(
            self.frame_controles, text="Resultado da Leitura:", font=("Arial", 14, "bold")
        )
        self.lbl_resultado_titulo.pack(anchor="w", padx=15, pady=(10, 5))

        self.txt_resultado = ctk.CTkTextbox(self.frame_controles, height=100, font=("Consolas", 13))
        self.txt_resultado.pack(fill="x", padx=15, pady=5)

        self.btn_copiar = ctk.CTkButton(
            self.frame_controles,
            text="📋 Copiar Código",
            command=self.copiar_codigo,
            height=30,
            state="disabled"
        )
        self.btn_copiar.pack(fill="x", padx=15, pady=10)

    def carregar_imagem(self):
        caminho = filedialog.askopenfilename(
            filetypes=[("Imagens", "*.jpg *.jpeg *.png *.bmp *.webp")]
        )
        if caminho:
            self.caminho_imagem = caminho
            self.exibir_preview(caminho)
            self.btn_processar.configure(state="normal")
            self.lbl_status.configure(text="Imagem carregada. Clique em 'Ler Código'.", text_color="white")
            self.txt_resultado.delete("1.0", tk.END)
            self.btn_copiar.configure(state="disabled")

    def exibir_preview(self, img_source):
        if isinstance(img_source, str):
            img = Image.open(img_source)
        else:
            img = Image.fromarray(cv2.cvtColor(img_source, cv2.COLOR_BGR2RGB))

        # Redimensiona para caber na tela sem distorcer
        img.thumbnail((400, 380))
        img_tk = ImageTk.PhotoImage(img)

        self.lbl_preview.configure(image=img_tk, text="")
        self.lbl_preview.image = img_tk

    def rotacionar_imagem(self, img, angulo):
        if angulo == 90:
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        elif angulo == 180:
            return cv2.rotate(img, cv2.ROTATE_180)
        elif angulo == 270:
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return img

    def gerar_variacoes(self, img_gray):
        variacoes = []
        variacoes.append(("Cinza Simples", img_gray))

        # Zoom 2x
        resized = cv2.resize(img_gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        variacoes.append(("Zoom 2x", resized))

        # Ajuste de Contraste (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        variacoes.append(("Ajuste de Contraste (CLAHE)", clahe.apply(img_gray)))

        # Limiarização Adaptativa (Preto e Branco puro)
        thresh = cv2.adaptiveThreshold(
            img_gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10
        )
        variacoes.append(("Threshold Adaptativo", thresh))

        # Suavização + Otsu
        blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
        _, thresh_otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        variacoes.append(("Filtro Otsu", thresh_otsu))

        return variacoes

    def processar_imagem(self):
        if not self.caminho_imagem:
            return

        self.lbl_status.configure(text="Processando variações...", text_color="yellow")
        self.update()

        img_original = cv2.imread(self.caminho_imagem)
        if img_original is None:
            messagebox.showerror("Erro", "Não foi possível carregar a imagem.")
            return

        angulos = [0, 90, 180, 270]
        sucesso = False

        for angulo in angulos:
            img_rotacionada = self.rotacionar_imagem(img_original, angulo)
            img_gray = cv2.cvtColor(img_rotacionada, cv2.COLOR_BGR2GRAY)

            variacoes = self.gerar_variacoes(img_gray)

            for nome_tecnica, img_processada in variacoes:
                barcodes = decode(img_processada)

                if barcodes:
                    sucesso = True
                    self.exibir_preview(img_rotacionada)
                    
                    # Formatar resultados
                    texto_resultado = ""
                    codigos = []
                    for barcode in barcodes:
                        dado = barcode.data.decode("utf-8")
                        tipo = barcode.type
                        codigos.append(dado)
                        texto_resultado += f"Código: {dado}\nTipo: {tipo}\nRotação: {angulo}°\nTécnica: {nome_tecnica}\n\n"

                    self.codigo_detectado = "\n".join(codigos)
                    self.txt_resultado.delete("1.0", tk.END)
                    self.txt_resultado.insert("1.0", texto_resultado)

                    self.lbl_status.configure(text="✅ Código lido com sucesso!", text_color="lightgreen")
                    self.btn_copiar.configure(state="normal")
                    break

            if sucesso:
                break

        if not sucesso:
            self.lbl_status.configure(text="❌ Falha ao ler código de barras.", text_color="red")
            self.txt_resultado.delete("1.0", tk.END)
            self.txt_resultado.insert("1.0", "Nenhum código foi identificado após tentar todas as rotações e filtros.")
            self.btn_copiar.configure(state="disabled")

    def copiar_codigo(self):
        if self.codigo_detectado:
            self.clipboard_clear()
            self.clipboard_append(self.codigo_detectado)
            messagebox.showinfo("Sucesso", "Código copiado para a área de transferência!")


if __name__ == "__main__":
    app = LeitorCodigoBarrasApp()
    app.mainloop()
