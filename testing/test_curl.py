"""Simple test to see the exact error from the registration endpoint"""

import requests
import json

def test_registration():
    url = "http://localhost:8001/api/v1/auth/register"
    
    data = {
        "email": "tesgksgdkt@example.com",
        "password": "TestPass123",
        "confirm_password": "TestPass123"
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        print(f"🔍 Testing registration endpoint: {url}")
        print(f"📤 Request data: {json.dumps(data, indent=2)}")
        print()
        
        response = requests.post(url, json=data, headers=headers)
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        print(f"📥 Response text: {response.text}")
        
        if response.status_code != 201:
            print(f"\n❌ Registration failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"❌ Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"❌ Could not parse error response as JSON")
        else:
            print(f"\n✅ Registration successful!")
            try:
                result = response.json()
                print(f"✅ Response: {json.dumps(result, indent=2)}")
            except:
                print(f"✅ Could not parse response as JSON")
                
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_registration()