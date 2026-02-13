from src.api.client import api_client

def get_all_stock_raw():
    # Endpoint: api/V2/Item/GetItem (POST)
    payload = {"ItemCode": [], "IncludeBatchBal": True}
    response = api_client.post("api/V2/Item/GetItem", json=payload)
    
    if response and isinstance(response, dict):
        return response.get("ResultTable", [])
    return []

def _get_qty(item):
    """Helper to calculate total quantity from ItemDTL or main fields."""
    total_qty = 0.0
    if 'BalQty' in item: total_qty = float(item['BalQty'])
    elif 'Qty' in item: total_qty = float(item['Qty'])
    
    if "ItemDTL" in item and isinstance(item["ItemDTL"], list):
        for dtl in item["ItemDTL"]: 
            total_qty += float(dtl.get("BalQty", dtl.get("Qty", 0)))
    return total_qty

def get_stock_item(item_code):
    # Fetch all (or filter list locally) because API V2 search by specific code 
    # might require exact match in payload ["CODE"]
    
    # Strategy: Fetch list and search locally (matches bot_main.py logic)
    all_stock = get_all_stock_raw()
    
    item_code = item_code.lower()
    for item in all_stock:
        code = item.get('ItemCode', '').lower()
        desc = item.get('Description', '').lower()
        
        if item_code in code or item_code in desc:
            item['calculated_qty'] = _get_qty(item)
            return item
            
    return None

def get_all_stock(limit=20):
    data = get_all_stock_raw()
    if not data: return []
    
    # Calculate qty for display
    for i in data:
        i['calculated_qty'] = _get_qty(i)
        
    return data[:limit]