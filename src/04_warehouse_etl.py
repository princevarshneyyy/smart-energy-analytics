"""
Step 4: Data Warehouse ETL & Star Schema Population Module.

Purpose:
  1. Implements idempotent ETL (safe to re-run multiple times without duplicate keys).
  2. Extracts dimension tables and assigns surrogate keys:
     - Dim_Date: integer surrogate key YYYYMMDD
     - Dim_Time: hour surrogate key 0..23
     - Dim_Consumer: surrogate integer consumer_key
     - Dim_Location: surrogate integer location_key
     - Dim_Weather: surrogate integer weather_key
  3. Constructs the Fact Table: Fact_Energy_Consumption with grain (1 consumer, 1 hour).
  4. Loads star schema tables into the database engine (MySQL or SQLite fallback).
  5. Exports Fact Table CSV to data/processed/fact_energy_consumption.csv.

Inputs:
  - data/processed/featured_energy_data.csv
Outputs:
  - Tables populated in MySQL / SQLite:
    - Dim_Date, Dim_Time, Dim_Consumer, Dim_Location, Dim_Weather, Fact_Energy_Consumption
  - data/processed/fact_energy_consumption.csv

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import pandas as pd
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from src.db_connection import get_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("04_WarehouseETL")


def build_and_load_star_schema(input_csv: Path = config.FEATURE_ENGINEERED_CSV):
    """
    Constructs dimension and fact tables, and writes them to the database.
    """
    logger.info("Reading featured dataset from %s...", input_csv)
    df = pd.read_csv(input_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    engine, dialect = get_db_engine()
    logger.info("Starting ETL load into %s database...", dialect.upper())

    # -------------------------------------------------------------
    # 1. BUILD DIM_DATE
    # -------------------------------------------------------------
    logger.info("Building Dim_Date...")
    dates_df = pd.DataFrame({"full_date": df["timestamp"].dt.date.drop_duplicates()}).sort_values("full_date")
    dates_df["full_date"] = pd.to_datetime(dates_df["full_date"])
    
    dim_date = pd.DataFrame({
        "date_key": dates_df["full_date"].dt.strftime("%Y%m%d").astype(int),
        "full_date": dates_df["full_date"].dt.date,
        "day_of_month": dates_df["full_date"].dt.day,
        "month_number": dates_df["full_date"].dt.month,
        "month_name": dates_df["full_date"].dt.month_name(),
        "quarter_number": dates_df["full_date"].dt.quarter,
        "quarter_name": "Q" + dates_df["full_date"].dt.quarter.astype(str),
        "year_number": dates_df["full_date"].dt.year,
        "day_of_week_num": dates_df["full_date"].dt.dayofweek,
        "day_name": dates_df["full_date"].dt.day_name(),
        "is_weekend": (dates_df["full_date"].dt.dayofweek >= 5).astype(int),
        "season": dates_df["full_date"].dt.month.apply(
            lambda m: "Winter" if m in [12, 1, 2] else ("Spring" if m in [3, 4] else ("Summer" if m in [5, 6] else ("Monsoon" if m in [7, 8, 9] else "Autumn")))
        )
    })

    # -------------------------------------------------------------
    # 2. BUILD DIM_TIME
    # -------------------------------------------------------------
    logger.info("Building Dim_Time...")
    dim_time = pd.DataFrame({
        "time_key": list(range(24)),
        "hour_of_day": list(range(24)),
        "time_label": [f"{h:02d}:00" for h in range(24)],
        "period_of_day": [
            "Morning" if 5 <= h < 12 else ("Afternoon" if 12 <= h < 17 else ("Evening" if 17 <= h < 22 else "Night"))
            for h in range(24)
        ],
        "is_peak_hour": [1 if 18 <= h <= 22 else 0 for h in range(24)]
    })

    # -------------------------------------------------------------
    # 3. BUILD DIM_CONSUMER
    # -------------------------------------------------------------
    logger.info("Building Dim_Consumer...")
    cons_cols = ["consumer_id", "consumer_name", "consumer_type", "tariff_category", "connected_load_kw", "contract_start_date"]
    dim_consumer = df[cons_cols].drop_duplicates().reset_index(drop=True)
    dim_consumer["consumer_key"] = dim_consumer.index + 1
    dim_consumer["meter_type"] = "Smart Meter 3-Phase"

    # Reorder columns
    dim_consumer = dim_consumer[[
        "consumer_key", "consumer_id", "consumer_name", "consumer_type",
        "tariff_category", "connected_load_kw", "meter_type", "contract_start_date"
    ]]

    # -------------------------------------------------------------
    # 4. BUILD DIM_LOCATION
    # -------------------------------------------------------------
    logger.info("Building Dim_Location...")
    loc_cols = ["city", "state", "region", "pincode", "climate_zone"]
    dim_location = df[loc_cols].drop_duplicates().reset_index(drop=True)
    dim_location["location_key"] = dim_location.index + 1
    dim_location = dim_location[["location_key", "city", "state", "region", "pincode", "climate_zone"]]

    # -------------------------------------------------------------
    # 5. BUILD DIM_WEATHER
    # -------------------------------------------------------------
    logger.info("Building Dim_Weather...")
    weather_unique = df[["weather_condition"]].drop_duplicates().reset_index(drop=True)
    weather_unique["weather_key"] = weather_unique.index + 1
    weather_unique["temperature_range"] = "Varied"
    weather_unique["humidity_range"] = "Varied"
    dim_weather = weather_unique[["weather_key", "weather_condition", "temperature_range", "humidity_range"]]

    # -------------------------------------------------------------
    # 6. BUILD FACT TABLE: Fact_Energy_Consumption
    # -------------------------------------------------------------
    logger.info("Mapping foreign keys and constructing Fact_Energy_Consumption...")
    df["date_key"] = df["timestamp"].dt.strftime("%Y%m%d").astype(int)
    df["time_key"] = df["timestamp"].dt.hour

    # Merge foreign keys
    fact_df = df.merge(dim_consumer[["consumer_id", "consumer_key"]], on="consumer_id", how="left")
    fact_df = fact_df.merge(dim_location[["city", "pincode", "location_key"]], on=["city", "pincode"], how="left")
    fact_df = fact_df.merge(dim_weather[["weather_condition", "weather_key"]], on="weather_condition", how="left")

    fact_df["fact_id"] = fact_df.index + 1
    fact_table = fact_df[[
        "fact_id", "date_key", "time_key", "consumer_key", "location_key", "weather_key",
        "energy_kwh", "voltage_v", "reactive_power_kwh", "peak_demand_kw", "carbon_emissions_kg"
    ]].copy()

    # Rename reactive_power_kwh to match SQL schema column name global_reactive_power_kwh
    fact_table.rename(columns={"reactive_power_kwh": "global_reactive_power_kwh"}, inplace=True)

    # -------------------------------------------------------------
    # 7. LOAD INTO DATABASE (Idempotent: drop and recreate or replace)
    # -------------------------------------------------------------
    logger.info("Executing idempotent table writes to database...")
    with engine.begin() as conn:
        dim_date.to_sql("Dim_Date", conn, if_exists="replace", index=False)
        dim_time.to_sql("Dim_Time", conn, if_exists="replace", index=False)
        dim_consumer.to_sql("Dim_Consumer", conn, if_exists="replace", index=False)
        dim_location.to_sql("Dim_Location", conn, if_exists="replace", index=False)
        dim_weather.to_sql("Dim_Weather", conn, if_exists="replace", index=False)
        fact_table.to_sql("Fact_Energy_Consumption", conn, if_exists="replace", index=False)

    logger.info("Warehouse ETL Successfully completed!")
    logger.info("Rows loaded -> Dim_Date: %d, Dim_Time: %d, Dim_Consumer: %d, Dim_Location: %d, Fact: %d",
                len(dim_date), len(dim_time), len(dim_consumer), len(dim_location), len(fact_table))

    # Save Fact CSV for offline exploration and backup
    fact_table.to_csv(config.WAREHOUSE_FACT_CSV, index=False)
    logger.info("Exported Fact Table CSV to: %s", config.WAREHOUSE_FACT_CSV)

    return fact_table


def run_warehouse_etl():
    """Main execution entrypoint for Step 4."""
    logger.info("=== STEP 4: STARTING WAREHOUSE ETL ===")
    fact_table = build_and_load_star_schema()
    logger.info("=== STEP 4 COMPLETE ===")
    return fact_table


if __name__ == "__main__":
    run_warehouse_etl()

