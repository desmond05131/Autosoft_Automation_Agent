import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

class Config:
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    
    # Matches bot_main.py: "http://localhost:8015"
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8015") 
    
    API_TOKEN = os.getenv("API_TOKEN")
    API_USER = os.getenv("API_USER", "ADMIN")
    API_PASSWORD = os.getenv("API_PASSWORD", "ADMIN")
    
    # Matches bot_main.py default
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-r1:8b") 

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_TOKEN:
            raise ValueError("Missing TELEGRAM_TOKEN in .env")
        if not cls.API_BASE_URL:
            raise ValueError("Missing API_BASE_URL in .env")