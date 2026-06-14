from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import time
import json

load_dotenv()

from models import Base, engine, get_db, Transaction, Alert
from rules import evaluate_transaction, GLOBAL_WEIGHTS, GLOBAL_THRESHOLDS
from data_gen import generate_synthetic_data

app = FastAPI(title="FraudShield Backend API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize physical database schemas
Base.metadata.create_all(bind=engine)

# Auto-seed on startup if the database is empty
def _seed_if_empty():
    db = next(get_db())
    try:
        if db.query(Transaction).count() == 0:
            tx_list = generate_synthetic_data(count=950)
            db.bulk_save_objects(tx_list)
            db.commit()
            
            # Explicitly route 50 transactions through the evaluation engine to generate realistic ALERTS naturally.
            eval_list = generate_synthetic_data(count=50)
            for tx in eval_list:
                db.add(tx)
                db.commit()
                db.refresh(tx)
                history = db.query(Transaction).filter(Transaction.user_id == tx.user_id).order_by(Transaction.timestamp.desc()).limit(50).all()
                score, flags = evaluate_transaction(tx, history)
                if score >= 50:
                    alert = Alert(transaction_id=tx.id, risk_score=score, flagged_rules=json.dumps(flags), status="PENDING_AI")
                    db.add(alert)
                    db.commit()
    finally:
        db.close()

_seed_if_empty()

# Pydantic Schemas
class TransactionCreateReq(BaseModel):
    user_id: str
    amount: float
    merchant: str
    city: str
    category: str
    device_type: str = "WEB"
    ip_address: str = "0.0.0.0"

class ConfigUpdateReq(BaseModel):
    weights: dict
    thresholds: dict

class EvalResponse(BaseModel):
    transaction_id: str
    risk_score: int
    status: str
    rules_flagged: List[str]

class SimulateResponse(BaseModel):
    message: str
    total_transactions_created: int
    execution_time_ms: float

@app.post("/simulate", response_model=SimulateResponse)
def simulate_data(count: int = 1000, db: Session = Depends(get_db)):
    """Triggers the synthetic data creation and bulk inserts to DB."""
    start = time.time()
    
    tx_list = generate_synthetic_data(count=count)
    
    # Bulk insert for speed to respect 4GB NFR constraints
    db.bulk_save_objects(tx_list)
    db.commit()
    
    elapsed_ms = (time.time() - start) * 1000
    return SimulateResponse(
        message="Simulation succeeded.", 
        total_transactions_created=len(tx_list),
        execution_time_ms=elapsed_ms
    )

@app.post("/evaluate", response_model=EvalResponse)
def evaluate_tx(req: TransactionCreateReq, db: Session = Depends(get_db)):
    """Receives a new transaction, evaluates it via the Rule Engine, saves it, and returns the alert state."""
    # 1. Build DB object
    tx = Transaction(
        user_id=req.user_id,
        amount=req.amount,
        merchant=req.merchant,
        city=req.city,
        category=req.category,
        device_type=req.device_type,
        ip_address=req.ip_address
    )
    
    # Save the transaction so history logic includes it? No, save after evaluating so we don't count it twice incorrectly.
    # Actually, the logic in Unit 1 handles ignoring itself. So save it now.
    db.add(tx)
    db.commit()
    db.refresh(tx)
    
    # 2. Fetch recent history for rules evaluation 
    # Fetching only the last 50 for the user to optimize memory overhead.
    history = db.query(Transaction).filter(Transaction.user_id == tx.user_id).order_by(Transaction.timestamp.desc()).limit(50).all()
    
    # 3. Rule Engine Execution
    score, flags = evaluate_transaction(tx, history)
    
    # 4. Determine Action
    status = "ANALYZED"
    if score >= 50:
        status = "REJECTED"
        # Generate Alert entity
        alert = Alert(
            transaction_id=tx.id,
            risk_score=score,
            flagged_rules=json.dumps(flags),  # proper JSON serialization
            status=status
        )
        db.add(alert)
        db.commit()
        
    return EvalResponse(
        transaction_id=tx.id,
        risk_score=score,
        status=status,
        rules_flagged=flags
    )

@app.get("/alerts")
def get_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """Fetches flagged alerts for the dashboard."""
    alerts = db.query(Alert).order_by(Alert.risk_score.desc()).limit(limit).all()
    return alerts

@app.get("/alerts/{alert_id}")
def get_alert_detail(alert_id: str, db: Session = Depends(get_db)):
    """Fetches a specific alert payload including AI insights by ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
    return alert

@app.get("/transactions")
def get_transactions(limit: int = 500, db: Session = Depends(get_db)):
    """Retrieves all standard transactions. Strictly capped via pagination to protect memory limits."""
    cap = min(limit, 500)
    txs = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(cap).all()
    return txs

@app.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    """Computes summary statistics for the dashboard charts."""
    total_tx = db.query(Transaction).count()
    total_alerts = db.query(Alert).count()
    
    # Capital at risk = sum of amounts from all transactions that generated alerts
    capital_at_risk_result = (
        db.query(func.sum(Transaction.amount))
        .join(Alert, Alert.transaction_id == Transaction.id)
        .scalar()
    )
    capital_at_risk = round(capital_at_risk_result or 0.0, 2)
    
    return {
        "total_transactions": total_tx,
        "total_alerts": total_alerts,
        "fraud_ratio": round((total_alerts / max(1, total_tx)) * 100, 2),
        "capital_at_risk": capital_at_risk
    }

@app.get("/transactions/{tx_id}")
def get_transaction_detail(tx_id: str, db: Session = Depends(get_db)):
    """Get full details of a single transaction."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found.")
    return tx

@app.post("/analyze/{alert_id}")
def trigger_ai_analysis(alert_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Orchestrates the BackgroundTask async handoff to the Gemini API (Unit 3)."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found.")
        
    # Set immediate tracking state
    alert.status = "PENDING_AI"
    db.commit()
    
    # Hand off to the isolated LLM generator network bounds
    from gemini_client import process_ai_insight
    background_tasks.add_task(process_ai_insight, alert.id)
    
    return {"message": "queued", "alert_status": "PENDING_AI"}

@app.get("/config/weights")
def get_config_weights():
    return {
        "weights": GLOBAL_WEIGHTS,
        "thresholds": GLOBAL_THRESHOLDS
    }

@app.post("/config/weights")
def update_config_weights(req: ConfigUpdateReq):
    # Mutates the in-memory dictionary globally so the whole server thread pulls new scoring boundaries!
    GLOBAL_WEIGHTS.update(req.weights)
    GLOBAL_THRESHOLDS.update(req.thresholds)
    return {"status": "success"}

# Server Bootstrap Code
if __name__ == "__main__":
    import uvicorn
    # Launches the application natively on localhost:8000
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
