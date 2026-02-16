from src.api.invoice import create_invoice

def test_manual_invoice():
    print("?? Starting Manual Invoice Test...")
    
    # Hardcoded test values matching your successful manual entry attempt
    debtor = "300-T001"
    item = "HLMINK"
    qty = 1
    price = 10.00 # Arbitrary price for testing
    
    print(f"?? Sending Request: Debtor={debtor}, Item={item}, Qty={qty}")
    
    # Call the function
    result = create_invoice(debtor, item, qty, price)
    
    print("\n-----------------------------")
    if result['success']:
        print(f"? SUCCESS! Invoice Created: {result['doc_no']}")
    else:
        print(f"? FAILED. Error Message: {result.get('error')}")
    print("-----------------------------\n")

if __name__ == "__main__":
    test_manual_invoice()

