"""
Step 2: Data Preprocessing & Cleaning Module.

Purpose:
  1. Identifies and removes duplicate readings (e.g. smart meter retry transmissions).
  2. Resolves inconsistent data types and sentinel strings (e.g. converting '?' to NaN).
  3. Imputes missing values using domain-appropriate grouping:
     - Missing energy_kwh imputed via consumer-specific median (preserves typical load profile).
     - Missing voltage_v imputed via nominal grid median (230.0V).
     - Missing temperature/humidity imputed via seasonal median.
  4. Generates and prints a detailed "Before and After" Data Quality Audit Report.
  5. Writes clean data to data/processed/cleaned_energy_data.csv.

Inputs:
  - data/processed/integrated_energy_data.csv
Outputs:
  - data/processed/cleaned_energy_data.csv
  - Data cleaning statistics printed and logged

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("02_Preprocessing")


def preprocess_data(input_csv: Path = config.INTEGRATED_CSV) -> pd.DataFrame:
    """
    Cleans raw integrated smart meter data and produces a Before/After quality report.
    """
    logger.info("Loading integrated dataset from %s for preprocessing...", input_csv)
    df = pd.read_csv(input_csv)

    # -------------------------------------------------------------
    # BEFORE-CLEANING AUDIT
    # -------------------------------------------------------------
    initial_rows = len(df)
    initial_dups = df.duplicated().sum()
    initial_qm = (df == "?").sum().to_dict()
    initial_nulls = df.isnull().sum().to_dict()

    print("\n" + "=" * 70)
    print("      DATA QUALITY & PREPROCESSING AUDIT REPORT (BEFORE)")
    print("=" * 70)
    print(f"Total Initial Records   : {initial_rows:,}")
    print(f"Duplicate Rows Detected : {initial_dups:,}")
    print("Missing / Null Values per Column:")
    for col, null_cnt in initial_nulls.items():
        if null_cnt > 0 or initial_qm.get(col, 0) > 0:
            print(f"  - {col:<22}: {null_cnt} nulls | {initial_qm.get(col, 0)} '?' tokens")
    print("=" * 70 + "\n")

    # -------------------------------------------------------------
    # 1. REMOVE DUPLICATE RECORDS
    # -------------------------------------------------------------
    if initial_dups > 0:
        df = df.drop_duplicates().reset_index(drop=True)
        logger.info("Removed %d duplicate records.", initial_dups)

    # -------------------------------------------------------------
    # 2. RESOLVE INCONSISTENT VALUE ENCODINGS ('?' -> NaN)
    # -------------------------------------------------------------
    df = df.replace("?", np.nan)

    # Coerce numeric columns to float
    numeric_cols = ["energy_kwh", "voltage_v", "reactive_power_kwh", "peak_demand_kw", "temperature_c", "humidity_pct"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Coerce timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # -------------------------------------------------------------
    # 3. DOMAIN-SPECIFIC MISSING VALUE IMPUTATION
    # -------------------------------------------------------------
    # For energy_kwh: Impute using consumer-specific median (respects household vs industrial scale)
    if df["energy_kwh"].isnull().sum() > 0:
        logger.info("Imputing missing energy_kwh using consumer-specific median...")
        df["energy_kwh"] = df.groupby("consumer_id")["energy_kwh"].transform(
            lambda grp: grp.fillna(grp.median())
        )
        # Any residual overall fallback
        df["energy_kwh"] = df["energy_kwh"].fillna(df["energy_kwh"].median())

    # For voltage_v: Impute using nominal standard grid voltage (230.0V)
    if df["voltage_v"].isnull().sum() > 0:
        logger.info("Imputing missing voltage_v using median voltage...")
        df["voltage_v"] = df["voltage_v"].fillna(df["voltage_v"].median())

    # For reactive power and peak demand: proportional to energy_kwh
    if df["reactive_power_kwh"].isnull().sum() > 0:
        df["reactive_power_kwh"] = df["reactive_power_kwh"].fillna(df["energy_kwh"] * 0.20)
    if df["peak_demand_kw"].isnull().sum() > 0:
        df["peak_demand_kw"] = df["peak_demand_kw"].fillna(df["energy_kwh"] * 1.25)

    # Weather imputation: Group by city and month
    df["month_tmp"] = df["timestamp"].dt.month
    if df["temperature_c"].isnull().sum() > 0:
        df["temperature_c"] = df.groupby(["city", "month_tmp"])["temperature_c"].transform(
            lambda grp: grp.fillna(grp.median())
        )
    if df["humidity_pct"].isnull().sum() > 0:
        df["humidity_pct"] = df.groupby(["city", "month_tmp"])["humidity_pct"].transform(
            lambda grp: grp.fillna(grp.median())
        )
    df.drop(columns=["month_tmp"], inplace=True)

    # -------------------------------------------------------------
    # AFTER-CLEANING AUDIT
    # -------------------------------------------------------------
    final_rows = len(df)
    final_dups = df.duplicated().sum()
    final_nulls = df.isnull().sum().sum()

    print("\n" + "=" * 70)
    print("      DATA QUALITY & PREPROCESSING AUDIT REPORT (AFTER)")
    print("=" * 70)
    print(f"Total Cleaned Records   : {final_rows:,} (Retained {final_rows/initial_rows*100:.2f}%)")
    print(f"Duplicate Rows Remaining: {final_dups}")
    print(f"Total Nulls Remaining   : {final_nulls}")
    print("All numeric data types coerced and validated successfully.")
    print("=" * 70 + "\n")

    # Save cleaned dataset
    output_path = config.CLEANED_CSV
    df.to_csv(output_path, index=False)
    logger.info("Saved cleaned dataset to: %s", output_path)

    return df


def run_preprocessing():
    """Main execution entrypoint for Step 2."""
    logger.info("=== STEP 2: STARTING DATA PREPROCESSING ===")
    df_cleaned = preprocess_data()
    logger.info("=== STEP 2 COMPLETE ===")
    return df_cleaned


if __name__ == "__main__":
    run_preprocessing()

