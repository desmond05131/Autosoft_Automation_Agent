from src.api.client import api_client

def create_invoice(debtor_code, item_code, qty, unit_price):
    """
    Creates a simple Invoice (IV) in AutoCount.
    """
    # Payload structure based on documentation and error correction
    payload = [
        {
            "DebtorCode": debtor_code,
            "DocStatus": "A",             # A = Active
            "SubmitEInvoice": "T",        # Enable E-Invoice
            "ConsolidatedEInvoice": "F",  # Not consolidated
            "SubmitInvoiceNow": "F",      # Fix for "Column does not allow nulls". F = Do not auto-submit to LHDN yet.
            "IVDTL": [
                {
                    "ItemCode": item_code,
                    "Qty": qty,
                    "UnitPrice": unit_price,
                    # "TaxCode": "GST-6" # Optional: Add if your system enforces tax codes
                }
            ]
        }
    ]
    
    try:
        response = api_client.post("api/Invoice", json_payload=payload)
        
        # Check for success (API usually returns a list with ResultTable or Status)
        if response and isinstance(response, dict):
            status = response.get("Status", "")
            # AutoCount V2 API sometimes returns Status: "Success" or just a ResultTable
            if status == "Success" or response.get("ResultTable"):
                # Extract DocNo if available
                result_table = response.get("ResultTable", [])
                doc_no = result_table[0].get("DocNo") if result_table else "New Invoice"
                return {"success": True, "doc_no": doc_no}
        
        # If we get here, the API call returned a dict but indicated failure or missing data
        return {"success": False, "error": str(response)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}