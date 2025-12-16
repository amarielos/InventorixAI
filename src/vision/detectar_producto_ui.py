# detectar_producto_ui.py
import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame, QShortcut
)
from PyQt5.QtGui import QImage, QPixmap, QKeySequence
from PyQt5.QtCore import QTimer, Qt

from src.vision.detectar_producto import DetectorProducto


class DetectorUI(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Inventorix AI · Escaneo")
        self.resize(1100, 650)
        self.setStyleSheet(self.estilos())

        # --------- LÓGICA ---------
        self.detector = DetectorProducto()
        self.resultado = None

        # --------- UI ---------
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(720, 540)
        self.video_label.setStyleSheet(
            "background-color: #000; border-radius: 8px;"
        )

        panel = QFrame()
        panel.setObjectName("panel")

        titulo = QLabel("📦 Conteo detectado")
        titulo.setObjectName("titulo")

        self.info_label = QLabel("Esperando detección...")
        self.info_label.setObjectName("conteo")

        self.btn_entrada = QPushButton("⬆ Entrada  (E)")
        self.btn_salida = QPushButton("⬇ Salida   (S)")
        self.btn_cancelar = QPushButton("✖ Cancelar (Q)")

        self.btn_entrada.clicked.connect(lambda: self.confirmar("entrada"))
        self.btn_salida.clicked.connect(lambda: self.confirmar("salida"))
        self.btn_cancelar.clicked.connect(self.cancelar)

        self.btn_entrada.setEnabled(False)
        self.btn_salida.setEnabled(False)

        panel_layout = QVBoxLayout()
        panel_layout.addWidget(titulo)
        panel_layout.addWidget(self.info_label)
        panel_layout.addStretch()
        panel_layout.addWidget(self.btn_entrada)
        panel_layout.addWidget(self.btn_salida)
        panel_layout.addWidget(self.btn_cancelar)

        panel.setLayout(panel_layout)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(24)
        main_layout.addWidget(self.video_label)
        main_layout.addWidget(panel)
        self.setLayout(main_layout)

        # --------- ATAJOS ---------
        QShortcut(QKeySequence("E"), self, activated=lambda: self.confirmar("entrada"))
        QShortcut(QKeySequence("S"), self, activated=lambda: self.confirmar("salida"))
        QShortcut(QKeySequence("Q"), self, activated=self.cancelar)

        # --------- TIMER ---------
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    # ==================================================
    def update_frame(self):
        frame, conteo = self.detector.leer_frame()
        if frame is None:
            return

        if conteo:
            texto = "\n".join(f"• {k}: {v}" for k, v in conteo.items())
            self.info_label.setText(texto)
            self.btn_entrada.setEnabled(True)
            self.btn_salida.setEnabled(True)
        else:
            self.info_label.setText("Esperando detección...")
            self.btn_entrada.setEnabled(False)
            self.btn_salida.setEnabled(False)

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(img))

    def confirmar(self, tipo):
        self.resultado = self.detector.obtener_resultado(tipo)
        self.close()

    def cancelar(self):
        self.resultado = None
        self.close()

    def closeEvent(self, event):
        self.detector.liberar()
        event.accept()

    # ==================================================
    def estilos(self):
        return """
        QWidget {
            background-color: #f5f7fa;
            font-family: Arial;
        }

        #panel {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 20px;
            min-width: 280px;
        }

        QLabel#titulo {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        QLabel#conteo {
            font-size: 15px;
            background-color: #f0f2f6;
            border-radius: 8px;
            padding: 12px;
        }

        QPushButton {
            height: 42px;
            border-radius: 8px;
            font-size: 14px;
        }

        QPushButton:enabled {
            background-color: #1f77ff;
            color: white;
        }

        QPushButton:disabled {
            background-color: #cfd6e0;
            color: #6b7280;
        }

        QPushButton:hover:enabled {
            background-color: #155fd1;
        }
        """


# =========================================================
# FUNCIÓN INTERNA PARA LA UI
# =========================================================
def lanzar_ui():
    app = QApplication(sys.argv)
    win = DetectorUI()
    win.show()
    app.exec_()
    return win.resultado
