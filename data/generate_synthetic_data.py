"""
Synthetic Multi-Consumer, Multi-Location Energy Dataset Generator.

Purpose:
  Produces a realistic smart meter dataset across 50 consumers and 6 cities over 2 years
  (2023-01-01 to 2024-12-31) at hourly resolution (or sampled hourly/daily).
  Incorporates realistic seasonal patterns, diurnal (time-of-day) curves, weather dynamics,
  and deliberate dirty data (missing values, duplicate rows, anomalous spikes) to give
  the data warehousing and preprocessing pipeline realistic data cleaning work.

Inputs:
  - config.py parameters (RANDOM_SEED, SYNTHETIC_RAW_CSV)
Outputs:
  - data/raw/synthetic_energy_data.csv (Raw multi-consumer electricity dataset)

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("DataGenerator")


def generate_synthetic_energy_dataset() -> pd.DataFrame:
    """
    Generates a multi-consumer, multi-location synthetic smart meter dataset.
    """
    logger.info("Initializing synthetic data generation with seed %d...", config.RANDOM_SEED)
    np.random.seed(config.RANDOM_SEED)

    # 1. Consumer Profiles & Locations
    cities = [
        {"city": "Noida", "state": "Uttar Pradesh", "region": "North", "pincode": "201301", "climate": "Subtropical"},
        {"city": "Greater Noida", "state": "Uttar Pradesh", "region": "North", "pincode": "201310", "climate": "Subtropical"},
        {"city": "Delhi", "state": "Delhi", "region": "North", "pincode": "110001", "climate": "Semi-Arid"},
        {"city": "Gurugram", "state": "Haryana", "region": "North", "pincode": "122001", "climate": "Semi-Arid"},
        {"city": "Ghaziabad", "state": "Uttar Pradesh", "region": "North", "pincode": "201001", "climate": "Subtropical"},
        {"city": "Faridabad", "state": "Haryana", "region": "North", "pincode": "121001", "climate": "Semi-Arid"}
    ]

    consumer_types = ["Residential", "Commercial", "Industrial"]
    consumer_type_weights = [0.60, 0.25, 0.15]  # 60% residential, 25% commercial, 15% industrial

    consumers = []
    num_consumers = 50

    for i in range(1, num_consumers + 1):
        c_id = f"CONS_{i:03d}"
        c_type = np.random.choice(consumer_types, p=consumer_type_weights)
        loc = np.random.choice(cities)

        if c_type == "Residential":
            base_kw = np.random.uniform(1.0, 3.5)
            connected_load = np.random.uniform(4.0, 8.0)
            tariff = "Domestic LT"
        elif c_type == "Commercial":
            base_kw = np.random.uniform(8.0, 20.0)
            connected_load = np.random.uniform(25.0, 60.0)
            tariff = "Commercial HT"
        else:  # Industrial
            base_kw = np.random.uniform(30.0, 80.0)
            connected_load = np.random.uniform(100.0, 250.0)
            tariff = "Industrial HT"

        consumers.append({
            "consumer_id": c_id,
            "consumer_name": f"Consumer {c_id} ({c_type[:3]})",
            "consumer_type": c_type,
            "tariff_category": tariff,
            "connected_load_kw": round(connected_load, 1),
            "base_kw": base_kw,
            "city": loc["city"],
            "state": loc["state"],
            "region": loc["region"],
            "pincode": loc["pincode"],
            "climate_zone": loc["climate"],
            "contract_start_date": f"2022-{np.random.randint(1, 12):02d}-01"
        })

    consumers_df = pd.DataFrame(consumers)

    # 2. Date Range: 2023-01-01 to 2024-12-31
    # For fast execution in college labs while keeping statistical integrity,
    # generate hourly readings sampled systematically across 730 days (2 years).
    # Sample: 2 weeks per quarter across 2 years = 112 days * 24 hours = 2,688 timestamps per consumer
    # Total dataset: 50 consumers * ~2,688 rows = ~134,400 rows (manageable in seconds, deep enough for star schema)
    dates_list = []
    for year in [2023, 2024]:
        for month in range(1, 13):
            # Select 7 sample days per month to give full 24-month span with realistic day-of-week & seasonality
            for day in [3, 7, 12, 16, 20, 25, 28]:
                dates_list.append(pd.Timestamp(year=year, month=month, day=day))

    hours = list(range(24))
    timestamps = [ts.replace(hour=h) for ts in dates_list for h in hours]
    total_timestamps = len(timestamps)

    logger.info("Generating %d timestamps across %d consumers (~%d total readings)...",
                total_timestamps, num_consumers, total_timestamps * num_consumers)

    records = []

    # Diurnal hourly multipliers (24 hours)
    # Residential: peaks 7-9am and 7-10pm
    res_diurnal = np.array([0.4, 0.35, 0.3, 0.3, 0.35, 0.6, 1.2, 1.5, 1.3, 0.9, 0.8, 0.8,
                            0.85, 0.8, 0.8, 0.85, 0.9, 1.2, 1.6, 1.8, 1.7, 1.4, 0.9, 0.6])
    # Commercial: peaks 9am-6pm (office/retail hours)
    com_diurnal = np.array([0.3, 0.3, 0.25, 0.25, 0.3, 0.4, 0.6, 0.8, 1.2, 1.6, 1.7, 1.7,
                            1.6, 1.65, 1.7, 1.65, 1.6, 1.4, 1.1, 0.8, 0.6, 0.5, 0.4, 0.35])
    # Industrial: fairly continuous with day-shift bump
    ind_diurnal = np.array([0.8, 0.75, 0.75, 0.8, 0.85, 0.9, 1.1, 1.25, 1.3, 1.3, 1.25, 1.2,
                            1.2, 1.2, 1.25, 1.25, 1.3, 1.2, 1.1, 1.0, 0.95, 0.9, 0.85, 0.8])

    for _, c in consumers_df.iterrows():
        c_id = c["consumer_id"]
        c_type = c["consumer_type"]
        base_kw = c["base_kw"]

        if c_type == "Residential":
            diurnal = res_diurnal
        elif c_type == "Commercial":
            diurnal = com_diurnal
        else:
            diurnal = ind_diurnal

        for ts in timestamps:
            month = ts.month
            hour = ts.hour
            is_weekend = (ts.weekday() >= 5)

            # Seasonal temperature simulation (Northern India / NCR)
            # Jan: ~14C, May: ~38C, Jul: ~33C, Oct: ~26C
            base_temp = 25 - 11 * np.cos(2 * np.pi * (month - 1) / 12)
            temp = float(base_temp + 5 * np.sin(np.pi * (hour - 6) / 12) + np.random.normal(0, 1.5))
            temp = round(max(5.0, min(48.0, temp)), 1)

            # Humidity (%)
            if month in [7, 8, 9]:  # Monsoon
                humidity = round(np.random.uniform(65, 92), 1)
                condition = "Rain" if np.random.rand() < 0.25 else "Humid"
            elif month in [5, 6]:  # Peak Summer
                humidity = round(np.random.uniform(25, 48), 1)
                condition = "Extreme Heat" if temp > 40 else "Sunny"
            elif month in [12, 1]:  # Winter
                humidity = round(np.random.uniform(40, 75), 1)
                condition = "Cloudy" if np.random.rand() < 0.2 else "Sunny"
            else:
                humidity = round(np.random.uniform(35, 65), 1)
                condition = "Sunny"

            # Energy calculation with realistic physical interactions
            hour_factor = diurnal[hour]
            season_factor = 1.0 + 0.35 * max(0, (temp - 26) / 10)  # AC cooling load above 26C
            if month in [12, 1] and c_type == "Residential":
                season_factor += 0.15  # Winter heating / geyser load

            weekend_factor = 1.15 if (is_weekend and c_type == "Residential") else (
                0.65 if (is_weekend and c_type == "Commercial") else 0.90 if is_weekend else 1.0
            )

            energy = base_kw * hour_factor * season_factor * weekend_factor * np.random.normal(1.0, 0.08)
            energy = max(0.05, round(energy, 4))

            # Voltage simulation (Nominal 230V +- grid variations)
            voltage = round(np.random.normal(230.0, 4.5), 1)
            reactive_power = round(energy * np.random.uniform(0.12, 0.28), 4)
            peak_demand = round(energy * np.random.uniform(1.1, 1.4), 2)

            records.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "consumer_id": c_id,
                "consumer_name": c["consumer_name"],
                "consumer_type": c_type,
                "tariff_category": c["tariff_category"],
                "connected_load_kw": c["connected_load_kw"],
                "city": c["city"],
                "state": c["state"],
                "region": c["region"],
                "pincode": c["pincode"],
                "climate_zone": c["climate_zone"],
                "contract_start_date": c["contract_start_date"],
                "energy_kwh": energy,
                "voltage_v": voltage,
                "reactive_power_kwh": reactive_power,
                "peak_demand_kw": peak_demand,
                "temperature_c": temp,
                "humidity_pct": humidity,
                "weather_condition": condition,
                "is_synthetic_anomaly": 0
            })

    df = pd.DataFrame(records)

    # 3. Deliberately Inject Ground-Truth Synthetic Anomalies
    # Reproduce the exact scenario from problem definition:
    # A consumer who normally uses 8-15 kWh/day suddenly records 38 kWh
    logger.info("Injecting realistic synthetic anomalies (clearly tagged for validation)...")
    anomaly_indices = np.random.choice(len(df), size=int(len(df) * 0.015), replace=False)  # 1.5% anomalies
    df.loc[anomaly_indices, "energy_kwh"] = df.loc[anomaly_indices, "energy_kwh"] * np.random.uniform(3.5, 6.0)
    df.loc[anomaly_indices, "is_synthetic_anomaly"] = 1

    # Specifically ensure consumer CONS_001 records the exact 38 kWh peak anomaly requested
    cons1_idx = df[(df["consumer_id"] == "CONS_001") & (df["energy_kwh"] >= 5.0)].index
    if len(cons1_idx) > 0:
        target_idx = cons1_idx[0]
        df.loc[target_idx, "energy_kwh"] = 38.00
        df.loc[target_idx, "is_synthetic_anomaly"] = 1
        logger.info("Injected benchmark anomaly: CONS_001 recorded 38.00 kWh at %s", df.loc[target_idx, "timestamp"])

    # 4. Insert Dirty Data (Missing Values, Inconsistent Types, and Duplicates)
    # This ensures the Preprocessing module (src/02_preprocessing.py) has genuine cleaning tasks!
    logger.info("Injecting deliberate dirty data: missing values, string '?' tokens, duplicates...")

    # (a) Null values in energy_kwh and voltage_v (~1% rows)
    nan_indices = np.random.choice(len(df), size=int(len(df) * 0.01), replace=False)
    df.loc[nan_indices, "energy_kwh"] = np.nan

    # (b) UCI-style "?" string tokens in voltage_v (~0.8% rows)
    qm_indices = np.random.choice(len(df), size=int(len(df) * 0.008), replace=False)
    df.loc[qm_indices, "voltage_v"] = "?"

    # (c) Duplicate rows (e.g., 250 duplicate readings caused by smart meter retry transmits)
    dup_rows = df.sample(n=250, random_state=config.RANDOM_SEED)
    df = pd.concat([df, dup_rows], ignore_index=True)

    # Save to CSV
    output_path = config.SYNTHETIC_RAW_CSV
    df.to_csv(output_path, index=False)
    logger.info("Synthetic raw dataset successfully written to %s (Total records: %d)", output_path, len(df))

    return df


if __name__ == "__main__":
    generate_synthetic_energy_dataset()

