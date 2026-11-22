"""
Page 4: Unsupervised Anomaly Detection & Investigation Alerts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.utils import load_anomaly_data
import config

st.title("🚨 Anomaly Detection & Investigation Console")
st.warning("⚠️ **Operational Notice:** Flagged records represent **'unusual readings that need investigation'**, NOT definitive proof of power theft or equipment failure.")

df_anom = load_anomaly_data()

if not df_anom.empty:
    # Method selector
    method = st.selectbox(
        "Select Anomaly Detection Method to Inspect:",
        ["Consensus Voting (>=2 Methods)", "IQR Rule", "Z-Score Rule", "K-Means Distance Clustering"]
    )

    if method == "IQR Rule":
        flag_col = "is_anomaly_iqr"
    elif method == "Z-Score Rule":
        flag_col = "is_anomaly_zscore"
    elif method == "K-Means Distance Clustering":
        flag_col = "is_anomaly_kmeans"
    else:
        flag_col = "consensus_flag"
        df_anom["consensus_flag"] = (df_anom["anomaly_consensus_count"] >= 2).astype(int)

    # Summary metrics
    total_records = len(df_anom)
    total_anomalies = df_anom[flag_col].sum()
    pct_flagged = (total_anomalies / total_records) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Readings Evaluated", f"{total_records:,}")
    c2.metric("Unusual Readings Flagged", f"{total_anomalies:,}")
    c3.metric("Anomaly Flag Rate", f"{pct_flagged:.2f}%")

    st.divider()

    # Time-Series Interactive Inspection per Consumer
    st.subheader("📈 Consumer Time-Series with Highlighted Anomaly Alerts")
    consumers = sorted(df_anom["consumer_id"].unique().tolist())
    selected_consumer = st.selectbox("Select Consumer to Inspect", consumers, index=0)

    cons_data = df_anom[df_anom["consumer_id"] == selected_consumer].sort_values("timestamp")

    fig = go.Figure()
    # Baseline line
    fig.add_trace(go.Scatter(
        x=cons_data["timestamp"],
        y=cons_data["energy_kwh"],
        mode="lines",
        name="Hourly Energy (kWh)",
        line=dict(color="#1f77b4", width=1.5)
    ))

    # Anomaly markers
    anom_points = cons_data[cons_data[flag_col] == 1]
    if len(anom_points) > 0:
        fig.add_trace(go.Scatter(
            x=anom_points["timestamp"],
            y=anom_points["energy_kwh"],
            mode="markers",
            name="Unusual Reading (Flagged)",
            marker=dict(color="#d9534f", size=10, symbol="circle-open-dot", line=dict(width=2, color="red")),
            hovertext=anom_points["investigation_status"]
        ))

    fig.update_layout(
        title=f"Consumption Profile with Alerts — {selected_consumer}",
        xaxis_title="Timestamp",
        yaxis_title="Energy Consumption (kWh)",
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # Flagged investigation table
    st.subheader("📋 Flagged Records Requiring Field Inspection")
    flagged_table = df_anom[df_anom[flag_col] == 1][[
        "timestamp", "consumer_id", "consumer_name", "consumer_type", "city",
        "energy_kwh", "voltage_v", "anomaly_consensus_count", "investigation_status"
    ]].sort_values(by="energy_kwh", ascending=False)

    st.dataframe(flagged_table.head(100), use_container_width=True)
else:
    st.warning("Anomaly results not found. Please run `python run_pipeline.py` first.")

