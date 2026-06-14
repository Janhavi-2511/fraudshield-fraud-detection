import streamlit as st

st.set_page_config(page_title="FraudShield Command Center", layout="wide", page_icon="🛡️")

# We define the routing mechanism for our Multi-Page Streamlit App!
pages = {
    "Dashboards": [
        st.Page("pages/01_Analytics_Overview.py", title="Analytics Hub", icon="📊", default=True),
        st.Page("pages/02_Transactions_Ledger.py", title="All Transactions", icon="💸")
    ],
    "Engine Configuration": [
        st.Page("pages/03_Risk_Parameters.py", title="Risk Threshold Controls", icon="⚙️")
    ]
}

pg = st.navigation(pages)
pg.run()
