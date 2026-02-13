from datetime import datetime, timedelta
from src.api.client import api_client

def get_sales_listing(start_date, end_date):
    """Get invoices between dates."""
    params = {
        "StartDate": start_date,
        "EndDate": end_date
    }
    return api_client.get("Sales/GetInvoiceListing", params=params)

def get_daily_sales_dashboard(target_date_str=None):
    """Calculates daily revenue and invoice count."""
    if not target_date_str:
        target_date_str = datetime.now().strftime("%Y-%m-%d")
        
    invoices = get_sales_listing(target_date_str, target_date_str)
    
    if not invoices:
        return {"date": target_date_str, "revenue": 0.0, "count": 0}

    total_revenue = sum(float(inv.get('NetTotal', 0)) for inv in invoices)
    return {
        "date": target_date_str,
        "revenue": total_revenue,
        "count": len(invoices)
    }
