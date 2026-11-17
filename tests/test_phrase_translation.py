import json
import os
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtWidgets import QApplication
from image_tools import VisualDialog


class FakePage:
    def __init__(self, response):
        self.response = response
        self.scripts = []

    def runJavaScript(self, script, callback):
        self.scripts.append(script)
        if script.startswith('typeof ponteTraduzir'):
            callback(True)
        else:
            callback(json.dumps(self.response))


class FakePlayer:
    def __init__(self, response):
        self._page = FakePage(response)

    def page(self):
        return self._page


class PhraseTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def make_dialog(self, response):
        with patch.object(VisualDialog, 'start_player'):
            dialog = VisualDialog()
        dialog.player = FakePlayer(response)
        dialog.player_ready = True
        return dialog

    def test_phrase_is_encoded_as_data_and_result_is_shown(self):
        dialog = self.make_dialog({'estado': 'pronto', 'glosa': 'BOM_DIA VOCÊ'})
        phrase = 'Bom dia, "como você está?"'
        dialog.phrase_input.setText(phrase)
        dialog.translate_phrase()
        self.assertIn(json.dumps(phrase, ensure_ascii=True), dialog.player.page().scripts[0])
        self.assertIn('BOM_DIA VOCÊ', dialog.phrase_status.text())
        self.assertFalse(dialog.translation_in_progress)
        dialog.close()

    def test_empty_phrase_does_not_send(self):
        dialog = self.make_dialog({'estado': 'pronto', 'glosa': 'X'})
        dialog.phrase_input.setText('  ')
        dialog.translate_phrase()
        self.assertFalse(dialog.player.page().scripts)
        self.assertIn('Digite', dialog.phrase_status.text())
        dialog.close()

    def test_failed_translation_enables_retry(self):
        dialog = self.make_dialog({'estado': 'erro'})
        dialog.phrase_input.setText('Bom dia')
        dialog.translate_phrase()
        self.assertIn('Não foi possível', dialog.phrase_status.text())
        self.assertTrue(dialog.phrase_button.isEnabled())
        self.assertFalse(dialog.translation_in_progress)
        dialog.close()


if __name__ == '__main__':
    unittest.main()
