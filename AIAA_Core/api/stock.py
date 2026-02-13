from src.api.client import api_client

def get_stock_item(item_code):
    """Fetch stock details for a specific item code."""
    # Assuming endpoint based on your documentation or typical AutoCount patterns
    # You might need to adjust the endpoint '/Stock/GetItem' matches your Freely API 
    data = api_client.get("Stock/GetItem", params={"code": item_code})
    
    if data and isinstance(data, list) and len(data) > 0:
        return data[0]  # Return the first match
    return None
