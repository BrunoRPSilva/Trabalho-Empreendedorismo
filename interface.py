"""PONTE | Interface gráfica com webcam real (IA e voz ainda simuladas).

Execute com: python interface.py
Requer: PySide6 e opencv-python

A webcam é mostrada na janela Qt. O Gemini e a voz permanecem
independentes nesta fase e ainda NÃO reconhecem/traduzem sinais.
"""

from __future__ import annotations

import sys

import cv2
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QSize, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMainWindow,
    QMessageBox, QPushButton, QSizePolicy, QVBoxLayout, QWidget, QInputDialog,
)

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# Paleta de cores escolhida para manter a identidade do mockup.
C = {
    "navy": "#083f4d",
    "teal": "#006875",
    "green": "#008675",
    "bg": "#f2f7fa",
    "text": "#133747",
    "muted": "#637c88",
    "border": "#d7e4e9",
    "light": "#e9f5f4",
}

STYLESHEET = f"""
QMainWindow, #root {{ background-color: {C['bg']}; }}
QWidget {{ font-family: 'Segoe UI', 'Arial', sans-serif; color: {C['text']}; }}
QFrame#card {{
    background-color: white;
    border: 1px solid {C['border']};
    border-radius: 18px;
}}
QFrame#header {{ background-color: transparent; border: none; }}
QFrame#pill {{
    background-color: #e8f7f2;
    border: 1px solid #c8e7db;
    border-radius: 16px;
}}
QFrame#demoPill {{
    background-color: #f2f8fa;
    border: 1px solid {C['border']};
    border-radius: 12px;
}}
QFrame#translationHead {{
    background-color: {C['teal']};
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
}}
QFrame#exampleBox {{
    background-color: #f6fafb;
    border: 1px solid {C['border']};
    border-radius: 12px;
}}
QFrame#historyItem {{
    background-color: #eef4f7;
    border-radius: 10px;
    border: none;
}}
QFrame#timeBox {{ background-color: #dff4f0; border-radius: 12px; }}
QFrame#bottomBar {{ background-color: #dce8ed; border-radius: 16px; border: none; }}
QPushButton {{
    background-color: #f7fbfc;
    color: {C['text']};
    border: 1px solid #b6cbd4;
    border-radius: 12px;
    padding: 11px 18px;
    font-size: 14px;
    font-weight: 650;
}}
QPushButton:hover {{ background-color: #ebf6f8; border-color: {C['teal']}; }}
QPushButton:pressed {{ background-color: #d5e9ed; }}
QPushButton:disabled {{ color: #889aa3; background-color: #e7edf0; border-color: #d2dfe4; }}
QPushButton#primary {{
    background-color: {C['green']};
    color: white;
    border: 1px solid #006f66;
}}
QPushButton#primary:hover {{ background-color: #006f64; }}
QPushButton#primary:disabled {{ background-color: #90b7af; border-color: #90b7af; }}
QPushButton#simulate {{
    background-color: #e4f4f2;
    border: 1px solid #baded7;
    color: {C['teal']};
}}
QPushButton#simulate:hover {{ background-color: #d2ebe5; }}
QPushButton#simulate:disabled {{ background-color: #eff3f4; color: #91a4a9; }}
"""


def text_label(text: str, size: int = 12, bold: bool = False, color: str | None = None) -> QLabel:
    """Cria um rótulo de texto com uma tipografia consistente."""
    lbl = QLabel(text)
    font = QFont("Segoe UI", size)
    font.setBold(bold)
    lbl.setFont(font)
    if color:
        lbl.setStyleSheet(f"color: {color}; background: transparent; border: none;")
    return lbl


def card_layout(spacing: int = 12, margins: tuple[int, int, int, int] = (18, 18, 18, 18)):
    """Monta um cartão visual padronizado e seu layout vertical."""
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(*margins)
    layout.setSpacing(spacing)
    return frame, layout


def section_title(title: str, extra: str = "") -> QWidget:
    area = QWidget()
    row = QHBoxLayout(area)
    row.setContentsMargins(0, 0, 0, 0)
    heading = text_label(title, 16, True, C["navy"])
    row.addWidget(heading)
    if extra:
        row.addStretch()
        row.addWidget(text_label(extra, 10, False, C["muted"]))
    return area


def status_pill(emoji: str, label: str) -> tuple[QFrame, QLabel]:
    pill = QFrame()
    pill.setObjectName("pill")
    r = QHBoxLayout(pill)
    r.setContentsMargins(12, 8, 12, 8)
    r.setSpacing(8)
    ico = text_label(emoji, 13, True, C["teal"])
    val = text_label(label, 10, True, C["navy"])
    r.addWidget(ico)
    r.addWidget(val)
    return pill, val


class CameraPreview(QWidget):
    """Quadros da câmera, ajustados sem cortar mãos ou rosto."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pixmap = QPixmap()
        self.live = False
        self.message = "Câmera desligada\nClique em Iniciar para exibir a imagem."
        self.setMinimumHeight(285)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def show_frame(self, frame):
        """Converte um quadro BGR (OpenCV) para uma imagem independente do Qt."""
        height, width = frame.shape[:2]
        image = QImage(
            frame.data, width, height, frame.strides[0], QImage.Format.Format_BGR888
        ).copy()  # Copiar: o OpenCV reutiliza a memória do quadro seguinte.
        self.pixmap = QPixmap.fromImage(image)
        self.live = True
        self.update()

    def show_placeholder(self, message: str):
        self.pixmap = QPixmap()
        self.live = False
        self.message = message
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 13, 13)
        painter.setClipPath(path)
        painter.fillRect(rect, QColor("#e0ecef"))

        if not self.pixmap.isNull():
            # KeepAspectRatio: não recorta as mãos, importantes para Libras.
            width, height = self.width(), self.height()
            ratio = min(width / self.pixmap.width(), height / self.pixmap.height())
            display_w = self.pixmap.width() * ratio
            display_h = self.pixmap.height() * ratio
            target = QRectF((width - display_w) / 2, (height - display_h) / 2,
                            display_w, display_h)
            painter.fillRect(rect, QColor("#142f37"))
            painter.drawPixmap(target, self.pixmap, QRectF(self.pixmap.rect()))
        else:
            painter.setPen(QColor(C["muted"]))
            painter.setFont(QFont("Segoe UI", 13))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.message)

        if self.live:
            badge = QRectF(self.width() - 134, 12, 122, 34)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(5, 67, 76, 225))
            painter.drawRoundedRect(badge, 16, 16)
            painter.setPen(QColor("#ffffff"))
            font = QFont("Segoe UI", 10)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, "●  AO VIVO")
        painter.end()


class PonteWindow(QMainWindow):
    """Controla câmera e interface. Tradução/voz continuam em demonstração."""

    EXEMPLOS = ["Olá, tudo bem?", "Eu quero água.", "Obrigado.", "Bom dia!", "Preciso de ajuda."]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PONTE — Tradutor de Libras com IA (Interface)")
        self.setWindowIcon(QIcon(str(ASSETS_DIR / "ponte_icon.png")))
        self.setMinimumSize(1050, 720)
        self.resize(1390, 820)
        self.running = False
        self.example_index = 0
        self.history: list[tuple[str, str]] = []
        self.camera_index = 0  # Mesmo índice de teste_camera.py; pode mudar em Configurações.
        self.camera_capture = None
        self.failed_frames = 0
        self.camera_timer = QTimer(self)
        self.camera_timer.setInterval(40)  # Aproximadamente 25 quadros por segundo.
        self.camera_timer.timeout.connect(self._update_camera_frame)
        self._build_ui()
        self._refresh_history()

    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        all_layout = QVBoxLayout(root)
        all_layout.setContentsMargins(20, 18, 20, 18)
        all_layout.setSpacing(16)

        # CABEÇALHO ---------------------------------------------------------
        header = QFrame()
        header.setObjectName("header")
        header_row = QHBoxLayout(header)
        header_row.setContentsMargins(6, 0, 6, 0)
        header_row.setSpacing(20)

        logo = QLabel()
        logo.setPixmap(QPixmap(str(ASSETS_DIR / "ponte_icon.png")).scaled(
            62, 62, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
        ))
        header_row.addWidget(logo)
        brand = QWidget()
        brand_col = QVBoxLayout(brand)
        brand_col.setContentsMargins(0, 0, 0, 0)
        brand_col.setSpacing(0)
        brand_col.addWidget(text_label("PONTE", 28, True, C["teal"]))
        brand_col.addWidget(text_label("Tradutor de Libras com IA", 12, False, C["text"]))
        header_row.addWidget(brand)
        header_row.addStretch(1)
        camera_pill, self.camera_status_text = status_pill("◉", "Câmera: desligada")
        ai_pill, _ = status_pill("◇", "IA: desconectada")
        voice_pill, _ = status_pill("♪", "Voz: desconectada")
        header_row.addWidget(camera_pill)
        header_row.addWidget(ai_pill)
        header_row.addWidget(voice_pill)
        all_layout.addWidget(header)

        # CONTEÚDO: DIVISÃO ESQUERDA/DIREITA -------------------------------
        columns = QHBoxLayout()
        columns.setSpacing(15)
        all_layout.addLayout(columns, 1)

        # LADO ESQUERDO: PRÉVIA DE CÂMERA ---------------------------------
        camera_card, camera_col = card_layout(spacing=12)
        camera_col.addWidget(section_title("▣  Pré-visualização da câmera"))
        self.camera = CameraPreview()
        camera_col.addWidget(self.camera, 1)
        self.camera_info = text_label("●  Câmera desligada — clique em Iniciar", 10, False, C["muted"])
        camera_col.addWidget(self.camera_info)
        columns.addWidget(camera_card, 47)

        # LADO DIREITO: TRADUÇÃO, ÁUDIO, HISTÓRICO -------------------------
        right = QVBoxLayout()
        right.setSpacing(14)
        columns.addLayout(right, 53)

        translation_card, translation_col = card_layout(0, (0, 0, 0, 0))
        translation_head = QFrame()
        translation_head.setObjectName("translationHead")
        head_row = QHBoxLayout(translation_head)
        head_row.setContentsMargins(22, 13, 20, 13)
        head_row.addWidget(text_label("Tradução", 18, True, "white"))
        head_row.addStretch()
        head_row.addWidget(text_label("MODO DEMONSTRAÇÃO", 9, True, "#d6fbf4"))
        translation_col.addWidget(translation_head)

        translation_area = QVBoxLayout()
        translation_area.setContentsMargins(22, 20, 22, 16)
        translation_area.setSpacing(8)
        self.translation_text = text_label("Aguardando tradução...", 24, True, C["navy"])
        self.translation_text.setWordWrap(True)
        self.translation_text.setMinimumHeight(60)
        translation_area.addWidget(self.translation_text)
        self.translation_hint = text_label("Nenhum vídeo foi enviado à IA.", 10, False, C["muted"])
        translation_area.addWidget(self.translation_hint)
        control_row = QHBoxLayout()
        control_row.addStretch()
        self.simulate_button = QPushButton("▶  Simular tradução")
        self.simulate_button.setObjectName("simulate")
        self.simulate_button.setEnabled(False)
        self.simulate_button.clicked.connect(self.simulate_translation)
        control_row.addWidget(self.simulate_button)
        translation_area.addLayout(control_row)
        translation_col.addLayout(translation_area)
        right.addWidget(translation_card, 4)

        audio_card, audio_row_holder = card_layout(spacing=6, margins=(18, 14, 18, 14))
        audio_row = QHBoxLayout()
        audio_row.setSpacing(12)
        audio_icon = text_label("♪", 26, True, C["teal"])
        audio_row.addWidget(audio_icon)
        audio_info = QVBoxLayout()
        audio_info.setSpacing(2)
        audio_info.addWidget(text_label("Saída de voz", 15, True, C["navy"]))
        audio_info.addWidget(text_label("Reprodução de texto em áudio", 10, False, C["muted"]))
        audio_row.addLayout(audio_info)
        audio_row.addStretch()
        self.voice_button = QPushButton("▶  Reproduzir")
        self.voice_button.clicked.connect(self.reproduce)
        audio_row.addWidget(self.voice_button)
        audio_row_holder.addLayout(audio_row)
        right.addWidget(audio_card, 1)

        info_row = QHBoxLayout()
        info_row.setSpacing(14)
        right.addLayout(info_row, 4)

        history_card, history_col = card_layout(spacing=10)
        history_col.addWidget(section_title("◷  Histórico", "Últimas demonstrações"))
        self.history_container = QVBoxLayout()
        self.history_container.setSpacing(7)
        history_col.addLayout(self.history_container)
        history_col.addStretch()
        info_row.addWidget(history_card, 65)

        time_card, time_col = card_layout(spacing=12)
        time_col.addWidget(section_title("◴  Tempo de resposta"))
        time_frame = QFrame()
        time_frame.setObjectName("timeBox")
        time_layout = QVBoxLayout(time_frame)
        time_layout.setContentsMargins(12, 12, 12, 12)
        self.time_label = text_label("—", 27, True, C["teal"])
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        time_layout.addWidget(self.time_label)
        time_col.addWidget(time_frame)
        time_col.addStretch()
        time_col.addWidget(text_label("Somente ilustrativo", 9, False, C["muted"]))
        info_row.addWidget(time_card, 35)

        # AÇÕES PRINCIPAIS -------------------------------------------------
        controls = QFrame()
        controls.setObjectName("bottomBar")
        controls_row = QHBoxLayout(controls)
        controls_row.setContentsMargins(14, 12, 14, 12)
        controls_row.setSpacing(12)

        self.start_button = QPushButton("▶  Iniciar")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.start_camera)
        self.pause_button = QPushButton("Ⅱ  Pausar")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_camera)
        self.clear_button = QPushButton("⌫  Limpar")
        self.clear_button.clicked.connect(self.clear_demo)
        self.settings_button = QPushButton("⚙  Configurações")
        self.settings_button.clicked.connect(self.show_settings)
        for b, stretch in [
            (self.start_button, 2),
            (self.pause_button, 2),
            (self.clear_button, 2),
            (self.settings_button, 2),
        ]:
            b.setMinimumHeight(51)
            controls_row.addWidget(b, stretch)
        all_layout.addWidget(controls)

        notice = text_label(
            "Câmera real disponível • A tradução e a saída de voz ainda são demonstrações.",
            9, False, C["muted"]
        )
        notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        all_layout.addWidget(notice)

    def _refresh_history(self):
        # Remove widgets antigos; cria linhas a partir do histórico atual.
        while self.history_container.count():
            item = self.history_container.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        if not self.history:
            empty = text_label("As traduções de demonstração aparecerão aqui.", 10, False, C["muted"])
            empty.setWordWrap(True)
            self.history_container.addWidget(empty)
            return
        for phrase, moment in self.history[:3]:
            row = QFrame()
            row.setObjectName("historyItem")
            line = QHBoxLayout(row)
            line.setContentsMargins(12, 9, 10, 9)
            line.setSpacing(8)
            txt = text_label(phrase, 11, False, C["text"])
            txt.setWordWrap(True)
            line.addWidget(txt, 1)
            line.addWidget(text_label(moment, 9, False, C["muted"]))
            self.history_container.addWidget(row)

    def start_camera(self):
        """Abre a webcam do Windows, sem usar cv2.imshow()."""
        if self.running:
            return

        backend = cv2.CAP_DSHOW if sys.platform.startswith("win") else cv2.CAP_ANY
        capture = cv2.VideoCapture(self.camera_index, backend)
        if not capture.isOpened():
            capture.release()
            capture = cv2.VideoCapture(self.camera_index)
        if not capture.isOpened():
            capture.release()
            self.camera_status_text.setText("Câmera: indisponível")
            self.camera_info.setText("●  Não foi possível abrir a câmera")
            QMessageBox.warning(
                self, "Câmera não encontrada",
                f"Não consegui abrir a câmera {self.camera_index}.\n\n"
                "Verifique se a câmera conectada do celular está ativa no Windows, "
                "feche outros programas que possam estar usando-a ou escolha "
                "outro número em Configurações."
            )
            return

        self.camera_capture = capture
        self.failed_frames = 0
        self.running = True
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.simulate_button.setEnabled(True)
        self.camera_status_text.setText("Câmera: conectada")
        self.camera_info.setText("●  Câmera ligada — aguardando imagem...")
        self.translation_hint.setText("Câmera ativa. A tradução da IA ainda não está conectada.")
        self.camera_timer.start()

    def _update_camera_frame(self):
        """Lê um quadro por ciclo do Qt; não abre uma segunda janela."""
        if not self.running or self.camera_capture is None:
            return
        try:
            success, frame = self.camera_capture.read()
        except cv2.error:
            success, frame = False, None

        if not success or frame is None:
            self.failed_frames += 1
            if self.failed_frames >= 12:
                self.pause_camera()
                self.camera_status_text.setText("Câmera: sinal perdido")
                self.camera_info.setText("●  Conexão com a câmera interrompida")
                QMessageBox.warning(
                    self, "Conexão interrompida",
                    "Não estou recebendo imagem da câmera.\n"
                    "Confira a conexão com o celular e clique em Iniciar novamente."
                )
            return

        self.failed_frames = 0
        self.camera.show_frame(frame)
        self.camera_info.setText("●  Transmissão ao vivo — webcam conectada")

    def _release_camera(self):
        """Libera a câmera para outros programas e para o Windows."""
        self.camera_timer.stop()
        if self.camera_capture is not None:
            self.camera_capture.release()
            self.camera_capture = None
        self.running = False

    def pause_camera(self):
        self._release_camera()
        self.camera.show_placeholder("Câmera pausada\nClique em Iniciar para retomar.")
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.simulate_button.setEnabled(False)
        self.camera_status_text.setText("Câmera: pausada")
        self.camera_info.setText("●  Captura pausada — câmera liberada")
        self.translation_hint.setText("Captura pausada. A IA ainda não está conectada.")

    def simulate_translation(self):
        if not self.running:
            return
        phrase = self.EXEMPLOS[self.example_index % len(self.EXEMPLOS)]
        self.example_index += 1
        self.translation_text.setText(phrase)
        self.translation_hint.setText("Exemplo simulado • não reconhecido pela IA")
        self.time_label.setText("2,1 s")
        self.history.insert(0, (phrase, datetime.now().strftime("%H:%M")))
        self._refresh_history()

    def clear_demo(self):
        self.example_index = 0
        self.history.clear()
        self.translation_text.setText("Aguardando tradução...")
        self.translation_hint.setText(
            "Use “Simular tradução” para testar a interface." if self.running
            else "Nenhum vídeo foi enviado à IA."
        )
        self.time_label.setText("—")
        self._refresh_history()

    def reproduce(self):
        QMessageBox.information(
            self, "Saída de voz — próxima etapa",
            "Este botão já está preparado na interface.\n\n"
            "Na integração, ele chamará o método speak() do voice_service.py.\n"
            "Por enquanto, não reproduz áudio."
        )

    def show_settings(self):
        """Permite selecionar o índice do dispositivo (0, 1, 2...)."""
        if self.running:
            QMessageBox.information(self, "Configurações", "Pause a câmera antes de trocar o dispositivo.")
            return
        index, confirmed = QInputDialog.getInt(
            self, "Configurações da câmera",
            "Número da câmera (0 a 9):", self.camera_index, 0, 9
        )
        if confirmed:
            self.camera_index = index
            self.camera_status_text.setText(f"Câmera: dispositivo {index}")
            self.camera_info.setText(f"●  Dispositivo {index} selecionado — clique em Iniciar")
            self.camera.show_placeholder("Câmera desligada\nClique em Iniciar para exibir a imagem.")

    def closeEvent(self, event):
        self._release_camera()
        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    window = PonteWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
