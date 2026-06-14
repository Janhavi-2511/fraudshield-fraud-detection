import requests
import random

BASE_URL = "http://localhost:8000"

print("Injecting explicit Fraud Risk payloads to forcefully trigger UI Buttons...")

# We inject explicitly fraudulent transactions to trigger rules > score 50
merchants = ["Shady Offshore Co", "Anonymous VPN Services", "Crypto ATM XYZ", "Wire Transfer Global"]

for i in range(15):
    payload = {
        "user_id": f"SUSPECT_{random.randint(1000, 9999)}",
        "amount": random.uniform(85000.0, 150000.0), # Very high amounts trigger baseline rules natively
        "merchant": random.choice(merchants),
        "city": "Unknown",
        "category": random.choice(["Wire Transfer", "Crypto", "High Risk Transfer"])
    }
    
    try:
        r = requests.post(f"{BASE_URL}/evaluate", json=payload, timeout=5)
        if r.status_code == 200:
            data = r.json()
            score = data.get('risk_score', 0)
            status = data.get('status', 'OK')
            print(f"Injected transaction. Risk Score: {score} | Status: {status}")
    except Exception as e:
        print("Failed to route:", e)

print("Done forcing flags into the DB!")
