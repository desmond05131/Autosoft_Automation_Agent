from src.api.client import api_client

def create_invoice(debtor_code, item_code, qty, unit_price):
    """
    Creates a simple Invoice (IV) in AutoCount.
    """
    # Payload structure
    payload = [
        {
            "DebtorCode": debtor_code,
            "DocStatus": "A",             # A = Active
            "SubmitEInvoice": "T",        # Enable E-Invoice features
            "ConsolidatedEInvoice": "F",  # Not a consolidated invoice
            # --- FIX BELOW ---
            "SubmitInvoiceNow": "F",      # Required by your DB version. F = Draft/Do not submit to LHDN yet.
            # -----------------
            "IVDTL": [
                {
                    "ItemCode": item_code,
                    "Qty": qty,
                    "UnitPrice": unit_price,
                    # "TaxCode": "GST-0" # Uncomment if your system enforces tax codes
                }
            ]
        }
    ]
    
    try:
        response = api_client.post("api/Invoice", json_payload=payload)
        
        # Check for success
        # API returns a list containing the result object(s) or a dict with Status
        if response:
            # Handle list response (common in creating docs)
            if isinstance(response, list) and len(response) > 0:
                result_item = response[0]
                # If we get a result item with DocNo, it succeeded
                if "DocNo" in result_item:
                    return {"success": True, "doc_no": result_item["DocNo"]}
            
            # Handle dict response
            elif isinstance(response, dict):
                status = response.get("Status", "")
                result_table = response.get("ResultTable", [])
                
                if status == "Success" or (result_table and len(result_table) > 0):
                    # Try to extract DocNo from ResultTable if available
                    doc_no = "New Invoice"
                    if result_table and isinstance(result_table, list):
                        doc_no = result_table[0].get("DocNo", "New Invoice")
                    return {"success": True, "doc_no": doc_no}
        
        # If we reach here, consider it a failure and return the raw response for debugging
        return {"success": False, "error": str(response)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}