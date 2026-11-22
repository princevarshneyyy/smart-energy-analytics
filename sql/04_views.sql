-- =====================================================================
-- 04_views.sql
-- Smart Energy Consumption Analytics & Anomaly Detection System
-- Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida
--
-- Purpose:
--   Creates analytical SQL views for instant querying by the Streamlit dashboard
--   and ad-hoc reporting. Pre-joins star schema dimensions for fast response times.
-- =====================================================================

USE smart_energy_dw;

-- -------------------------------------------------------------
-- View 1: vw_daily_consumption
-- Aggregates consumption to daily grain per consumer and city
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vw_daily_consumption AS
SELECT 
    d.full_date,
    d.date_key,
    d.year_number,
    d.month_name,
    d.day_name,
    d.is_weekend,
    d.season,
    c.consumer_id,
    c.consumer_name,
    c.consumer_type,
    l.city,
    l.region,
    ROUND(SUM(f.energy_kwh), 2) AS daily_energy_kwh,
    ROUND(AVG(f.energy_kwh), 3) AS avg_hourly_kwh,
    ROUND(MAX(f.energy_kwh), 2) AS peak_hourly_kwh,
    ROUND(AVG(f.voltage_v), 1) AS avg_daily_voltage,
    ROUND(SUM(f.carbon_emissions_kg), 2) AS daily_carbon_kg
FROM Fact_Energy_Consumption f
JOIN Dim_Date d ON f.date_key = d.date_key
JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
JOIN Dim_Location l ON f.location_key = l.location_key
GROUP BY 
    d.full_date, d.date_key, d.year_number, d.month_name, d.day_name, 
    d.is_weekend, d.season, c.consumer_id, c.consumer_name, c.consumer_type, 
    l.city, l.region;

-- -------------------------------------------------------------
-- View 2: vw_city_monthly_summary
-- High-level overview of grid performance per city and month
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vw_city_monthly_summary AS
SELECT 
    d.year_number,
    d.month_number,
    d.month_name,
    l.city,
    l.region,
    c.consumer_type,
    COUNT(DISTINCT c.consumer_key) AS active_meter_count,
    ROUND(SUM(f.energy_kwh), 2) AS total_consumption_kwh,
    ROUND(AVG(f.energy_kwh), 3) AS avg_consumption_per_hr,
    ROUND(SUM(f.carbon_emissions_kg), 2) AS total_carbon_kg
FROM Fact_Energy_Consumption f
JOIN Dim_Date d ON f.date_key = d.date_key
JOIN Dim_Location l ON f.location_key = l.location_key
JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
GROUP BY 
    d.year_number, d.month_number, d.month_name, l.city, l.region, c.consumer_type;

-- -------------------------------------------------------------
-- View 3: vw_anomaly_investigation_feed
-- Joined view showing flagged anomalies alongside consumer details and reading context
-- -------------------------------------------------------------
CREATE OR REPLACE VIEW vw_anomaly_investigation_feed AS
SELECT 
    a.result_id,
    a.fact_id,
    d.full_date,
    t.time_label,
    t.period_of_day,
    c.consumer_id,
    c.consumer_name,
    c.consumer_type,
    l.city,
    a.energy_kwh,
    a.is_anomaly_iqr,
    a.is_anomaly_zscore,
    a.is_anomaly_kmeans,
    a.anomaly_consensus_count,
    a.investigation_status
FROM Anomaly_Detection_Results a
JOIN Fact_Energy_Consumption f ON a.fact_id = f.fact_id
JOIN Dim_Date d ON a.date_key = d.date_key
JOIN Dim_Time t ON f.time_key = t.time_key
JOIN Dim_Consumer c ON a.consumer_key = c.consumer_key
JOIN Dim_Location l ON f.location_key = l.location_key
WHERE a.anomaly_consensus_count > 0;

