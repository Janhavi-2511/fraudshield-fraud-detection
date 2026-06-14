import random
import uuid
from datetime import datetime, timedelta
from models import Transaction

INDIAN_CITIES = [
    "Mumbai", "Delhi", "Bengaluru", "Hyderabad", 
    "Ahmedabad", "Chennai", "Kolkata", "Surat"
]

NORMAL_CATEGORIES = ["Groceries", "Dining", "Retail", "Utilities", "Travel"]
HIGH_RISK_CATEGORIES = ["CRYPTO", "GAMBLING", "CASH_ADVANCE"]

def generate_synthetic_data(count: int = 1000) -> list[Transaction]:
    """
    Generates realistic simulation data for testing the application.
    ~15% of transactions will be explicitly designed to trigger fraud conditions.
    Memory Constraint: Yields a list to be digested efficiently.
    """
    transactions = []
    base_time = datetime(2023, 10, 1, 10, 0, 0) # Fixed start point for reproducibility
    
    # Pre-generate some consistent user IDs
    user_ids = [f"USR_{str(uuid.uuid4())[:8]}" for _ in range(50)]
    
    fraud_count_target = int(count * 0.15)
    fraud_generated = 0
    
    # We will walk forward in time
    current_time = base_time
    
    for i in range(count):
        # Move time forward by a few minutes usually
        current_time += timedelta(minutes=random.randint(5, 60))
        
        user_id = random.choice(user_ids)
        tx_id = str(uuid.uuid4())
        
        is_fraud = fraud_generated < fraud_count_target and random.random() < 0.2
        
        if is_fraud:
            fraud_generated += 1
            # Pick a rule to violate randomly
            fraud_type = random.choice(["high_value", "midnight", "high_risk"])
            
            if fraud_type == "high_value":
                amount = random.uniform(1050000.0, 5000000.0) # > 1m
                city = random.choice(INDIAN_CITIES)
                cat = random.choice(NORMAL_CATEGORIES)
                
            elif fraud_type == "midnight":
                amount = random.uniform(100.0, 50000.0)
                city = random.choice(INDIAN_CITIES)
                cat = random.choice(NORMAL_CATEGORIES)
                # Force time to 02:00 AM
                current_time = current_time.replace(hour=2)
                
            else: # high_risk
                amount = random.uniform(5000.0, 100000.0)
                city = random.choice(INDIAN_CITIES)
                cat = random.choice(HIGH_RISK_CATEGORIES)
                
        else:
            # Normal transaction
            amount = random.uniform(10.0, 50000.0)
            city = random.choice(INDIAN_CITIES)
            cat = random.choice(NORMAL_CATEGORIES)
            # Ensure safe hours
            if 0 <= current_time.hour < 5:
                current_time = current_time.replace(hour=10)

        tx = Transaction(
            id=tx_id,
            user_id=user_id,
            amount=round(amount, 2),
            timestamp=current_time,
            merchant=f"{cat} Merchant {random.randint(1,100)}",
            city=city,
            category=cat
        )
        transactions.append(tx)
        
    return transactions
