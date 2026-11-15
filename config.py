import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"), override=True)
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "").strip()
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "").strip()
OLLAMA_URL = os.getenv("OLLAMA_URL", "").strip().rstrip("/")

EMBED_MODEL = "embeddinggemma"
CHAT_MODEL = "qwen3:4b"
TOP_K = 5
