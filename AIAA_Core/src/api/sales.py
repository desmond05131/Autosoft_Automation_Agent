from src.api.client import api_client

def get_daily_sales(date_str):
    # Endpoint: api/Invoice/GetInvoice (POST)
    # Payload requires DateFrom and DateTo
    payload = {
        "DateFrom": date_str, # Format: YYYY/MM/DD
        "DateTo": date_str
    }
    
    # AutoCount usually returns data inside "ResultTable"
    response = api_client.post("api/Invoice/GetInvoice", json=payload)
    
    invoices = []
    if response and isinstance(response, dict):
        invoices = response.get("ResultTable", [])
    
    if not invoices:
        return {"revenue": 0.0, "count": 0, "diff": 0.0}

    # Calculate Total
    # AutoCount fields: FinalTotal or NetTotal
    total_revenue = 0.0
    count = 0
    
    for inv in invoices:
        if inv.get("Cancelled") == "T": 
            continue
        
        # Ensure we only sum sales for the specific date 
        # (API might return range, though here start=end)
        doc_date = inv.get("DocDate", "")[:10].replace("-", "/")
        if doc_date == date_str:
            amount = float(inv.get("FinalTotal", inv.get("NetTotal", 0.0)))
            total_revenue += amount
            count += 1
    
    return {
        "revenue": total_revenue,
        "count": count,
        "diff": 0.0 
    }