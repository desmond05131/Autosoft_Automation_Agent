from src.api.client import api_client

def get_debtor_list_raw():
    """Fetch raw list from AutoCount using the correct endpoint."""
    # Endpoint: api/Debtor/GetDebtor/ (POST)
    # Payload: {"AccNo": []} means "fetch all"
    return api_client.post("api/Debtor/GetDebtor/", json={"AccNo": []})

def _get_balance(item):
    """Helper to extract balance safely."""
    for key in ['Balance', 'Outstanding', 'CurBalance', 'NetTotal']:
        if key in item and item[key] is not None: 
            return float(item[key])
    return 0.0

def get_top_debtors(limit=5):
    data = get_debtor_list_raw()
    if not data: return []
    
    # Inject balance helper
    for d in data:
        d['calculated_balance'] = _get_balance(d)
        
    # Filter > 0 and Sort by Balance desc
    debtors = [d for d in data if d['calculated_balance'] > 0]
    sorted_data = sorted(debtors, key=lambda x: x['calculated_balance'], reverse=True)
    return sorted_data[:limit]

def get_all_debtors(limit=20):
    data = get_debtor_list_raw()
    if not data: return []
    return data[:limit]

def find_debtor(keyword):
    data = get_debtor_list_raw()
    if not data: return None
    
    keyword = keyword.lower()
    for d in data:
        # Search in CompanyName or AccNo
        if keyword in d.get('CompanyName', '').lower() or keyword in d.get('AccNo', '').lower():
            d['calculated_balance'] = _get_balance(d)
            return d
    return None