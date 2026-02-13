from src.api.client import api_client

def get_debtor_list():
    """Fetch raw list from AutoCount."""
    return api_client.get("Debtor/GetDebtorList")

def get_top_debtors(limit=5):
    data = get_debtor_list()
    if not data: return []
    
    # Sort by Balance desc
    sorted_data = sorted(data, key=lambda x: float(x.get('Balance', 0)), reverse=True)
    return sorted_data[:limit]

def get_all_debtors(limit=20):
    data = get_debtor_list()
    if not data: return []
    return data[:limit]

def find_debtor(keyword):
    data = get_debtor_list()
    if not data: return None
    
    keyword = keyword.lower()
    for d in data:
        if keyword in d.get('CompanyName', '').lower() or keyword in d.get('DebtorCode', '').lower():
            return d
    return None