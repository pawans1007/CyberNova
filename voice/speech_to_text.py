
import json
from pathlib import Path

import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer


class SpeechToText:
    def __init__(
        self,
        sample_rate=16000,
        model_path=None
    ):
        self.sample_rate = sample_rate

        if model_path is None:
            project_root = Path(__file__).resolve().parent.parent
            model_path = project_root / "vosk-model"

        self.model_path = Path(model_path)

        if not self.model_path.is_dir():
            raise FileNotFoundError(
                f"Vosk model folder not found: {self.model_path}"
            )

        self.model = Model(str(self.model_path))

    def record(self, duration=5):
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        return audio.flatten()

    def transcribe(self, audio):
        recognizer = KaldiRecognizer(
            self.model,
            self.sample_rate
        )

        audio_bytes = np.asarray(
            audio,
            dtype=np.int16
        ).tobytes()

        recognizer.AcceptWaveform(audio_bytes)

        result = json.loads(recognizer.FinalResult())
        return result.get("text", "").strip()

    def listen_once(self, duration=5):
        audio = self.record(duration)
        return self.transcribe(audio)