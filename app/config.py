import os
from dotenv import load_dotenv, find_dotenv


def getenv_int(name: str, default: int) -> int:
    try:
        value = os.getenv(name)
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default

def getenv_bool(name: str, default: bool) -> bool:
    try:
        value = os.getenv(name)
        if value is None:
            return default
        return value.lower() not in ["false", "0"]
    except (TypeError, ValueError):
        return default

load_dotenv(override=True)

MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "ollama")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
AGENT_NAME = os.getenv("AGENT_NAME", "Local Work Agent")

ENABLE_THINKING = getenv_bool("ENABLE_THINKING", False)

BATCH_SIZE = getenv_int("BATCH_SIZE", 5)
CONCURRENT_OLLAMA_CALLS = getenv_int("CONCURRENT_OLLAMA_CALLS", 3)
