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
        # Login is one of the few endpoints that specifically uses /api/v3/
        endpoint = f"{self.base_url}/api/v3/Login"
        payload = {
            "UserID": Config.API_USER,
            "Password": Config.API_PASSWORD,
            "Token": Config.API_TOKEN 
        }
        
        try:
            print(f"🔐 Attempting Login to {endpoint}...")
            response = self.session.post(endpoint, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
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
            headers["Authorization"] = self.auth_key  # AutoCount uses the raw token, sometimes without 'Bearer'
        return headers

    def _request(self, method, endpoint, **kwargs):
        """Internal wrapper to handle full URLs and Re-login."""
        # We assume 'endpoint' starts with 'api/...' 
        # e.g. "api/Invoice/GetInvoice"
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.lower() == 'get':
                response = self.session.get(url, headers=self.get_headers(), timeout=15, **kwargs)
            else:
                response = self.session.post(url, headers=self.get_headers(), timeout=15, **kwargs)
            
            # If 401 Unauthorized, try to login again and retry
            if response.status_code == 401:
                print("⚠️ Token expired. Re-logging in...")
                if self.login():
                    if method.lower() == 'get':
                        response = self.session.get(url, headers=self.get_headers(), timeout=15, **kwargs)
                    else:
                        response = self.session.post(url, headers=self.get_headers(), timeout=15, **kwargs)

            if response.status_code != 200:
                logger.error(f"API Error ({endpoint}): {response.status_code} {response.text}")
                return None
                
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API Connection Error ({endpoint}): {e}")
            return None

    def get(self, endpoint, params=None):
        return self._request('get', endpoint, params=params)

    def post(self, endpoint, json=None):
        return self._request('post', endpoint, json=json)

# Singleton Instance
api_client = AutoCountClient()