# Data Warehouse Design & Dimensional Modeling

## 1. Dimensional Modeling Rationale

A **Star Schema** was chosen for this energy analytics warehouse. In multidimensional data warehousing, star schemas are preferred over 3NF (Third Normal Form) or snowflake schemas because:
1. **Simplified Navigation:** Fact-to-dimension relationships are direct (1-hop joins).
2. **Optimal OLAP Query Performance:** Relational database query optimizers execute star joins efficiently using bitmap indexes and hash joins.
3. **Intuitive for Business Analysts:** Fact measures and descriptive dimensional attributes map cleanly to business entities.

---

## 2. Fact Table Definition & Grain

- **Fact Table Name:** `Fact_Energy_Consumption`
- **Grain:** **One individual consumer meter reading per one calendar hour.**
  - *Example:* Consumer `CONS_001` on date `2023-05-12` at hour `14:00`.
- **Measures (Numeric Additive & Semi-Additive Facts):**
  - `energy_kwh`: Active electricity consumed during the hour (Additive across time and consumers).
  - `voltage_v`: Terminal voltage measured in volts (Non-additive; summarized via Average, Min, Max).
  - `global_reactive_power_kwh`: Reactive power consumed (Additive).
  - `peak_demand_kw`: Maximum instantaneous power spike in that hour interval (Semi-additive; summarized via Max).
  - `carbon_emissions_kg`: Estimated CO2 emissions computed as `energy_kwh * 0.82` (Additive).

---

## 3. Dimension Tables

1. **Dim_Date (Temporal Date Dimension):**
   - **Surrogate Key:** `date_key` (Format: `YYYYMMDD` integer, e.g., `20230512`).
   - **Attributes:** `full_date`, `day_of_month`, `month_number`, `month_name`, `quarter_number`, `quarter_name`, `year_number`, `day_of_week_num`, `day_name`, `is_weekend`, `season`.
2. **Dim_Time (Time-of-Day Dimension):**
   - **Surrogate Key:** `time_key` (Integer: 0 to 23).
   - **Attributes:** `hour_of_day`, `time_label` (`14:00`), `period_of_day` (`Afternoon`), `is_peak_hour` (`1` if 18-22 hrs).
3. **Dim_Consumer (Consumer Profile Dimension):**
   - **Surrogate Key:** `consumer_key` (Auto-increment integer).
   - **Natural Key:** `consumer_id` (`CONS_001`).
   - **Attributes:** `consumer_name`, `consumer_type` (Residential, Commercial, Industrial), `tariff_category`, `connected_load_kw`, `meter_type`, `contract_start_date`.
4. **Dim_Location (Geographic Dimension):**
   - **Surrogate Key:** `location_key` (Auto-increment integer).
   - **Attributes:** `city`, `state`, `region`, `pincode`, `climate_zone`.
5. **Dim_Weather (Environmental Dimension):**
   - **Surrogate Key:** `weather_key` (Auto-increment integer).
   - **Attributes:** `weather_condition`, `temperature_range`, `humidity_range`.

---

## 4. Entity-Relationship (ER) Star Schema Diagram

```mermaid
erDiagram
    Dim_Date ||--o{ Fact_Energy_Consumption : "occurs_on"
    Dim_Time ||--o{ Fact_Energy_Consumption : "at_hour"
    Dim_Consumer ||--o{ Fact_Energy_Consumption : "recorded_by"
    Dim_Location ||--o{ Fact_Energy_Consumption : "located_at"
    Dim_Weather ||--o{ Fact_Energy_Consumption : "under_weather"
    Fact_Energy_Consumption ||--o{ Anomaly_Detection_Results : "evaluated_in"

    Dim_Date {
        int date_key PK
        date full_date
        int month_number
        string month_name
        string quarter_name
        int year_number
        string day_name
        boolean is_weekend
        string season
    }

    Dim_Time {
        int time_key PK
        int hour_of_day
        string time_label
        string period_of_day
        boolean is_peak_hour
    }

    Dim_Consumer {
        int consumer_key PK
        string consumer_id NK
        string consumer_name
        string consumer_type
        string tariff_category
        decimal connected_load_kw
    }

    Dim_Location {
        int location_key PK
        string city
        string state
        string region
        string pincode
        string climate_zone
    }

    Dim_Weather {
        int weather_key PK
        string weather_condition
        string temperature_range
        string humidity_range
    }

    Fact_Energy_Consumption {
        bigint fact_id PK
        int date_key FK
        int time_key FK
        int consumer_key FK
        int location_key FK
        int weather_key FK
        decimal energy_kwh
        decimal voltage_v
        decimal peak_demand_kw
        decimal carbon_emissions_kg
    }

    Anomaly_Detection_Results {
        bigint result_id PK
        bigint fact_id FK
        int consumer_key FK
        boolean is_anomaly_iqr
        boolean is_anomaly_zscore
        boolean is_anomaly_kmeans
        int anomaly_consensus_count
        string investigation_status
    }
```

---

## 5. Architectural Decision: Separate Anomaly Results Table

Notice that `Anomaly_Detection_Results` is maintained as a separate table linked by `fact_id` rather than cluttering `Fact_Energy_Consumption`.
- **Reason 1 (Idempotent Experimentation):** Machine learning models and anomaly algorithms can be retrained or replaced without modifying historical immutable fact table records.
- **Reason 2 (Lean Fact Storage):** Keeping facts clean ensures fast OLAP scans and low storage overhead.

