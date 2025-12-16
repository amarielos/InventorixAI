# detectar_producto.py
import cv2
import json
from collections import Counter
from ultralytics import YOLO


class DetectorProducto:
    # CAMBIAR ÍNDICE DE CÁMARA SEGÚN LA QUE SE USE (cam_index=0, 1, 2, ...)
    def __init__(self, cam_index=3, conf=0.4):
        # Inventario
        with open("data/inventario.json", "r", encoding="utf-8") as f:
            self.inventario = json.load(f)

        self.map_inv = {p["name"].lower(): p for p in self.inventario}

        # Modelo YOLO
        self.model = YOLO("yolov8n.pt")
        self.conf = conf

        # Cámara
        self.cap = cv2.VideoCapture(cam_index)

        self.conteo = Counter()

    def leer_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None, None

        results = self.model(frame, conf=self.conf)
        frame_annotated = results[0].plot()

        clases = []
        boxes = results[0].boxes
        if boxes is not None:
            for box in boxes:
                class_id = int(box.cls[0])
                clases.append(self.model.names[class_id].lower())

        self.conteo = Counter(clases)
        return frame_annotated, self.conteo

    def obtener_resultado(self, tipo_movimiento):
        for nombre, cantidad in self.conteo.items():
            if nombre in self.map_inv:
                return {
                    "producto": self.map_inv[nombre],
                    "cantidad": int(cantidad),
                    "tipo": tipo_movimiento
                }
        return None

    def liberar(self):
        self.cap.release()


# =========================================================
# FUNCIÓN QUE CONSUME EL FRONT (STREAMLIT)
# =========================================================
def detectar_producto():
    """
    Punto de entrada para el frontend.
    Abre la UI de escaneo y devuelve el resultado.
    """
    from src.vision.detectar_producto_ui import lanzar_ui
    return lanzar_ui()
