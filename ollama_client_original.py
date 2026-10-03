import ollama
from config import OLLAMA_HOST, OLLAMA_MODEL


class OllamaClient:
    def __init__(self, model=OLLAMA_MODEL, host=OLLAMA_HOST):
        self.model = model
        self.host = host
        self.client = ollama.Client(host=self.host)

    def generate(self, messages, num_predict=512):
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "num_predict": num_predict,
                },
            )

            return response["message"]["content"]

        except Exception as error:
            raise RuntimeError(
                f"Ollama generation failed: {error}"
            ) from error

    def stream(self, messages, num_predict=512):
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "num_predict": num_predict,
                },
            )

            for chunk in response:
                content = chunk.get(
                    "message", {}
                ).get("content", "")

                if content:
                    yield content

        except Exception as error:
            raise RuntimeError(
                f"Ollama streaming failed: {error}"
            ) from error

    def check_connection(self):
        try:
            self.client.list()
            return True, "Ollama is connected."

        except Exception as error:
            return False, str(error)

    def update_connection(self, host=None, model=None):
        new_host = (
            str(host).strip()
            if host is not None
            else self.host
        )

        new_model = (
            str(model).strip()
            if model is not None
            else self.model
        )

        if not new_host:
            raise ValueError(
                "Ollama host cannot be empty."
            )

        if not new_model:
            raise ValueError(
                "Ollama model cannot be empty."
            )

        self.host = new_host
        self.model = new_model

        self.client = ollama.Client(
            host=self.host
        )

        return True

    def get_current_settings(self):
        return {
            "host": self.host,
            "model": self.model,
        }
