import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import QApplication

from image_tools import ImagePreview, VisualDialog


class VisualLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        with patch.object(VisualDialog, 'start_player'):
            self.dialog = VisualDialog()
        self.dialog.show()
        self.app.processEvents()

    def tearDown(self):
        self.dialog.close()
        self.app.processEvents()

    def test_tabs_and_wide_layout(self):
        self.assertEqual([self.dialog.tabs.tabText(i) for i in range(self.dialog.tabs.count())],
                         ['Imagens → português', 'Frase → Libras'])
        self.dialog.resize(950, 650)
        self.app.processEvents()
        self.assertEqual(self.dialog.image_splitter.orientation(), Qt.Orientation.Horizontal)
        self.assertEqual(self.dialog.result_splitter.orientation(), Qt.Orientation.Vertical)
        self.assertFalse(self.dialog.image_splitter.childrenCollapsible())

    def test_narrow_layout_scrolls_to_result(self):
        self.dialog.resize(600, 450)
        self.app.processEvents()
        self.assertEqual(self.dialog.image_splitter.orientation(), Qt.Orientation.Vertical)
        self.assertGreater(self.dialog.image_scroll.verticalScrollBar().maximum(), 0)
        self.assertLess(self.dialog.images.geometry().bottom(), self.dialog.add_button.geometry().top())
        self.assertLess(self.dialog.add_button.geometry().bottom(), self.dialog.remove_button.geometry().top())
        self.dialog.image_scroll.ensureWidgetVisible(self.dialog.analysis)
        self.app.processEvents()
        self.assertGreater(self.dialog.image_scroll.verticalScrollBar().value(), 0)
        self.assertGreater(self.dialog.analysis.width(), 0)
        self.assertGreater(self.dialog.analysis.height(), 0)

    def test_preview_rescales_without_cropping(self):
        preview = ImagePreview()
        preview.resize(300, 180)
        preview.show()
        self.app.processEvents()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'imagem.png'
            original = QPixmap(800, 400)
            original.fill(QColor('blue'))
            self.assertTrue(original.save(str(path)))
            preview.show_image(str(path))
            self.assertAlmostEqual(preview.pixmap().width() / preview.pixmap().height(), 2, places=1)
            previous_width = preview.pixmap().width()
            preview.resize(180, 150)
            self.app.processEvents()
            self.assertLess(preview.pixmap().width(), previous_width)
            self.assertLessEqual(preview.pixmap().width(), preview.width())
            self.assertLessEqual(preview.pixmap().height(), preview.height())
        preview.close()


if __name__ == '__main__':
    unittest.main()
