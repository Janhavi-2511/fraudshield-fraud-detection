# fraudshield-fraud-detection

# FraudShield — AI-Based Fraud Detection Dashboard

A full-stack fraud detection system built with FastAPI and Streamlit,
using a rule-based engine and Gemini 2.0 Flash AI for real-time fraud
pattern explanations.

## What It Does
- Scores transactions across 3 risk dimensions: high-value thresholds,
  off-hours activity, and high-risk merchant categories
- Integrates Gemini 2.0 Flash API to generate AI-driven explanations
  for flagged alerts
- Simulates 1,000+ synthetic transactions with ~15% fraud injection
- Live dashboard metrics: fraud ratio, capital at risk, configurable
  risk parameters

## Tech Stack
Python, FastAPI, Streamlit, SQLAlchemy, SQLite, Pydantic, Gemini 2.0 Flash API

## How to Run
1. Clone the repo
2. Install dependencies: `pip install -r requirements.txt`
3. Add your Gemini API key to environment variables
4. Run the API: `uvicorn api:app --reload`
5. Run the dashboard: `streamlit run app.py`
