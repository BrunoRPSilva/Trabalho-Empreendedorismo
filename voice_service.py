import pyttsx3

class VoiceService:
    def __init__(self):
        self.engine = pyttsx3.init()
        # Tenta buscar uma voz em português instalada no Windows
        voices = self.engine.getProperty('voices')
        for voice in voices:
            if "brazil" in voice.name.lower() or "portuguese" in voice.name.lower():
                self.engine.setProperty('voice', voice.id)
                break

    def speak(self, text):
        if text and "Erro" not in text:
            self.engine.say(text)
            self.engine.runAndWait()