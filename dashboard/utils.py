"""
Streamlit Dashboard Utilities & Cached Data Fetchers.

Purpose:
  Provides cached queries, star schema data loading, and interactive Plotly chart generators
  shared across all Streamlit dashboard pages.

Dual-Mode Architecture:
  1. Primary: If MySQL settings exist (in .env or Streamlit secrets) and connection succeeds,
     reads live star-schema data directly from MySQL.
  2. Fallback: If MySQL is unavailable, seamlessly loads from `deploy_data/`:
     - Connects to `deploy_data/smart_energy_dw.sqlite` or reads `deploy_data/fact_daily_summary.csv`
     - Computes all OLAP aggregations (roll-up, drill-down, slice, dice) locally with Pandas.
     - Detects and displays active data source banner in the sidebar.

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

logger = logging.getLogger("DashboardUtils")
DEPLOY_DATA_DIR = BASE_DIR / "deploy_data"


def get_mysql_credentials() -> Dict[str, Any]:
    """
    Extracts MySQL credentials with precedence:
    1. Streamlit Cloud Secrets (st.secrets) if present.
    2. Environment variables (.env / os.environ).
    """
    creds = {
        "host": config.DB_HOST,
        "port": config.DB_PORT,
        "user": config.DB_USER,
        "password": config.DB_PASSWORD,
        "database": config.DB_NAME
    }

    # Streamlit secrets override
    try:
        if hasattr(st, "secrets") and "mysql" in st.secrets:
            s_mysql = st.secrets["mysql"]
            creds["host"] = s_mysql.get("host", creds["host"])
            creds["port"] = int(s_mysql.get("port", creds["port"]))
            creds["user"] = s_mysql.get("user", creds["user"])
            creds["password"] = s_mysql.get("password", creds["password"])
            creds["database"] = s_mysql.get("database", creds["database"])
    except Exception:
        pass

    return creds


def try_connect_mysql() -> Optional[Any]:
    """
    Attempts to create a live connection to MySQL.
    Fails safely if MySQL is not reachable or libraries are absent.
    """
    creds = get_mysql_credentials()

    # If host is default localhost and password is empty or default template, verify gently
    try:
        from sqlalchemy import create_engine, text
        mysql_url = (
            f"mysql+pymysql://{creds['user']}:{creds['password']}@"
            f"{creds['host']}:{creds['port']}/{creds['database']}"
        )
        engine = create_engine(mysql_url, pool_recycle=3600, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
        return engine
    except Exception as e:
        logger.info("Live MySQL not accessible (%s). Will use deploy_data/ fallback.", str(e))
        return None


@st.cache_resource
def get_active_data_source() -> Tuple[str, str]:
    """
    Determines active data source mode:
    Returns (source_type, status_label)
      source_type: 'mysql' or 'fallback'
      status_label: 'Live MySQL warehouse' or 'Exported warehouse data'
    """
    engine = try_connect_mysql()
    if engine is not None:
        return "mysql", "Live MySQL warehouse"
    return "fallback", "Exported warehouse data"


def render_datasource_badge():
    """Renders a small sidebar note showing active data source."""
    source_type, status_label = get_active_data_source()
    if source_type == "mysql":
        st.sidebar.success(f"🟢 **Data Source:** {status_label}")
    else:
        st.sidebar.info(f"📦 **Data Source:** {status_label}")


@st.cache_data(ttl=3600)
def load_fact_data() -> pd.DataFrame:
    """
    Loads joined fact table and dimension attributes.
    If MySQL is live, queries SQL warehouse directly.
    Otherwise loads from deploy_data/ SQLite DB or fact_daily_summary.csv.
    """
    source_type, _ = get_active_data_source()

    if source_type == "mysql":
        try:
            from sqlalchemy import text
            engine = try_connect_mysql()
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
            logger.warning("Error querying MySQL: %s. Falling back to local data.", str(e))

    # FALLBACK MODE: Check SQLite in deploy_data/
    deploy_sqlite = DEPLOY_DATA_DIR / "smart_energy_dw.sqlite"
    if deploy_sqlite.exists():
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(f"sqlite:///{deploy_sqlite}", connect_args={"check_same_thread": False})
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
            logger.warning("Could not read deploy SQLite: %s", str(e))

    # Fallback to deploy_data/fact_daily_summary.csv
    deploy_csv = DEPLOY_DATA_DIR / "fact_daily_summary.csv"
    if deploy_csv.exists():
        df = pd.read_csv(deploy_csv)
        df["full_date"] = pd.to_datetime(df["full_date"])
        return df

    # Fallback to project root processed data
    if config.FEATURE_ENGINEERED_CSV.exists():
        df = pd.read_csv(config.FEATURE_ENGINEERED_CSV)
        df["full_date"] = pd.to_datetime(pd.to_datetime(df["timestamp"]).dt.date)
        return df

    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_anomaly_data() -> pd.DataFrame:
    """Loads anomaly detection results from deploy_data/ or database."""
    # Check deploy_data first
    deploy_anom_csv = DEPLOY_DATA_DIR / "anomaly_detection_results.csv"
    if deploy_anom_csv.exists():
        df = pd.read_csv(deploy_anom_csv)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    # Check processed CSV
    if config.ANOMALY_RESULTS_CSV.exists():
        df = pd.read_csv(config.ANOMALY_RESULTS_CSV)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df

    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_anomaly_summary() -> Dict[str, Any]:
    """Loads high-level anomaly metrics summary."""
    summary_path = DEPLOY_DATA_DIR / "anomaly_summary.json"
    if summary_path.exists():
        try:
            with open(summary_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


@st.cache_data(ttl=3600)
def load_classification_metrics() -> pd.DataFrame:
    """Loads classification comparison metrics table."""
    deploy_metrics = DEPLOY_DATA_DIR / "classification_metrics.csv"
    if deploy_metrics.exists():
        return pd.read_csv(deploy_metrics)

    metrics_file = config.TABLES_DIR / "classification_metrics.csv"
    if metrics_file.exists():
        return pd.read_csv(metrics_file)
    return pd.DataFrame()


def render_kpi_card(title: str, value: str, subtext: str = "", delta: str = None):
    """Renders a styled KPI metric card in Streamlit."""
    st.metric(label=title, value=value, delta=delta, help=subtext)
