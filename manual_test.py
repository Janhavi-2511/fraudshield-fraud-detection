from models import Transaction
from rules import evaluate_transaction
from datetime import datetime, timedelta

print("\n--- TEST 1: HIGH AMOUNT (R01) ---")

tx = Transaction(
    user_id="U1",
    amount=1500000,
    city="Mumbai",
    timestamp=datetime.now(),
    category="electronics"   # ✅ ADD THIS
)

history = []

score, rules = evaluate_transaction(tx, history)
print("Score:", score)
print("Rules Triggered:", rules)


print("\n--- TEST 2: VELOCITY (R02) ---")

now = datetime.now()

history = [
    Transaction(
        user_id="U1",
        amount=1000,
        city="Mumbai",
        timestamp=now - timedelta(minutes=10),
        category="grocery"
    ),
    Transaction(
        user_id="U1",
        amount=2000,
        city="Mumbai",
        timestamp=now - timedelta(minutes=20),
        category="grocery"
    )
]

tx = Transaction(
    user_id="U1",
    amount=3000,
    city="Mumbai",
    timestamp=now,
    category="grocery"
)

score, rules = evaluate_transaction(tx, history)
print("Score:", score)
print("Rules Triggered:", rules)


print("\n--- TEST 3: GEO (R03) ---")

history = [
    Transaction(
    user_id="U1",
    amount=1000,
    city="Mumbai",
    timestamp=now - timedelta(minutes=60),
    category="grocery"
)
]

tx = Transaction(
    user_id="U1",
    amount=2000,
    city="Delhi",
    timestamp=now,
    category="grocery"
)

score, rules = evaluate_transaction(tx, history)
print("Score:", score)
print("Rules Triggered:", rules)


print("\n--- TEST 4: NORMAL CASE ---")

history = []

tx = Transaction(
    user_id="U1",
    amount=1000,
    city="Mumbai",
    timestamp=datetime.now(),
    category="grocery"
)

score, rules = evaluate_transaction(tx, history)
print("Score:", score)
print("Rules Triggered:", rules)