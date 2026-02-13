from datetime import datetime, timedelta
from src.api.client import api_client

def get_sales_dashboard(specific_date_str=None):
    """
    Returns sales stats for a specific date AND the previous day (for comparison).
    Matches bot_main.py logic.
    """
    url = "api/Invoice/GetInvoice"
    
    # Date Logic
    if specific_date_str:
        try:
            target_dt = datetime.strptime(specific_date_str, "%Y/%m/%d")
        except:
            # Try ISO format if passed from AI agent
            try:
                target_dt = datetime.strptime(specific_date_str, "%Y-%m-%d")
            except:
                return None
    else:
        target_dt = datetime.now()

    # Format for API: YYYY/MM/DD
    target_date = target_dt.strftime("%Y/%m/%d")
    prev_date = (target_dt - timedelta(days=1)).strftime("%Y/%m/%d")
    
    # Payload requests range from PrevDate to TargetDate
    payload = {"DateFrom": prev_date, "DateTo": target_date}
    
    try:
        response = api_client.post(url, json_payload=payload)
        data = []
        if response and isinstance(response, dict):
            data = response.get("ResultTable", [])
            
        stats = {"sales": 0.0, "prev_sales": 0.0, "count": 0, "date": target_date}
        
        for inv in data:
            if inv.get("Cancelled") == "T": continue
            
            # Clean date string "2026-01-29T00..." -> "2026/01/29"
            doc_date_raw = inv.get("DocDate", "")[:10].replace("-", "/")
            
            amount = float(inv.get("FinalTotal", inv.get("NetTotal", 0.0)))
            
            if doc_date_raw == target_date:
                stats["sales"] += amount
                stats["count"] += 1
            elif doc_date_raw == prev_date:
                stats["prev_sales"] += amount
                
        return stats
    except Exception as e:
        print(f"Sales API Error: {e}")
        return None