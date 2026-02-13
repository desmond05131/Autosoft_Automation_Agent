import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8015")
    
    # Critical: Ensure these match what works in bot_main.py
    API_TOKEN = os.getenv("API_TOKEN") # The License Key
    API_USER = os.getenv("API_USER", "ADMIN")
    API_PASSWORD = os.getenv("API_PASSWORD", "ADMIN")
    
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b")

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN")
        if not cls.API_TOKEN:
            raise ValueError("Missing API_TOKEN (License Key)")