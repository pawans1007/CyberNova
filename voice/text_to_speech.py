
import pyttsx3
import threading


class TextToSpeech:
    def __init__(self, rate=175, volume=1.0):
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)
        self.lock = threading.Lock()

    def speak(self, text):
        if not text:
            return

        with self.lock:
            self.engine.say(str(text))
            self.engine.runAndWait()

    def stop(self):
        with self.lock:
            self.engine.stop()