
from PySide6.QtCore import QThread, Signal

from voice.speech_to_text import SpeechToText
from voice.text_to_speech import TextToSpeech


class VoiceWorker(QThread):
    transcript_ready = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, duration=5):
        super().__init__()
        self.duration = duration
        self.stt = SpeechToText()

    def run(self):
        try:
            text = self.stt.listen_once(self.duration)

            if text.strip():
                self.transcript_ready.emit(text)
            else:
                self.error_occurred.emit(
                    "No speech was detected."
                )

        except Exception as error:
            self.error_occurred.emit(str(error))


class VoiceService:
    def __init__(self):
        self.tts = TextToSpeech()

    def speak(self, text):
        self.tts.speak(text)