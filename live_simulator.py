import time
import requests
import random
import uuid

# Fixed Configuration
API_BASE = "http://localhost:8000"

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", 
    "Ahmedabad", "Chennai", "Kolkata", "Surat", 
    "Pune", "Jaipur", "Lucknow", "Kanpur", "Nagpur", 
    "Indore", "Thane", "Bhopal", "Visakhapatnam",
    "Patna", "Vadodara", "Ghaziabad", "Coimbatore"
]

CATEGORIES = [
    "Groceries", "Dining", "Retail", "Utilities", "Travel",
    "Entertainment", "Healthcare", "Education", "Insurance",
    "Real Estate", "Fuel", "Subscription",
    "CRYPTO", "GAMBLING", "CASH_ADVANCE", "WIRE_TRANSFER"
]

MERCHANTS = [
    "Amazon India", "Flipkart", "BigBasket", "Swiggy", "Zomato",
    "IRCTC", "BookMyShow", "PhonePe Merchant", "Paytm Mall",
    "Reliance Digital", "DMart", "Starbucks India", "Uber India",
    "MakeMyTrip", "Apollo Pharmacy", "Croma", "Nykaa",
    "JioCinema Premium", "Netflix India", "Hotstar",
    "Unknown Offshore LLC", "CryptoSwap Exchange", "AnonymousVPN Co",
    "Cash Express ATM", "Wire Global Services", "Shell Petrol",
    "HP Fuel", "BPCL", "LIC Premium", "SBI Insurance"
]

DEVICE_TYPES = ["iOS", "Android", "Web", "POS", "ATM"]

user_ids = [f"USR_{str(uuid.uuid4())[:8]}" for _ in range(200)]

def random_ip():
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def generate_payload():
    user_id = random.choice(user_ids)
    
    # 30% chance of anomaly for more interesting data
    is_anomaly = random.random() < 0.30
    
    if is_anomaly:
        anomaly_type = random.choice(["extreme_value", "high_risk_merch", "suspicious_pattern", "micro_fraud"])
        if anomaly_type == "extreme_value":
            amount = random.uniform(1200000.0, 8000000.0)
            cat = random.choice(["Real Estate", "Insurance", "WIRE_TRANSFER"])
            merchant = random.choice(["Wire Global Services", "Unknown Offshore LLC", "LIC Premium"])
        elif anomaly_type == "high_risk_merch":
            amount = random.uniform(5000.0, 500000.0)
            cat = random.choice(["CRYPTO", "GAMBLING", "CASH_ADVANCE"])
            merchant = random.choice(["CryptoSwap Exchange", "Cash Express ATM", "AnonymousVPN Co"])
        elif anomaly_type == "suspicious_pattern":
            amount = random.uniform(49000.0, 51000.0)  # Just under/over round numbers
            cat = random.choice(CATEGORIES[:8])
            merchant = random.choice(MERCHANTS[:15])
        else:  # micro_fraud - lots of small transactions
            amount = random.uniform(1.0, 500.0)
            cat = random.choice(["Subscription", "Entertainment"])
            merchant = random.choice(MERCHANTS[:15])
    else:
        # Normal transactions with realistic spread
        amount_tier = random.choice(["low", "medium", "high"])
        if amount_tier == "low":
            amount = random.uniform(50.0, 3000.0)
        elif amount_tier == "medium":
            amount = random.uniform(3000.0, 50000.0)
        else:
            amount = random.uniform(50000.0, 300000.0)
        cat = random.choice(CATEGORIES[:12])  # Only normal categories
        merchant = random.choice(MERCHANTS[:20])
        
    return {
        "user_id": user_id,
        "amount": round(amount, 2),
        "merchant": merchant,
        "city": random.choice(INDIAN_CITIES),
        "category": cat,
        "device_type": random.choice(DEVICE_TYPES),
        "ip_address": random_ip()
    }

def run_simulation():
    print("Starting Infinite Live Simulator Engine...")
    print("Press CTRL+C to stop.")
    
    while True:
        try:
            requests.get(f"{API_BASE}/metrics", timeout=2)
            break
        except requests.exceptions.RequestException:
            print("Waiting for FastAPI server...")
            time.sleep(2)
            
    print("Connected! Pumping diverse telemetry...")
    
    req_counter = 0
    try:
        while True:
            payload = generate_payload()
            try:
                r = requests.post(f"{API_BASE}/evaluate", json=payload, timeout=2)
                if r.status_code == 200:
                    req_counter += 1
                    data = r.json()
                    status = data.get('status')
                    if status == "REJECTED":
                        print(f"[BLOCK] Score: {data.get('risk_score')} | {payload['merchant']} | {payload['amount']:.0f}")
                    elif req_counter % 20 == 0:
                        print(f"[OK] Clean traffic count: {req_counter}")
            except requests.exceptions.RequestException as e:
                print(f"[WARN] {e}")
                
            time.sleep(random.uniform(0.1, 0.4))
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    run_simulation()
