from src.api.client import api_client

def create_invoice(debtor_code, item_code, qty, unit_price):
    """
    Creates a simple Invoice (IV) in AutoCount.
    """
    # Payload structure based on documentation
    payload = [
        {
            "DebtorCode": debtor_code,
            "DocStatus": "A",
            "SubmitEInvoice": "T",
            "ConsolidatedEInvoice": "F",
            "IVDTL": [
                {
                    "ItemCode": item_code,
                    "Qty": qty,
                    "UnitPrice": unit_price,
                    # Optional: Add default tax/classification if needed by your specific DB
                    # "Classification": "007" 
                }
            ]
        }
    ]
    
    try:
        response = api_client.post("api/Invoice", json_payload=payload)
        
        # Check for success (API usually returns a list with ResultTable or Status)
        if response and isinstance(response, dict):
            status = response.get("Status", "")
            if status == "Success" or response.get("ResultTable"):
                # Extract DocNo if available
                result_table = response.get("ResultTable", [])
                doc_no = result_table[0].get("DocNo") if result_table else "New Invoice"
                return {"success": True, "doc_no": doc_no}
                
        return {"success": False, "error": str(response)}
        
    except Exception as e:
        return {"success": False, "error": str(e)}