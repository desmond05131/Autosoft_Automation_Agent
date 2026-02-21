from src.api.client import api_client
import json

def inspect_latest_invoice():
    print("?? Fetching latest invoice to inspect structure...")
    
    # Based on AutoCount API patterns (e.g., api/Quotation/GetQuotation)
    # likely matches api/Invoice/GetInvoice
    endpoint = "api/Invoice/GetInvoice"
    
    # Request the single most recent record
    payload = {
        "RecordCount": 1
    }
    
    try:
        response = api_client.post(endpoint, json_payload=payload)
        
        if isinstance(response, dict) and "ResultTable" in response:
            invoices = response["ResultTable"]
            if len(invoices) > 0:
                invoice = invoices[0]
                print(f"\n? Successfully fetched Invoice: {invoice.get('DocNo')}")
                print("-" * 40)
                
                # 1. Search for the specific key in the main body
                found_key = False
                for key, value in invoice.items():
                    if "Submit" in key or "InvoiceNow" in key:
                        print(f"?? FOUND CANDIDATE KEY: '{key}' : '{value}'")
                        found_key = True
                
                if not found_key:
                    print("? No key resembling 'SubmitInvoiceNow' found in the main header.")

                # 2. Check UDFs (User Defined Fields)
                print("\n?? Checking UDFs...")
                udfs = invoice.get("UDF", [])
                if udfs:
                    print(json.dumps(udfs, indent=2))
                else:
                    print("No UDFs found.")

                print("-" * 40)
                print("\n?? Full Invoice Dump (for manual checking):")
                print(json.dumps(invoice, indent=2))
            else:
                print("? No invoices found in the database.")
        else:
            print(f"? Unexpected response format: {response}")

    except Exception as e:
        print(f"? Error executing request: {str(e)}")

if __name__ == "__main__":
    inspect_latest_invoice()
