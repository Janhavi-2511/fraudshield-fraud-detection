import streamlit as st
import requests

API_BASE = "http://localhost:8000"

def fetch_data(endpoint):
    try:
        res = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        if res.status_code == 200:
            return res.json()
    except requests.exceptions.RequestException:
        pass
    return None

def trigger_ai(alert_id):
    try:
        requests.post(f"{API_BASE}/analyze/{alert_id}", timeout=2)
    except Exception:
        pass

def inject_light_theme_css():
    st.markdown("""
        <style>
        .stContainer > div {
            background-color: #ffffff;
            padding: 1.2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            border: 1px solid #e9ecef;
        }
        
        /* Hide the default Streamlit running status tracker to prevent visual jumping */
        div[data-testid="stStatusWidget"] { display: none !important; }
        
        /* ENTIRELY remove the reloading shadow/dim effect */
        *[data-stale="true"], div[data-stale="true"], [data-testid="stFragment"] {
            opacity: 1 !important; 
            transition: none !important; 
            filter: none !important;
        }
        </style>
    """, unsafe_allow_html=True)
