from src.api.client import api_client

def get_debtor_list():
    """Fetch all debtors."""
    return api_client.get("Debtor/GetDebtorList")

def get_outstanding_debtors(min_amount=0):
    """Logic to filter debtors who owe money."""
    debtors = get_debtor_list()
    if not debtors:
        return []
    
    # Filter based on balance
    outstanding = [
        d for d in debtors 
        if float(d.get('Balance', 0)) > min_amount
    ]
    # Sort by highest balance
    return sorted(outstanding, key=lambda x: float(x.get('Balance', 0)), reverse=True)
