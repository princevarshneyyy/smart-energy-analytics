"""
Main Entrypoint for Smart Energy Analytics & Anomaly Detection System Dashboard.

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
from pathlib import Path
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from dashboard.utils import render_datasource_badge

st.set_page_config(
    page_title="Smart Energy Analytics & Anomaly Detection",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Render active data source badge in sidebar
render_datasource_badge()

st.title("⚡ Smart Energy Consumption Analytics & Anomaly Detection System")
st.markdown("### *Data Mining and Warehousing Lab (24B15CS313) — JIIT Noida*")

st.markdown("""
Welcome to the interactive analytics platform. This system implements a full-stack end-to-end data mining
and data warehousing solution for electrical consumption intelligence across smart meter grids.

---
#### 📌 Key System Modules & Navigation:
1. **📊 1_Overview**: High-level KPIs, temporal energy consumption trends (daily/weekly/monthly), and demand distributions.
2. **🧊 2_OLAP_Explorer**: Multidimensional data cube operations — **Roll-up, Drill-down, Slice, and Dice** with dynamic filtering.
3. **🎯 3_Classification**: Supervised model performance (**Decision Tree, Naive Bayes, kNN, SVM**), confusion matrices, and feature importance.
4. **🚨 4_Anomaly_Alerts**: Unsupervised anomaly detection (**IQR, Z-Score, K-Means clustering**) highlighting unusual consumption readings.

---
#### 🏛️ Architecture Highlights:
- **Star Schema Data Warehouse**: Centered around `Fact_Energy_Consumption` with surrogate-keyed dimensions (`Dim_Date`, `Dim_Time`, `Dim_Consumer`, `Dim_Location`, `Dim_Weather`).
- **Dual-Mode Data Engine**: Seamlessly toggles between live MySQL cloud warehouses and lightweight exported offline replicas.
- **Zero-Data-Leakage Classification**: Model inputs are strictly isolated from contemporaneous target values.
- **Wording Standard**: Anomalies are flagged as *"unusual readings that need investigation"*, avoiding unverified claims of theft or equipment failure.
- **WEKA Integration**: Pre-generated `.arff` files ready for comparative analysis in WEKA Explorer GUI.

*Use the sidebar on the left to navigate through the pages.*
""")

# System Status Check
st.sidebar.success("✅ System Status: Active")
st.sidebar.info("**Author:** 3rd-Year B.Tech CSE Student\n\n**Institution:** JIIT Noida")
