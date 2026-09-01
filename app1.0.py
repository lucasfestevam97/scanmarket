import streamlit as st
import pandas as pd
import cv2
import numpy as np
from datetime import datetime
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase, WebRtcMode

# Inicializa o detector nativo do OpenCV (Compatível com Python 3.14)
barcode_detector = cv2.barcode.BarcodeDetector()

# ---------------------------------------------------------
# Processador de Vídeo para Python 3.14
# ---------------------------------------------------------
class BarcodeScanner(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        
        # Leitura nativa via OpenCV
        ok, decoded_info, decoded_type, corners = barcode_detector.detectAndDecode(img)
        
        if ok and decoded_info:
            for info in decoded_info:
                if info:
                    # Salva o código detectado no estado do app
                    st.session_state.codigo_lido_camera = info
                    
        # Desenha retângulo verde caso encontre o código
        if corners is not None:
            corners = corners.astype(int)
            for corner in corners:
                cv2.polylines(img, [corner], True, (0, 255, 0), 3)

        return img