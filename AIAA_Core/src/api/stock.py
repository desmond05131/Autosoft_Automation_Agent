from src.api.client import api_client

def get_stock_item(item_code):
    # Try exact match first via API query if supported, or fetch list and filter
    # Based on logs, 'Stock/GetItem?code=...' is valid
    response = api_client.get("Stock/GetItem", params={"code": item_code})
    
    # If API returns a list, return first item
    if isinstance(response, list) and len(response) > 0:
        return response[0]
    # If API returns a single dict
    if isinstance(response, dict) and response.get('ItemCode'):
        return response
    
    # Fallback: Search manually in full list (slower but safer)
    all_stock = get_all_stock(limit=1000)
    for item in all_stock:
        if item_code.lower() in item.get('ItemCode', '').lower() or \
           item_code.lower() in item.get('Description', '').lower():
            return item
            
    return None

def get_all_stock(limit=20):
    # Assuming Stock/GetItem without params returns list, or use Stock/GetStockList if available
    # Using GetItem based on your bot_main.py logs
    data = api_client.get("Stock/GetItem") 
    if not data: return []
    return data[:limit]