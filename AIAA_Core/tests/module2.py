from src.api.debtor import create_debtor

def test_manual_create_debtor():
    print("🚀 Starting Manual Create Debtor Test...")
    
    # Hardcoded test values based on your chat attempt
    company_name = "WWI Enterprise (Test)"
    phone1 = "60123456789"
    address1 = "123 Test Street"
    register_no = "123456-T"
    
    print(f"📦 Sending Request: Company={company_name}, Phone={phone1}")
    
    # Call the function
    result = create_debtor(
        company_name=company_name, 
        phone1=phone1,
        address1=address1,
        register_no=register_no
    )
    
    print("\n-----------------------------")
    if result.get('success'):
        print(f"✅ SUCCESS! Debtor Created: Account No {result.get('acc_no')}")
    else:
        print(f"❌ FAILED. Error Message: {result.get('error')}")
    print("-----------------------------\n")

if __name__ == "__main__":
    test_manual_create_debtor()
