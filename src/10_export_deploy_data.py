"""
Step 10: Warehouse Export for Streamlit Cloud Deployment.

Purpose:
  Exports all warehouse tables and analytical views used by the Streamlit dashboard
  into a lightweight `deploy_data/` directory (under 50 MB total) so that the dashboard
  can run for free on Streamlit Community Cloud without requiring a hosted MySQL database.

Exports:
  1. deploy_data/smart_energy_dw.sqlite: SQLite database containing Fact & Dimension tables.
  2. deploy_data/fact_daily_summary.csv: Pre-aggregated daily fact table for ultra-fast fallback OLAP.
  3. deploy_data/anomaly_detection_results.csv: Anomaly readings for the anomaly alert console.
  4. deploy_data/anomaly_summary.json: Pre-computed totals to preserve exact grid evaluation metrics.
  5. deploy_data/classification_metrics.csv: Benchmark leaderboard metrics.

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import json
import logging
import sqlite3
from pathlib import Path
import pandas as pd
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from src.db_connection import get_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("10_ExportDeployData")

DEPLOY_DATA_DIR = BASE_DIR / "deploy_data"


def export_deploy_data():
    """
    Reads all warehouse tables and anomaly results from the active database
    and creates the standalone deploy_data/ assets.
    """
    logger.info("Initializing export for cloud deployment...")
    DEPLOY_DATA_DIR.mkdir(parents=True, exist_ok=True)

    engine, dialect = get_db_engine()
    logger.info("Reading warehouse data from active engine: %s...", dialect.upper())

    # 1. Export Standalone SQLite Database (Dim tables + Fact table + Anomaly table)
    sqlite_export_path = DEPLOY_DATA_DIR / "smart_energy_dw.sqlite"
    if sqlite_export_path.exists():
        sqlite_export_path.unlink()

    dest_conn = sqlite3.connect(sqlite_export_path)

    tables = [
        "Dim_Date", "Dim_Time", "Dim_Consumer",
        "Dim_Location", "Dim_Weather",
        "Fact_Energy_Consumption", "Anomaly_Detection_Results"
    ]

    with engine.connect() as conn:
        for tbl in tables:
            try:
                df = pd.read_sql(text(f"SELECT * FROM {tbl}"), conn)
                df.to_sql(tbl, dest_conn, if_exists="replace", index=False)
                logger.info("  Exported %s: %d rows to deploy SQLite DB", tbl, len(df))
            except Exception as e:
                logger.warning("  Could not export table %s directly: %s", tbl, str(e))

    # Add analytical indexes to the deploy SQLite DB
    dest_conn.execute("CREATE INDEX IF NOT EXISTS idx_f_dt ON Fact_Energy_Consumption(date_key);")
    dest_conn.execute("CREATE INDEX IF NOT EXISTS idx_f_cons ON Fact_Energy_Consumption(consumer_key);")
    dest_conn.execute("CREATE INDEX IF NOT EXISTS idx_anom_fact ON Anomaly_Detection_Results(fact_id);")
    dest_conn.commit()
    dest_conn.close()

    sqlite_size_mb = sqlite_export_path.stat().st_size / (1024 * 1024)
    logger.info("Standalone SQLite DB written to %s (%.2f MB)", sqlite_export_path, sqlite_size_mb)

    # 2. Export Pre-joined Daily Fact CSV for ultra-fast Pandas fallback OLAP
    logger.info("Generating pre-aggregated daily fact CSV...")
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
        full_df = pd.read_sql(text(query), conn)

    daily_csv_path = DEPLOY_DATA_DIR / "fact_daily_summary.csv"
    daily_df = full_df.groupby([
        "full_date", "year_number", "quarter_name", "month_name", "month_number",
        "day_name", "day_of_month", "is_weekend", "season",
        "city", "state", "region", "pincode",
        "consumer_id", "consumer_name", "consumer_type", "tariff_category", "connected_load_kw"
    ]).agg(
        energy_kwh=("energy_kwh", "sum"),
        peak_demand_kw=("peak_demand_kw", "max"),
        voltage_v=("voltage_v", "mean"),
        carbon_emissions_kg=("carbon_emissions_kg", "sum"),
        reading_count=("fact_id", "count")
    ).reset_index()

    # Re-attach surrogate fact_id
    daily_df["fact_id"] = daily_df.index + 1
    daily_df.to_csv(daily_csv_path, index=False)
    daily_size_mb = daily_csv_path.stat().st_size / (1024 * 1024)
    logger.info("Daily fact CSV written to %s (%d rows, %.2f MB)", daily_csv_path, len(daily_df), daily_size_mb)

    # 3. Export Anomaly Results CSV & Summary JSON
    anom_src_csv = config.ANOMALY_RESULTS_CSV
    anom_dest_csv = DEPLOY_DATA_DIR / "anomaly_detection_results.csv"
    summary_json_path = DEPLOY_DATA_DIR / "anomaly_summary.json"

    if anom_src_csv.exists():
        df_anom = pd.read_csv(anom_src_csv)
        # Compute exact full-population summary metrics
        summary_metrics = {
            "total_evaluated": len(df_anom),
            "iqr_flags": int(df_anom["is_anomaly_iqr"].sum()),
            "zscore_flags": int(df_anom["is_anomaly_zscore"].sum()),
            "kmeans_flags": int(df_anom["is_anomaly_kmeans"].sum()),
            "consensus_flags": int((df_anom["anomaly_consensus_count"] >= 2).sum())
        }
        with open(summary_json_path, "w") as f:
            json.dump(summary_metrics, f, indent=2)
        logger.info("Anomaly summary metrics written to %s", summary_json_path)

        # For the dashboard visual inspection, preserve all flagged anomalies across all 50 consumers,
        # plus the first 250 chronological readings per consumer for baseline plotting.
        needed_cols = [
            "timestamp", "consumer_id", "consumer_name", "consumer_type", "city",
            "energy_kwh", "voltage_v", "is_anomaly_iqr", "is_anomaly_zscore",
            "is_anomaly_kmeans", "anomaly_consensus_count", "investigation_status"
        ]
        available_cols = [c for c in needed_cols if c in df_anom.columns]
        df_anom_clean = df_anom[available_cols].copy()
        df_anom_clean["energy_kwh"] = df_anom_clean["energy_kwh"].round(2)
        df_anom_clean["voltage_v"] = df_anom_clean["voltage_v"].round(1)

        sub_rows = []
        for cid, grp in df_anom_clean.groupby("consumer_id"):
            sub_rows.append(grp.sort_values("timestamp").head(250))
            sub_rows.append(grp[grp["anomaly_consensus_count"] > 0])
        combined = pd.concat(sub_rows).drop_duplicates(subset=["consumer_id", "timestamp"]).reset_index(drop=True)

        combined.to_csv(anom_dest_csv, index=False)
        anom_size_mb = anom_dest_csv.stat().st_size / (1024 * 1024)
        logger.info("Anomaly detection results written to %s (%d rows, %.2f MB)",
                    anom_dest_csv, len(combined), anom_size_mb)

    # 4. Copy Classification Metrics
    metrics_src = config.TABLES_DIR / "classification_metrics.csv"
    metrics_dest = DEPLOY_DATA_DIR / "classification_metrics.csv"
    if metrics_src.exists():
        df_m = pd.read_csv(metrics_src)
        df_m.to_csv(metrics_dest, index=False)
        logger.info("Classification metrics copied to %s", metrics_dest)

    total_size_mb = sum(f.stat().st_size for f in DEPLOY_DATA_DIR.glob("*") if f.is_file()) / (1024 * 1024)
    logger.info("==================================================================")
    logger.info("DEPLOY DATA EXPORT COMPLETE! Total folder size: %.2f MB (< 50 MB target)", total_size_mb)
    logger.info("==================================================================")


if __name__ == "__main__":
    export_deploy_data()
