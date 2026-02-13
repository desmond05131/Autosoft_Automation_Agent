import requests
from src.config import Config

class AutoCountClient:
    def __init__(self):
        self.base_url = Config.API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {Config.API_TOKEN}",
            "Content-Type": "application/json"
        }

    def get(self, endpoint, params=None):
        """Standard GET request wrapper"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API Error ({endpoint}): {e}")
            return None

# Singleton instance to be used across the app
api_client = AutoCountClient()
