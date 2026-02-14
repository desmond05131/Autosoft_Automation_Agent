from src.api.client import api_client

def create_invoice(debtor_code, item_code, qty, unit_price):
    """
    Creates a simple Invoice (IV) in AutoCount.
    """
    # Payload structure with E-Invoice fields
    payload = [
        {
            "DebtorCode": debtor_code,
            "DocStatus": "A",             # A = Active
            "SubmitEInvoice": "T",        # Enable E-Invoice features
            "ConsolidatedEInvoice": "F",  # Not a consolidated invoice
            "SubmitInvoiceNow": "F",      # REQUIRED FIX: Do not auto-submit to LHDN immediately
            "IVDTL": [
                {
                    "ItemCode": item_code,
                    "Qty": qty,
                    "UnitPrice": unit_price,
                    # Optional: "TaxCode": "GST-0"
                }
            ]
        }
    ]
    
    try:
        response = api_client.post("api/Invoice", json_payload=payload)
        
        # Check for success
        if response and isinstance(response, dict):
            status = response.get("Status", "")
            # API can return "Success" or just a ResultTable
            if status == "Success" or response.get("ResultTable"):
                result_table = response.get("ResultTable", [])
                doc_no = result_table[0].get("DocNo") if result_table else "New Invoice"
                return {"success": True, "doc_no": doc_no}
        
        # If API returns a failure message structure
        return {"success": False, "error": str(response)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}