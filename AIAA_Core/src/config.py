import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    API_BASE_URL = os.getenv("API_BASE_URL")
    API_TOKEN = os.getenv("API_TOKEN")
    API_USER = os.getenv("API_USER")
    API_PASSWORD = os.getenv("API_PASSWORD")
    
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN in .env")
        if not cls.API_BASE_URL:
            raise ValueError("Missing API_BASE_URL in .env")
