from src.api.client import api_client
import json

def test_manual_invoice_fix():
    print("?? Starting Manual Invoice Test (Fix Attempt)...")
    
    # Test Data
    debtor = "300-T001"
    item = "HLMINK" 
    qty = 1
    price = 10.00
    
    print(f"?? Sending Request: Debtor={debtor}, Item={item}, Qty={qty}")

    # Payload
    payload = [
        {
            "DebtorCode": debtor,
            "DocStatus": "A",
            "SubmitEInvoice": "F",        
            "ConsolidatedEInvoice": "F",  
            "Description": "API Test Invoice",
            "IVDTL": [
                {
                    "ItemCode": item,
                    "Qty": qty,
                    "UnitPrice": price
                }
            ],
            # KEY FIX: Passing 'SubmitInvoiceNow' via UDF to force a value into the column
            "UDF": [
                {
                    "FieldName": "SubmitInvoiceNow",
                    "Value": "F"
                }
            ]
        }
    ]
    
    try:
        # Print payload for verification
        print(f"?? Payload being sent:\n{json.dumps(payload, indent=2)}")
        
        response = api_client.post("api/Invoice", json_payload=payload)
        
        print("\n-----------------------------")
        # Check for success
        success = False
        doc_no = "Unknown"
        
        # Handle list response (Success usually returns a list of results)
        if isinstance(response, list) and len(response) > 0:
            result_item = response[0]
            # API often returns the created object with DocNo
            if "DocNo" in result_item:
                success = True
                doc_no = result_item["DocNo"]
        
        # Handle dict response (Error or status object)
        elif isinstance(response, dict):
            status = response.get("Status", "")
            if status == "Success":
                success = True
                # Try to find DocNo in ResultTable if available
                if "ResultTable" in response and response["ResultTable"]:
                    doc_no = response["ResultTable"][0].get("DocNo", "Unknown")

        if success:
            print(f"? SUCCESS! Invoice Created: {doc_no}")
        else:
            print(f"? FAILED. Raw Response: {response}")
            
    except Exception as e:
        print(f"? EXCEPTION: {str(e)}")

    print("-----------------------------\n")

if __name__ == "__main__":
    test_manual_invoice_fix()