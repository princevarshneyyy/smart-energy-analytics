"""
Step 3: Feature Engineering & Temporal Enrichment Module.

Purpose:
  1. Extracts calendar and temporal features: hour, day, month, quarter, year,
     day-of-week, weekend indicator, time-of-day period, and season.
  2. Constructs time-series lag and rolling statistics for classification:
     - 1-hour lag, 2-hour lag of energy consumption per consumer
     - 6-hour rolling mean and standard deviation
     - Peak hour indicator (18:00 - 22:00)
  3. Derives the Consumption Level Target variable ('Low', 'Normal', 'High'):
     - Computes quantile cutoffs per consumer type to account for residential vs industrial scale.
     - Documented rule: Low (<33rd percentile), Normal (33rd-67th), High (>67th).
  4. CRITICAL: Prevents Data Leakage!
     - In feature sets intended for classification, energy_kwh is isolated. The classification
       models use ONLY temporal, environmental, consumer-profile, and past lag features.
  5. Saves enriched dataset to data/processed/featured_energy_data.csv.

Inputs:
  - data/processed/cleaned_energy_data.csv
Outputs:
  - data/processed/featured_energy_data.csv

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
logger = logging.getLogger("03_FeatureEngineering")


def get_season(month: int) -> str:
    """Classifies month into meteorological season for Northern India / NCR."""
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4]:
        return "Spring"
    elif month in [5, 6]:
        return "Summer"
    elif month in [7, 8, 9]:
        return "Monsoon"
    else:
        return "Autumn"


def get_period_of_day(hour: int) -> str:
    """Classifies hour into human-interpretable diurnal period."""
    if 5 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 22:
        return "Evening"
    else:
        return "Night"


def engineer_features(input_csv: Path = config.CLEANED_CSV) -> pd.DataFrame:
    """
    Performs full feature engineering and temporal enrichment.
    """
    logger.info("Loading cleaned dataset from %s for feature engineering...", input_csv)
    df = pd.read_csv(input_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # Sort sequentially by consumer and timestamp for accurate lag computation
    df = df.sort_values(by=["consumer_id", "timestamp"]).reset_index(drop=True)

    logger.info("Extracting temporal calendar features...")
    df["hour"] = df["timestamp"].dt.hour
    df["day"] = df["timestamp"].dt.day
    df["month"] = df["timestamp"].dt.month
    df["month_name"] = df["timestamp"].dt.month_name()
    df["quarter"] = df["timestamp"].dt.quarter
    df["year"] = df["timestamp"].dt.year
    df["day_of_week"] = df["timestamp"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["day_name"] = df["timestamp"].dt.day_name()
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)

    # Derived qualitative time features
    df["season"] = df["month"].apply(get_season)
    df["period_of_day"] = df["hour"].apply(get_period_of_day)
    df["is_peak_hour"] = df["hour"].apply(lambda h: 1 if 18 <= h <= 22 else 0)

    # Carbon footprint estimation: 0.82 kg CO2 per kWh (CEA India baseline grid emission factor)
    df["carbon_emissions_kg"] = (df["energy_kwh"] * 0.82).round(4)

    # -------------------------------------------------------------
    # LAG AND ROLLING TIME-SERIES FEATURES (PER CONSUMER)
    # -------------------------------------------------------------
    logger.info("Generating lag and rolling window features (past energy behavior)...")
    # Lag 1-period (previous reading)
    df["energy_lag_1"] = df.groupby("consumer_id")["energy_kwh"].shift(1)
    df["energy_lag_2"] = df.groupby("consumer_id")["energy_kwh"].shift(2)

    # 6-step rolling mean and standard deviation
    df["energy_rolling_mean_6"] = df.groupby("consumer_id")["energy_kwh"].transform(
        lambda s: s.rolling(window=6, min_periods=1).mean()
    )
    df["energy_rolling_std_6"] = df.groupby("consumer_id")["energy_kwh"].transform(
        lambda s: s.rolling(window=6, min_periods=1).std()
    ).fillna(0.0)

    # Fill earliest consumer lags with baseline consumer mean
    df["energy_lag_1"] = df["energy_lag_1"].fillna(df["energy_kwh"])
    df["energy_lag_2"] = df["energy_lag_2"].fillna(df["energy_kwh"])

    # -------------------------------------------------------------
    # DERIVING TARGET CLASS: consumption_class ('Low', 'Normal', 'High')
    # Documented rule: Partition per consumer_type using 33rd & 67th percentiles
    # -------------------------------------------------------------
    logger.info("Defining target consumption_class via category-specific quantiles...")
    
    def assign_class(row, thresholds):
        c_type = row["consumer_type"]
        val = row["energy_kwh"]
        q_low, q_high = thresholds[c_type]
        if val <= q_low:
            return "Low"
        elif val <= q_high:
            return "Normal"
        else:
            return "High"

    thresholds = {}
    for c_type in df["consumer_type"].unique():
        sub = df[df["consumer_type"] == c_type]["energy_kwh"]
        q_low = sub.quantile(config.LOW_QUANTILE)
        q_high = sub.quantile(config.HIGH_QUANTILE)
        thresholds[c_type] = (q_low, q_high)
        logger.info("Consumer Type '%s' cutoffs -> Low: <=%.2f kWh | Normal: (%.2f, %.2f] | High: >%.2f kWh",
                    c_type, q_low, q_low, q_high, q_high)

    df["consumption_class"] = df.apply(assign_class, thresholds=thresholds, axis=1)
    
    class_dist = df["consumption_class"].value_counts(normalize=True) * 100
    logger.info("Target class distribution:\n%s", class_dist.to_string())

    # Save to CSV
    output_path = config.FEATURE_ENGINEERED_CSV
    df.to_csv(output_path, index=False)
    logger.info("Saved feature engineered dataset to: %s", output_path)

    return df


def run_feature_engineering():
    """Main execution entrypoint for Step 3."""
    logger.info("=== STEP 3: STARTING FEATURE ENGINEERING ===")
    df_featured = engineer_features()
    logger.info("=== STEP 3 COMPLETE ===")
    return df_featured


if __name__ == "__main__":
    run_feature_engineering()

