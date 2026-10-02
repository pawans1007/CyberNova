from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

APP_NAME = "CyberNova"
APP_VERSION = "1.0.0"

OLLAMA_HOST = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:3b-instruct"

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATABASE_PATH = DATA_DIR / "cybernova.db"

MAX_HISTORY_MESSAGES = 30
AI_TIMEOUT_SECONDS = 120

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)