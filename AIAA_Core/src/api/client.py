import requests
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class AutoCountClient:
    def __init__(self):
        # Remove trailing slash to handle endpoints cleanly
        self.base_url = Config.API_BASE_URL.rstrip('/')
        self.user_id = Config.API_USER
        self.password = Config.API_PASSWORD
        self.token = Config.API_TOKEN
        self.auth_key = None
        self.session = requests.Session()
        
        # Initial Login
        self.login()

    def login(self):
        """Exchanges License Key for a Session JWT Token."""
        url = f"{self.base_url}/api/v3/Login"
        payload = {"UserID": self.user_id, "Password": self.password, "Token": self.token}
        
        try:
            print(f"🔐 Attempting Login to {url}...")
            response = self.session.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    self.auth_key = data[0].get("JWTToken")
                    print(f"✅ [AutoCount] Login Successful. Token acquired.")
                    return True
                else:
                    print(f"❌ [AutoCount] Login Failed: Empty response.")
            else:
                print(f"❌ [AutoCount] Login Failed: Status {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ [AutoCount] Login Exception: {e}")
        
        return False

    def _get_headers(self):
        """Returns headers with Auth Token. Re-logins if needed."""
        if not self.auth_key:
            self.login()
        return {"Content-Type": "application/json", "Authorization": self.auth_key}

    def post(self, endpoint, json_payload=None):
        """
        Generic POST request wrapper.
        Handles full URL construction and Re-login on 401.
        """
        # Ensure endpoint format (bot_main.py uses full paths like /api/Debtor/...)
        if not endpoint.startswith("api/"):
             # Handle cases where user might pass short paths, though we prefer full paths
             pass 

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            headers = self._get_headers()
            response = self.session.post(url, json=json_payload, headers=headers, timeout=15)
            
            # Auto-retry on 401 Unauthorized
            if response.status_code == 401:
                print("⚠️ Token expired. Re-logging in...")
                if self.login():
                    headers = self._get_headers()
                    response = self.session.post(url, json=json_payload, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.error(f"API Error ({endpoint}): {response.status_code} {response.text}")
                return None
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API Connection Error ({endpoint}): {e}")
            return None

# Singleton Instance
api_client = AutoCountClient()