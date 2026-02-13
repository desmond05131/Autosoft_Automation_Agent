import os
from pathlib import Path
from dotenv import load_dotenv

# --- ROBUST PATH FINDING ---
# Finds .env file relative to this file (src/config.py -> up one level -> .env)
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / '.env'

# Load .env explicitly
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    print(f"⚠️ WARNING: .env file NOT found at: {ENV_PATH}")

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_TOKEN = os.getenv("API_TOKEN")
    API_USER = os.getenv("API_USER")
    API_PASSWORD = os.getenv("API_PASSWORD")
    
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

    @classmethod
    def validate(cls):
        """Ensures all necessary variables are loaded."""
        missing = []
        if not cls.TELEGRAM_TOKEN:
            missing.append("TELEGRAM_TOKEN")
        if not cls.API_BASE_URL:
            missing.append("API_BASE_URL")
        if not cls.API_TOKEN:
            missing.append("API_TOKEN")
            
        if missing:
            raise ValueError(f"Missing required .env variables: {', '.join(missing)}")