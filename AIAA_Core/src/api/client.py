import requests
from src.config import Config

class AutoCountClient:
    def __init__(self):
        self.base_url = Config.API_BASE_URL.rstrip('/') # Ensure no double slash
        self.token = Config.API_TOKEN
        self.headers = {
            "Content-Type": "application/json"
        }
        # Login on startup (optional, but good practice if using token based auth later)
        # For now we use the static token method from bot_main.py logic

    def get(self, endpoint, params=None):
        """
        Sends GET request to: {API_BASE_URL}/api/v3/{endpoint}
        Example: endpoint="Debtor/GetDebtorList" -> http://localhost:8015/api/v3/Debtor/GetDebtorList
        """
        try:
            # Construct the full URL exactly like bot_main.py
            url = f"{self.base_url}/api/v3/{endpoint}"
            
            # Add token to payload/params if needed, or headers
            # Based on bot_main.py, some endpoints might need the token in the body or params
            # But usually Freely API uses headers or a static key. 
            # We will assume standard structure based on your logs.
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Connection Error: {e}")
            return None

api_client = AutoCountClient()