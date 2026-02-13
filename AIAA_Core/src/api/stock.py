from src.api.client import api_client

def _get_qty(item):
    """Calculates total quantity looking at BalQty, Qty, and ItemDTL."""
    total_qty = 0.0
    if 'BalQty' in item: total_qty = float(item['BalQty'])
    elif 'Qty' in item: total_qty = float(item['Qty'])
    
    if "ItemDTL" in item and isinstance(item["ItemDTL"], list):
        for dtl in item["ItemDTL"]: 
            total_qty += float(dtl.get("BalQty", dtl.get("Qty", 0)))
    return total_qty

def get_stock_raw():
    """Fetches all items with batch balance."""
    # Matches bot_main.py: /api/V2/Item/GetItem
    payload = {"ItemCode": [], "IncludeBatchBal": True}
    response = api_client.post("api/V2/Item/GetItem", json_payload=payload)
    
    if response and isinstance(response, dict):
        return response.get("ResultTable", [])
    return []

def get_stock_list(limit=20):
    """Returns list of items with show_qty."""
    data = get_stock_raw()
    if not data: return []
    
    for i in data:
        i['show_qty'] = _get_qty(i)
        
    return data[:limit]

def get_stock_profile(keyword):
    """Finds exact item."""
    data = get_stock_raw()
    if not data: return None
    
    keyword = keyword.lower()
    for item in data:
        if keyword in item.get("ItemCode", "").lower() or keyword in item.get("Description", "").lower():
            item['show_qty'] = _get_qty(item)
            return item
    return None