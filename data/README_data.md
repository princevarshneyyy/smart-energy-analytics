# Data Sources and Schema Guide

## 1. Datasets Used in This Project

This project supports both **real-world benchmark data** from the UCI Machine Learning Repository and a **rich multi-consumer, multi-location synthetic dataset** designed specifically for Star Schema Data Warehousing and OLAP analysis.

### A. Primary Real-World Benchmark: UCI Household Power Consumption
- **Source:** [UCI Machine Learning Repository - Individual Household Electric Power Consumption](https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption)
- **Characteristics:**
  - Collected from a single household in Sceaux, France (Dec 2006 – Nov 2010).
  - 2,075,259 minute-level electrical measurements.
  - Missing values are explicitly encoded with the question mark character `?`.
- **How to download and use the UCI file:**
  1. Download the zip archive `household_power_consumption.zip` from the UCI repository link above.
  2. Place `household_power_consumption.zip` (or the extracted `household_power_consumption.txt`) directly inside `data/raw/`.
  3. When present, `src/01_data_integration.py` detects and aggregates it from minute-level to hourly/daily format.

### B. Multi-Consumer Synthetic Smart Meter Dataset (`synthetic_energy_data.csv`)
- **Generator Script:** `data/generate_synthetic_data.py`
- **Why it is needed:** The UCI benchmark represents only **one household** in **one location**. In order to satisfy the requirements of a true multidimensional Star Schema data warehouse with `Dim_Consumer` and `Dim_Location`, this project includes a physics-based synthetic data generator.
- **Key Characteristics:**
  - **Consumers:** 50 unique smart meters across 3 categories (Residential, Commercial, Industrial).
  - **Geographies:** 6 National Capital Region (NCR) cities: Noida, Greater Noida, Delhi, Gurugram, Ghaziabad, and Faridabad.
  - **Temporal Scope:** 2 full years (2023 to 2024), sampled hourly to model diurnal and seasonal effects.
  - **Physical Modeling:** Realistic diurnal consumption curves (morning/evening peaks for homes; workday peaks for commercial offices), seasonal temperature impacts (air-conditioning cooling load in summer; heating in winter), and nominal grid voltage variations (230V ± 5V).
  - **Deliberate Dirty Data:** Injected missing entries (NaN), UCI-style `?` tokens, and duplicate rows so that `src/02_preprocessing.py` performs rigorous cleaning.
  - **Ground-Truth Benchmark Anomaly:** Injected anomalous spikes (e.g. consumer CONS_001 jumping from 8-15 kWh to 38 kWh) tagged with `is_synthetic_anomaly = 1` for quantitative model evaluation.

---

## 2. Column Dictionary (Raw Synthetic Dataset)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `timestamp` | String (YYYY-MM-DD HH:MM:SS) | Date and hour of smart meter observation |
| `consumer_id` | String (`CONS_001` .. `050`) | Unique natural identifier of the consumer |
| `consumer_name` | String | Consumer descriptive name |
| `consumer_type` | Categorical | Residential, Commercial, or Industrial |
| `tariff_category`| String | Applicable tariff rate category (e.g. Domestic LT, Commercial HT) |
| `connected_load_kw`| Float | Contracted maximum electrical load in kilowatts |
| `city` | String | Location city (e.g., Noida, Delhi) |
| `state` | String | State / Union Territory |
| `region` | String | Grid operational region (North) |
| `pincode` | String | Postal Code |
| `climate_zone` | String | Regional climate classification |
| `contract_start_date` | Date (YYYY-MM-DD) | Date of meter installation/contract |
| `energy_kwh` | Float (Measure) | Active electrical energy consumed during the hour |
| `voltage_v` | Float / String | Meter terminal voltage in Volts (contains dirty `?` values) |
| `reactive_power_kwh`| Float (Measure) | Global reactive power in kilovolt-ampere-reactive |
| `peak_demand_kw` | Float (Measure) | Maximum demand registered during the billing interval |
| `temperature_c` | Float | Ambient outdoor temperature in degrees Celsius |
| `humidity_pct` | Float | Ambient relative humidity percentage |
| `weather_condition` | Categorical | Weather state (Sunny, Cloudy, Rain, Humid, Extreme Heat) |
| `is_synthetic_anomaly` | Integer (0 or 1) | Ground-truth tag indicating injected anomaly for evaluation |

