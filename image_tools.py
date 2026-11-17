"""Consultas visuais de Libras na interface desktop."""
from pathlib import Path
import json
from PySide6.QtCore import QEvent, Qt, QThread, QTimer, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSizePolicy, QSplitter,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)


class ImageAnalysisWorker(QThread):
    result = Signal(str)
    failed = Signal(str)

    def __init__(self, paths, parent):
        super().__init__(parent)
        self.paths = paths

    def run(self):
        try:
            from ai_service import AIService
            self.result.emit(AIService().translate_sign_images(self.paths))
        except Exception as exc:
            self.failed.emit(str(exc))


class ImagePreview(QLabel):
    """Redimensiona a imagem original conforme o espaço disponível."""

    def __init__(self):
        super().__init__('Prévia da imagem selecionada')
        self.original = QPixmap()
        self.setObjectName('imagePanel')
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(120, 100)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)

    def show_image(self, path):
        self.original = QPixmap(path)
        if self.original.isNull():
            self.setText('Não foi possível carregar esta imagem.')
        else:
            self._scale_image()

    def reset_image(self):
        self.original = QPixmap()
        self.clear()
        self.setText('Prévia da imagem selecionada')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._scale_image()

    def _scale_image(self):
        if not self.original.isNull():
            available = self.contentsRect().size()
            if available.width() > 8 and available.height() > 8:
                self.setPixmap(self.original.scaled(
                    available.width() - 8, available.height() - 8,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))


class VisualDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('PONTE — Consultas visuais')
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        screen = QGuiApplication.primaryScreen()
        available = screen.availableGeometry() if screen else None
        self.resize(min(900, available.width() - 50) if available else 900,
                    min(760, available.height() - 60) if available else 760)
        self.setMinimumSize(480, 360)
        self.setStyleSheet('''
            QDialog { background: #f2f7fa; }
            QWidget { color: #133747; font-family: "Segoe UI"; font-size: 13px; }
            QLabel { background: transparent; color: #355c66; }
            QLabel#visualTitle { color: #083f4d; font-size: 23px; font-weight: 700; }
            QLabel#visualSubtitle { color: #637c88; font-size: 13px; }
            QTabWidget::pane { background: #ffffff; border: 1px solid #d7e4e9; border-radius: 14px; top: -1px; }
            QTabBar::tab { background: #e6eff2; color: #476a72; border: 1px solid #d7e4e9; border-bottom: 0; border-top-left-radius: 10px; border-top-right-radius: 10px; padding: 12px 20px; margin-right: 5px; font-weight: 600; }
            QTabBar::tab:selected { background: white; color: #006875; }
            QLineEdit, QListWidget, QTextEdit { background: #ffffff; color: #133747; border: 1px solid #c5d9dd; border-radius: 9px; padding: 9px; selection-background-color: #a8dcd6; }
            QListWidget::item:selected { background: #d5f1ec; color: #064c51; }
            QLineEdit:focus { border: 2px solid #008675; }
            QScrollArea { background: transparent; border: none; }
            QWidget#imageContent, QWidget#phraseContent { background: #ffffff; }
            QScrollBar:vertical { background: #edf4f4; width: 12px; border-radius: 6px; }
            QScrollBar::handle:vertical { background: #8fb9b3; min-height: 28px; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background: #008675; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QSplitter::handle { background: #c5dcda; border-radius: 3px; }
            QSplitter::handle:hover { background: #008675; }
            QLabel#imagePanel { background: #edf6f6; color: #637c88; border: 1px solid #d7eae8; border-radius: 12px; }
            QLabel#notice { color: #476a72; background: #eef7f6; border-radius: 8px; padding: 10px; }
            QPushButton { background: #f7fbfc; color: #07535d; border: 1px solid #bad3d7; border-radius: 9px; padding: 10px 15px; font-weight: 600; }
            QPushButton:hover { background: #e3f4f1; }
            QPushButton:disabled { color: #98adb2; background: #edf2f3; border-color: #dce6e8; }
            QPushButton#visualPrimary { background: #008675; color: white; border-color: #008675; }
            QPushButton#visualPrimary:hover { background: #006f64; }
            QPushButton#visualPrimary:disabled { background: #a8c9c2; color: #ecf5f3; }
        ''')
        self.worker = None
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)
        title = QLabel('Imagens e sinais')
        title.setObjectName('visualTitle')
        root.addWidget(title)
        subtitle = QLabel('Explore sinais e consulte imagens de Libras')
        subtitle.setObjectName('visualSubtitle')
        root.addWidget(subtitle)
        self.tabs = QTabWidget()
        tabs = self.tabs
        root.addWidget(tabs)

        self.image_scroll = QScrollArea()
        self.image_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.image_scroll.setWidgetResizable(True)
        self.image_scroll.setMinimumSize(0, 0)
        self.image_scroll.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        self.image_scroll.viewport().installEventFilter(self)
        self.image_content = QWidget()
        self.image_content.setObjectName('imageContent')
        self.image_content.setMinimumWidth(390)
        self.image_scroll.setWidget(self.image_content)
        layout = QVBoxLayout(self.image_content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        instructions = QLabel('Selecione de 1 a 8 imagens e arraste os arquivos para ordenar. Ajuste a lista, a prévia e o resultado arrastando as divisórias.')
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        self.image_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.image_splitter.setChildrenCollapsible(False)
        self.image_splitter.setHandleWidth(9)
        self.image_splitter.setToolTip('Arraste a divisória para ajustar o tamanho das áreas.')
        layout.addWidget(self.image_splitter, 1)

        selection = QWidget()
        selection.setMinimumSize(180, 270)
        selection_layout = QVBoxLayout(selection)
        selection_layout.setContentsMargins(0, 0, 0, 0)
        selection_layout.setSpacing(8)
        selection_title = QLabel('Imagens selecionadas')
        selection_layout.addWidget(selection_title)
        self.images = QListWidget()
        self.images.setMinimumHeight(70)
        self.images.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.images.currentItemChanged.connect(self.preview_image)
        selection_layout.addWidget(self.images, 1)
        self.add_button = QPushButton('Adicionar imagens')
        self.add_button.clicked.connect(self.add_images)
        self.remove_button = QPushButton('Remover selecionada')
        self.remove_button.clicked.connect(self.remove_image)
        self.analyze_button = QPushButton('Analisar imagens com IA')
        self.analyze_button.setObjectName('visualPrimary')
        self.analyze_button.clicked.connect(self.analyze_images)
        for button in (self.add_button, self.remove_button, self.analyze_button):
            selection_layout.addWidget(button)
        self.image_splitter.addWidget(selection)

        self.result_splitter = QSplitter(Qt.Orientation.Vertical)
        self.result_splitter.setChildrenCollapsible(False)
        self.result_splitter.setHandleWidth(9)
        self.result_splitter.setToolTip('Arraste a divisória para ajustar a prévia e o resultado.')
        self.preview = ImagePreview()
        self.result_splitter.addWidget(self.preview)
        result_area = QWidget()
        result_area.setMinimumHeight(130)
        result_layout = QVBoxLayout(result_area)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_layout.setSpacing(8)
        self.analysis_status = QLabel('As imagens selecionadas serão enviadas ao Gemini.')
        self.analysis_status.setObjectName('notice')
        self.analysis_status.setWordWrap(True)
        self.analysis_status.setTextFormat(Qt.TextFormat.PlainText)
        result_layout.addWidget(self.analysis_status)
        self.analysis = QTextEdit()
        self.analysis.setMinimumHeight(65)
        self.analysis.setReadOnly(True)
        self.analysis.setPlaceholderText('Os sinais identificados e a possível tradução aparecerão aqui.')
        result_layout.addWidget(self.analysis, 1)
        self.result_splitter.addWidget(result_area)
        self.result_splitter.setStretchFactor(0, 1)
        self.result_splitter.setStretchFactor(1, 1)
        self.image_splitter.addWidget(self.result_splitter)
        self.image_splitter.setStretchFactor(0, 2)
        self.image_splitter.setStretchFactor(1, 3)
        tabs.addTab(self.image_scroll, 'Imagens → português')

        self.phrase_tab = QScrollArea()
        self.phrase_tab.setWidgetResizable(True)
        self.phrase_tab.setFrameShape(QFrame.Shape.NoFrame)
        self.phrase_tab.setMinimumSize(0, 0)
        self.phrase_tab.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
        phrase_content = QWidget()
        phrase_content.setObjectName('phraseContent')
        phrase_content.setMinimumSize(390, 430)
        self.phrase_tab.setWidget(phrase_content)
        phrase_layout = QVBoxLayout(phrase_content)
        phrase_layout.setContentsMargins(20, 20, 20, 20)
        phrase_layout.setSpacing(10)
        phrase_help = QLabel('Digite uma frase em português. O avatar do VLibras apresenta a tradução automática em Libras. Na primeira abertura, escolha no avatar se deseja permitir dados anônimos de uso.')
        phrase_help.setWordWrap(True)
        phrase_layout.addWidget(phrase_help)
        phrase_row = QHBoxLayout()
        self.phrase_input = QLineEdit()
        self.phrase_input.setMaxLength(500)
        self.phrase_input.setPlaceholderText('Ex.: Bom dia, como você está?')
        self.phrase_input.returnPressed.connect(self.translate_phrase)
        phrase_row.addWidget(self.phrase_input, 1)
        self.phrase_button = QPushButton('Traduzir em Libras')
        self.phrase_button.setObjectName('visualPrimary')
        self.phrase_button.setEnabled(False)
        self.phrase_button.clicked.connect(self.translate_phrase)
        phrase_row.addWidget(self.phrase_button)
        phrase_layout.addLayout(phrase_row)
        self.phrase_status = QLabel('O texto será enviado ao serviço público VLibras. É necessário acesso à internet.')
        self.phrase_status.setTextFormat(Qt.TextFormat.PlainText)
        self.phrase_status.setObjectName('notice')
        self.phrase_status.setWordWrap(True)
        phrase_layout.addWidget(self.phrase_status)
        self.player_layout = QVBoxLayout()
        phrase_layout.addLayout(self.player_layout, 1)
        phrase_footer = QHBoxLayout()
        self.reload_player_button = QPushButton('Recarregar avatar')
        self.reload_player_button.clicked.connect(self.reload_player)
        phrase_footer.addWidget(self.reload_player_button)
        dictionary_button = QPushButton('Dicionário brasileiro de Libras')
        dictionary_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl('https://wiki.vlibras.gov.br/')))
        phrase_footer.addWidget(dictionary_button)
        phrase_layout.addLayout(phrase_footer)
        tabs.addTab(self.phrase_tab, 'Frase → Libras')
        self.player = None
        self.player_started = False
        self.player_ready = False
        self.translation_in_progress = False
        self.player_polls = 0
        self.player_timer = QTimer(self)
        self.player_timer.setInterval(1500)
        self.player_timer.timeout.connect(self.check_player)
        self.translation_timer = QTimer(self)
        self.translation_timer.setInterval(800)
        self.translation_timer.timeout.connect(self.check_translation)
        self.translation_polls = 0

        tabs.currentChanged.connect(self.tab_changed)
        QTimer.singleShot(0, self.adjust_image_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'image_splitter'):
            self.adjust_image_layout()

    def eventFilter(self, watched, event):
        if (hasattr(self, 'image_scroll') and watched is self.image_scroll.viewport()
                and event.type() == QEvent.Type.Resize and hasattr(self, 'image_splitter')):
            QTimer.singleShot(0, self.adjust_image_layout)
        return super().eventFilter(watched, event)

    def adjust_image_layout(self):
        # Em janelas largas, lista e resultado ficam lado a lado; nas estreitas,
        # ficam empilhados e a rolagem evita que os controles saiam da tela.
        orientation = Qt.Orientation.Horizontal if self.width() >= 860 else Qt.Orientation.Vertical
        if self.image_splitter.orientation() != orientation:
            self.image_splitter.setOrientation(orientation)
            self.image_splitter.setSizes([260, 420])
        minimum = 370 if orientation == Qt.Orientation.Horizontal else 630
        maximum = max(minimum, self.image_scroll.viewport().height())
        if (self.image_content.minimumHeight() != minimum
                or self.image_content.maximumHeight() != maximum):
            self.image_content.setMinimumHeight(0)
            self.image_content.setMaximumHeight(maximum)
            self.image_content.setMinimumHeight(minimum)

    def tab_changed(self, _index):
        if self.tabs.currentWidget() is self.phrase_tab and not self.player_started:
            self.start_player()

    def start_player(self):
        self.player_started = True
        try:
            from PySide6.QtWebEngineCore import QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            self.phrase_status.setText('O componente de visualização não está instalado. Feche o PONTE e inicie pelo arquivo Iniciar_PONTE.bat para instalar as dependências.')
            self.reload_player_button.setEnabled(False)
            return
        self.player = QWebEngineView(self)
        self.player.setMinimumHeight(240)
        self.player.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
        self.player.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.player.loadFinished.connect(self.player_load_finished)
        self.player_layout.addWidget(self.player)
        self.reload_player()

    def reload_player(self):
        if self.player is None:
            return
        self.player_timer.stop()
        self.translation_timer.stop()
        self.player_polls = 0
        self.player_ready = False
        self.translation_in_progress = False
        self.phrase_button.setEnabled(False)
        self.phrase_status.setText('Carregando o avatar VLibras. A primeira abertura pode demorar; mantenha a internet conectada.')
        page = Path(__file__).resolve().parent / 'vlibras_view.html'
        url = QUrl.fromLocalFile(str(page))
        if self.player.url() == url:
            self.player.reload()
        else:
            self.player.setUrl(url)

    def player_load_finished(self, ok):
        if not ok:
            self.phrase_status.setText('Não foi possível abrir o avatar. Clique em Recarregar avatar.')
            return
        self.player_timer.start()
        self.check_player()

    def check_player(self):
        if self.player is None:
            return
        self.player_polls += 1
        self.player.page().runJavaScript("typeof pontePlayerStatus === 'function' ? pontePlayerStatus() : 'carregando'", self.player_status_changed)
        if self.player_polls >= 80:
            self.player_timer.stop()
            if not self.player_ready:
                self.phrase_status.setText('O avatar está demorando para abrir. Confira a internet e clique em Recarregar avatar.')

    def player_status_changed(self, status):
        if status == 'pronto':
            self.player_ready = True
            self.player_timer.stop()
            self.phrase_button.setEnabled(True)
            self.phrase_status.setText('Avatar pronto. O texto será enviado ao VLibras para tradução automática.')
        elif status == 'erro':
            self.player_timer.stop()
            self.phrase_status.setText('Não foi possível conectar ao VLibras. Confira a internet e clique em Recarregar avatar.')
        elif status == 'carregando-avatar':
            self.phrase_status.setText('Conectado ao VLibras. Carregando o avatar; isso pode demorar na primeira vez.')

    def translate_phrase(self):
        phrase = self.phrase_input.text().strip()
        if self.translation_in_progress:
            return
        if not phrase:
            self.phrase_status.setText('Digite uma frase em português para traduzir.')
            return
        if not self.player_ready or self.player is None:
            self.phrase_status.setText('Aguarde o avatar ficar pronto antes de traduzir.')
            return
        self.phrase_button.setEnabled(False)
        self.translation_in_progress = True
        self.phrase_status.setText('Traduzindo a frase com o VLibras…')
        script = 'typeof ponteTraduzir === "function" && ponteTraduzir(' + json.dumps(phrase, ensure_ascii=True) + ')'
        self.player.page().runJavaScript(script, self.phrase_submitted)

    def phrase_submitted(self, accepted):
        if accepted:
            self.translation_polls = 0
            self.translation_timer.start()
            self.check_translation()
        else:
            self.translation_in_progress = False
            self.player_ready = False
            self.phrase_button.setEnabled(False)
            self.phrase_status.setText('O avatar deixou de responder. Clique em Recarregar avatar.')

    def check_translation(self):
        if self.player is None:
            return
        self.translation_polls += 1
        self.player.page().runJavaScript('JSON.stringify(window.ponteResultado || {estado: "erro"})', self.translation_status_changed)
        if self.translation_polls >= 40:
            self.translation_timer.stop()
            self.translation_in_progress = False
            self.phrase_button.setEnabled(self.player_ready)
            self.phrase_status.setText('A tradução está demorando. Você pode tentar novamente.')

    def translation_status_changed(self, result):
        if not self.translation_in_progress:
            return
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (TypeError, ValueError):
                return
        if not isinstance(result, dict):
            return
        state = result.get('estado')
        if state == 'pronto':
            self.translation_timer.stop()
            self.translation_in_progress = False
            self.phrase_button.setEnabled(True)
            self.phrase_status.setText('Tradução recebida. Acompanhe o avatar; a glosa gerada é: ' + result.get('glosa', ''))
        elif state == 'erro':
            self.translation_timer.stop()
            self.translation_in_progress = False
            self.phrase_button.setEnabled(True)
            self.phrase_status.setText('Não foi possível traduzir a frase agora. Verifique a conexão e tente novamente.')

    def add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(self, 'Selecione imagens na ordem desejada', '', 'Imagens (*.png *.jpg *.jpeg *.webp)')
        for path in paths:
            if self.images.count() >= 8:
                self.analysis_status.setText('Limite de 8 imagens; arraste os arquivos para ordenar.')
                break
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.ItemDataRole.UserRole, path)
            item.setToolTip(path)
            self.images.addItem(item)
        if self.images.count() and self.images.currentRow() < 0:
            self.images.setCurrentRow(0)

    def remove_image(self):
        row = self.images.currentRow()
        if row >= 0:
            self.images.takeItem(row)
        if not self.images.count():
            self.preview.reset_image()

    def preview_image(self, current, previous=None):
        if current:
            self.preview.show_image(current.data(Qt.ItemDataRole.UserRole))

    def analyze_images(self):
        if self.worker is not None:
            return
        paths = [self.images.item(i).data(Qt.ItemDataRole.UserRole) for i in range(self.images.count())]
        if not paths:
            self.analysis_status.setText('Selecione pelo menos uma imagem.')
            return
        self.analysis.clear()
        self.analysis_status.setText('Enviando imagens ao Gemini para análise…')
        self.worker = ImageAnalysisWorker(paths, self)
        self.worker.result.connect(self.show_analysis)
        self.worker.failed.connect(lambda message: self.analysis_status.setText('Falha na análise: ' + message))
        self.start_worker()

    def show_analysis(self, result):
        self.analysis.setPlainText(result)
        self.analysis_status.setText('Resultado experimental: confira os sinais em uma referência de Libras.')

    def start_worker(self):
        self.analyze_button.setEnabled(False)
        self.add_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def worker_finished(self):
        self.worker.deleteLater()
        self.worker = None
        for button in (self.analyze_button, self.add_button, self.remove_button):
            button.setEnabled(True)

    def reject(self):
        if self.worker is not None:
            self.analysis_status.setText('Aguarde a consulta terminar antes de fechar esta janela.')
            return
        super().reject()
