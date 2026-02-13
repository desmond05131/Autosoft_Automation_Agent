from src.api.client import api_client

def get_daily_sales(date_str):
    # Endpoint: Sales/GetInvoiceListing?StartDate=...&EndDate=...
    params = {
        "StartDate": date_str,
        "EndDate": date_str
    }
    invoices = api_client.get("Sales/GetInvoiceListing", params=params)
    
    if not invoices:
        return {"revenue": 0.0, "count": 0, "diff": 0.0}

    total_revenue = sum(float(inv.get('NetTotal', 0)) for inv in invoices)
    
    return {
        "revenue": total_revenue,
        "count": len(invoices),
        "diff": 0.0 # Logic for diff comparison omitted for brevity
    }