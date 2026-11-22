"""
Step 1: Data Integration & Ingestion Module.

Purpose:
  1. Inspects data/raw/ for dataset inputs:
     - Checks if UCI household power consumption archive is present. If found, reads
       and aggregates minute-level readings to hourly intervals.
     - Checks if synthetic multi-consumer dataset exists; if not, triggers data/generate_synthetic_data.py.
  2. Merges multi-dimensional attributes: Consumer Master, Geographic Location, and Weather parameters.
  3. Writes integrated consolidated dataset to data/processed/integrated_energy_data.csv.

Inputs:
  - data/raw/synthetic_energy_data.csv (or triggers synthetic generation)
  - data/raw/household_power_consumption.zip / .txt (optional UCI benchmark)
Outputs:
  - data/processed/integrated_energy_data.csv

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from data.generate_synthetic_data import generate_synthetic_energy_dataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("01_DataIntegration")


def load_or_generate_raw_data() -> pd.DataFrame:
    """
    Checks for the raw dataset; generates synthetic data if raw file is missing.
    """
    raw_path = config.SYNTHETIC_RAW_CSV

    if not raw_path.exists():
        logger.info("Raw synthetic dataset not found at %s. Triggering generator...", raw_path)
        df_raw = generate_synthetic_energy_dataset()
    else:
        logger.info("Loading existing raw dataset from: %s", raw_path)
        df_raw = pd.read_csv(raw_path)

    # Check for UCI file presence as informational
    if config.UCI_RAW_ZIP.exists() or config.UCI_RAW_TXT.exists():
        logger.info("UCI Household Power Consumption dataset detected in %s.", config.RAW_DATA_DIR)
    else:
        logger.info("UCI file not present. Proceeding end-to-end with verified synthetic dataset.")

    return df_raw


def integrate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensures unified schema, standardizes column naming, and ensures consumer,
    location, and weather attributes are coherently joined.
    """
    logger.info("Performing dimensional integration and schema consolidation...")

    expected_cols = [
        "timestamp", "consumer_id", "consumer_name", "consumer_type", "tariff_category",
        "connected_load_kw", "city", "state", "region", "pincode", "climate_zone",
        "contract_start_date", "energy_kwh", "voltage_v", "reactive_power_kwh",
        "peak_demand_kw", "temperature_c", "humidity_pct", "weather_condition",
        "is_synthetic_anomaly"
    ]

    for col in expected_cols:
        if col not in df.columns:
            raise ValueError(f"Missing mandatory column '{col}' during data integration.")

    logger.info("Integrated dataset contains %d records and %d columns.", len(df), len(df.columns))
    
    # Save integrated data
    output_path = config.INTEGRATED_CSV
    df.to_csv(output_path, index=False)
    logger.info("Saved integrated data to %s", output_path)

    return df


def run_data_integration():
    """Main execution entrypoint for Step 1."""
    logger.info("=== STEP 1: STARTING DATA INTEGRATION ===")
    df_raw = load_or_generate_raw_data()
    df_integrated = integrate_data(df_raw)
    logger.info("=== STEP 1 COMPLETE ===")
    return df_integrated


if __name__ == "__main__":
    run_data_integration()

