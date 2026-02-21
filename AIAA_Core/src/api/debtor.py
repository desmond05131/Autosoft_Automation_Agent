from src.api.client import api_client

# Add this function to the bottom of src/api/debtor.py

def create_debtor(company_name, phone1="", address1="", register_no=""):
    """
    Creates a new Debtor in AutoCount.
    """
    # Payload matching the API documentation requirements + fixing the PeppolFormat error
    payload = {
        "DebtorType": "G01-A", 
        "CompanyName": company_name,
        "RegisterNo": register_no,
        "IsGroupCompany": "F",
        "IsActive": "T",
        "IsCashSaleDebtor": "F",
        "TaxEntityID": "1",
        "Address1": address1,
        "Phone1": phone1,
        "StatementType": "O",
        "AgingOn": "I",
        # Added to fix: "Column 'SGEInvoicePeppolFormat' does not allow nulls"
        "SGEInvoicePeppolFormat": ""  
    }
    
    try:
        response = api_client.post("api/Debtor/", json_payload=payload)
        
        if response and isinstance(response, list) and len(response) > 0:
            result_item = response[0]
            if "AccNo" in result_item:
                return {"success": True, "acc_no": result_item["AccNo"]}
                
        return {"success": False, "error": str(response)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def _get_balance(item):
    """Calculates balance checking multiple potential keys."""
    for key in ['Balance', 'Outstanding', 'CurBalance', 'NetTotal']:
        if key in item and item[key] is not None: 
            return float(item[key])
    return 0.0

def get_debtor_list_raw():
    """Fetch all debtors."""
    # Matches bot_main.py: /api/Debtor/GetDebtor/ with AccNo=[]
    return api_client.post("api/Debtor/GetDebtor/", json_payload={"AccNo": []})

def get_debtor_outstanding(limit=5):
    """Returns top N debtors with positive balance."""
    data = get_debtor_list_raw()
    if not data: return []

    # Calculate show_bal for each
    for d in data:
        d['show_bal'] = _get_balance(d)
    
    # Filter > 0
    debtors = [d for d in data if d['show_bal'] > 0]
    
    # Sort Descending
    sorted_debtors = sorted(debtors, key=lambda x: x['show_bal'], reverse=True)
    return sorted_debtors[:limit]

def get_all_debtors(limit=20):
    """Returns list of debtors."""
    data = get_debtor_list_raw()
    if not data: return []
    
    for d in data:
        d['show_bal'] = _get_balance(d)
        
    return data[:limit]

def get_debtor_profile(keyword):
    """Finds a specific debtor by Name or AccNo."""
    data = get_debtor_list_raw()
    if not data: return None
    
    keyword = keyword.lower()
    for item in data:
        if keyword in item.get("CompanyName", "").lower() or keyword in item.get("AccNo", "").lower():
            item['show_bal'] = _get_balance(item)
            return item
    return None