import requests
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class AutoCountClient:
    def __init__(self):
        self.base_url = Config.API_BASE_URL.rstrip('/')
        self.auth_key = None
        self.session = requests.Session()
        
        # Initial Login
        self.login()

    def login(self):
        """Exchanges License Key for a Session JWT Token."""
        endpoint = f"{self.base_url}/api/v3/Login"
        payload = {
            "UserID": Config.API_USER,
            "Password": Config.API_PASSWORD,
            "Token": Config.API_TOKEN  # This is the License Key
        }
        
        try:
            print(f"🔐 Attempting Login to {endpoint}...")
            response = self.session.post(endpoint, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    # Capture the JWT Token
                    self.auth_key = data[0].get("JWTToken")
                    print(f"✅ Login Successful. Token acquired.")
                    return True
                else:
                    print(f"❌ Login Failed: Empty response from server.")
            else:
                print(f"❌ Login Failed: Status {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Login Exception: {e}")
        
        return False

    def get_headers(self):
        """Constructs headers with the active Session Token."""
        headers = {
            "Content-Type": "application/json"
        }
        if self.auth_key:
            headers["Authorization"] = f"Bearer {self.auth_key}"
        return headers

    def get(self, endpoint, params=None):
        """Standard GET request wrapper with Auto-Relogin."""
        url = f"{self.base_url}/api/v3/{endpoint}"
        
        try:
            # First Attempt
            response = self.session.get(url, headers=self.get_headers(), params=params, timeout=15)
            
            # If 401 Unauthorized, try to login again and retry
            if response.status_code == 401:
                print("⚠️ Token expired. Re-logging in...")
                if self.login():
                    response = self.session.get(url, headers=self.get_headers(), params=params, timeout=15)

            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API Error ({endpoint}): {e}")
            # print(f"❌ API Error ({endpoint}): {e}") # Optional: Uncomment for noisy debugging
            return None

# Singleton Instance
api_client = AutoCountClient()