
import numpy as np
import sounddevice as sd
from openwakeword.model import Model


class WakeWordDetector:
    def __init__(self, model_name="alexa"):
        self.model = Model(
            wakeword_models=[model_name],
            inference_framework="onnx"
        )

        self.sample_rate = 16000
        self.frame_size = 1280

    def listen(self, threshold=0.5):
        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=self.frame_size
        ) as stream:
            while True:
                audio, _ = stream.read(self.frame_size)
                audio = np.squeeze(audio)

                predictions = self.model.predict(audio)

                if not predictions:
                    continue

                confidence = max(
                    predictions.values(),
                    default=0
                )

                if confidence >= threshold:
                    self.model.reset()
                    return True