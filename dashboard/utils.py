"""
Streamlit Dashboard Utilities & Cached Data Fetchers.

Purpose:
  Provides cached queries, star schema data loading, and interactive Plotly chart generators
  shared across all Streamlit dashboard pages.

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from src.db_connection import get_db_engine

logger = logging.getLogger("DashboardUtils")


@st.cache_data(ttl=3600)
def load_fact_data() -> pd.DataFrame:
    """Loads joined fact table and dimension data from SQL warehouse or CSV backup."""
    try:
        engine, dialect = get_db_engine()
        query = """
        SELECT 
            f.fact_id, f.energy_kwh, f.voltage_v, f.peak_demand_kw, f.carbon_emissions_kg,
            d.full_date, d.day_of_month, d.month_name, d.month_number, d.quarter_name, d.year_number, d.day_name, d.is_weekend, d.season,
            t.hour_of_day, t.time_label, t.period_of_day, t.is_peak_hour,
            c.consumer_id, c.consumer_name, c.consumer_type, c.tariff_category, c.connected_load_kw,
            l.city, l.state, l.region, l.pincode
        FROM Fact_Energy_Consumption f
        JOIN Dim_Date d ON f.date_key = d.date_key
        JOIN Dim_Time t ON f.time_key = t.time_key
        JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
        JOIN Dim_Location l ON f.location_key = l.location_key;
        """
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        df["full_date"] = pd.to_datetime(df["full_date"])
        return df
    except Exception as e:
        logger.warning("Could not query DB directly in dashboard (%s). Loading from feature CSV...", str(e))
        df = pd.read_csv(config.FEATURE_ENGINEERED_CSV)
        df["full_date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["full_date"] = pd.to_datetime(df["full_date"])
        return df


@st.cache_data(ttl=3600)
def load_anomaly_data() -> pd.DataFrame:
    """Loads anomaly detection results from CSV or database."""
    if config.ANOMALY_RESULTS_CSV.exists():
        df = pd.read_csv(config.ANOMALY_RESULTS_CSV)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_classification_metrics() -> pd.DataFrame:
    """Loads classification comparison metrics table."""
    metrics_file = config.TABLES_DIR / "classification_metrics.csv"
    if metrics_file.exists():
        return pd.read_csv(metrics_file)
    return pd.DataFrame()


def render_kpi_card(title: str, value: str, subtext: str = "", delta: str = None):
    """Renders a styled KPI metric card in Streamlit."""
    st.metric(label=title, value=value, delta=delta, help=subtext)

