import json
from datetime import datetime
from models import Transaction

# Global Configuration Constraints (Dynamically Modifiable via API)
GLOBAL_WEIGHTS = {
    "high_value": 40,
    "velocity": 25,
    "midnight": 10,
    "geographical": 15,
    "high_risk_merchant": 10
}

# Configurable Rule Threshold Parameters
GLOBAL_THRESHOLDS = {
    "high_value_limit": 1000000.0,
    "velocity_time_window_sec": 1800,
    "geographical_time_window_sec": 7200
}

HIGH_RISK_MERCHANT_CATEGORIES = ["CRYPTO", "GAMBLING", "CASH_ADVANCE"]

def rule_high_value(tx: Transaction) -> bool:
    """R01: Transaction amount >= Limit"""
    return tx.amount >= GLOBAL_THRESHOLDS["high_value_limit"]

def rule_velocity(tx: Transaction, history: list[Transaction]) -> bool:
    """R02: 3 or more transactions within 30 minutes from the same user"""
    if not history:
        return False
    
    recent_count = 0
    tx_time = tx.timestamp
    
    for past_tx in history:
        # Avoid counting the same transaction
        if past_tx is tx:
            continue
            
        time_diff = (tx_time - past_tx.timestamp).total_seconds()
        if 0 <= time_diff <= GLOBAL_THRESHOLDS["velocity_time_window_sec"]: 
            recent_count += 1
            
    return recent_count >= 2 # 2 past + current = 3

def rule_midnight(tx: Transaction) -> bool:
    """R04: Transaction occurs between 00:00 and 05:00 hours"""
    hour = tx.timestamp.hour
    return 0 <= hour < 5

def rule_geographical(tx: Transaction, history: list[Transaction]) -> bool:
    """R03: Same user, different cities within 2 hours"""
    if not history:
        return False
        
    tx_time = tx.timestamp
    
    for past_tx in history:
        if past_tx is tx:
            continue
            
        time_diff = (tx_time - past_tx.timestamp).total_seconds()
        # Within explicit dynamic bounds AND in a different city
        if 0 <= time_diff <= GLOBAL_THRESHOLDS["geographical_time_window_sec"] and past_tx.city != tx.city:
            return True
            
    return False

def rule_high_risk_merchant(tx: Transaction) -> bool:
    """R05: Merchant category is in the high-risk list"""
    return tx.category.upper() in HIGH_RISK_MERCHANT_CATEGORIES

def evaluate_transaction(tx: Transaction, history: list[Transaction], weights: dict = None) -> tuple[int, list]:
    """
    Evaluates a transaction against all 5 rules dynamically.
    Returns: (total_score, triggered_rule_ids)
    """
    if weights is None:
        weights = GLOBAL_WEIGHTS
        
    total_score = 0
    flagged_rules = []
    
    # R01 execution
    if rule_high_value(tx):
        total_score += weights.get("high_value", 40)
        flagged_rules.append("R01")
        
    # R02 execution
    if rule_velocity(tx, history):
        total_score += weights.get("velocity", 25)
        flagged_rules.append("R02")
        
    # R04 execution (chronological ID)
    if rule_midnight(tx):
        total_score += weights.get("midnight", 10)
        flagged_rules.append("R04")
        
    # R03 execution
    if rule_geographical(tx, history):
        total_score += weights.get("geographical", 15)
        flagged_rules.append("R03")
        
    # R05 execution
    if rule_high_risk_merchant(tx):
        total_score += weights.get("high_risk_merchant", 10)
        flagged_rules.append("R05")
        
    # Cap maximum score at 100
    final_score = min(total_score, 100)
    
    return final_score, flagged_rules
