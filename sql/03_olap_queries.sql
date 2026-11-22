-- =====================================================================
-- 03_olap_queries.sql
-- Smart Energy Consumption Analytics & Anomaly Detection System
-- Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida
--
-- Purpose:
--   Implements pure-SQL analytical OLAP queries:
--   1. ROLL-UP: Moving from detailed hourly to daily, monthly, and yearly aggregation
--   2. DRILL-DOWN: Navigating from yearly totals down to quarterly, monthly, and city breakdown
--   3. SLICE: Filtering on a single dimension slice (e.g., Only Commercial Consumers)
--   4. DICE: Multi-dimensional sub-cube filter (e.g., Residential consumers in Noida & Delhi during Summer peak hours)
--   5. PIVOT / CUBE: Multi-way aggregation with subtotals using GROUP BY ... WITH ROLLUP
-- =====================================================================

USE smart_energy_dw;

-- -------------------------------------------------------------
-- OPERATION 1: ROLL-UP (Aggregation to higher hierarchy levels)
-- Explanation: Aggregates energy consumption across Year -> Quarter -> Month
-- using WITH ROLLUP to show hierarchical sub-totals.
-- -------------------------------------------------------------
SELECT 
    d.year_number,
    d.quarter_name,
    d.month_name,
    COUNT(f.fact_id) AS total_readings,
    ROUND(SUM(f.energy_kwh), 2) AS total_energy_kwh,
    ROUND(AVG(f.energy_kwh), 3) AS avg_hourly_kwh,
    ROUND(MAX(f.energy_kwh), 2) AS peak_energy_kwh
FROM Fact_Energy_Consumption f
JOIN Dim_Date d ON f.date_key = d.date_key
GROUP BY d.year_number, d.quarter_name, d.month_name WITH ROLLUP;

-- -------------------------------------------------------------
-- OPERATION 2: DRILL-DOWN (Navigating from high-level to detailed)
-- Explanation: Zooms into Year 2023, drilling down into City and Consumer Type
-- to identify localized grid pressure.
-- -------------------------------------------------------------
SELECT 
    d.year_number,
    d.month_name,
    l.city,
    c.consumer_type,
    ROUND(SUM(f.energy_kwh), 2) AS total_energy_kwh,
    ROUND(AVG(f.peak_demand_kw), 2) AS avg_peak_demand_kw,
    ROUND(AVG(f.voltage_v), 1) AS avg_voltage
FROM Fact_Energy_Consumption f
JOIN Dim_Date d ON f.date_key = d.date_key
JOIN Dim_Location l ON f.location_key = l.location_key
JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
WHERE d.year_number = 2023
GROUP BY d.year_number, d.month_name, l.city, c.consumer_type
ORDER BY d.month_name, total_energy_kwh DESC;

-- -------------------------------------------------------------
-- OPERATION 3: SLICE (Fixing ONE dimension)
-- Explanation: Cuts a 2D slice across the cube by fixing Consumer Type = 'Commercial'
-- to inspect commercial energy behavior across seasons and periods of the day.
-- -------------------------------------------------------------
SELECT 
    d.season,
    t.period_of_day,
    t.is_peak_hour,
    ROUND(SUM(f.energy_kwh), 2) AS total_energy_kwh,
    ROUND(AVG(f.energy_kwh), 3) AS avg_hourly_kwh,
    ROUND(SUM(f.carbon_emissions_kg), 2) AS total_carbon_kg
FROM Fact_Energy_Consumption f
JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
JOIN Dim_Date d ON f.date_key = d.date_key
JOIN Dim_Time t ON f.time_key = t.time_key
WHERE c.consumer_type = 'Commercial' -- SLICE CONDITION
GROUP BY d.season, t.period_of_day, t.is_peak_hour
ORDER BY d.season, total_energy_kwh DESC;

-- -------------------------------------------------------------
-- OPERATION 4: DICE (Multi-dimensional sub-cube extraction)
-- Explanation: Extracts a sub-cube by filtering multiple dimensions simultaneously:
-- - Location: Noida, Greater Noida, Delhi
-- - Consumer Type: Residential
-- - Season: Summer
-- - Time: Peak Hours only
-- -------------------------------------------------------------
SELECT 
    l.city,
    d.month_name,
    t.time_label,
    ROUND(SUM(f.energy_kwh), 2) AS total_energy_kwh,
    ROUND(AVG(f.energy_kwh), 3) AS avg_hourly_kwh,
    COUNT(DISTINCT f.consumer_key) AS active_consumers
FROM Fact_Energy_Consumption f
JOIN Dim_Location l ON f.location_key = l.location_key
JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
JOIN Dim_Date d ON f.date_key = d.date_key
JOIN Dim_Time t ON f.time_key = t.time_key
WHERE l.city IN ('Noida', 'Greater Noida', 'Delhi')    -- DIMENSION 1 FILTER
  AND c.consumer_type = 'Residential'                  -- DIMENSION 2 FILTER
  AND d.season = 'Summer'                              -- DIMENSION 3 FILTER
  AND t.is_peak_hour = 1                               -- DIMENSION 4 FILTER
GROUP BY l.city, d.month_name, t.time_label
ORDER BY l.city, total_energy_kwh DESC;

-- -------------------------------------------------------------
-- OPERATION 5: PIVOT / CUBE (City vs Consumer Type Cross-Tabulation)
-- Explanation: Generates a cross-tabulated grid showing total consumption
-- per city partitioned across consumer categories.
-- -------------------------------------------------------------
SELECT 
    l.city,
    ROUND(SUM(CASE WHEN c.consumer_type = 'Residential' THEN f.energy_kwh ELSE 0 END), 2) AS Residential_kWh,
    ROUND(SUM(CASE WHEN c.consumer_type = 'Commercial' THEN f.energy_kwh ELSE 0 END), 2) AS Commercial_kWh,
    ROUND(SUM(CASE WHEN c.consumer_type = 'Industrial' THEN f.energy_kwh ELSE 0 END), 2) AS Industrial_kWh,
    ROUND(SUM(f.energy_kwh), 2) AS Total_kWh
FROM Fact_Energy_Consumption f
JOIN Dim_Location l ON f.location_key = l.location_key
JOIN Dim_Consumer c ON f.consumer_key = c.consumer_key
GROUP BY l.city WITH ROLLUP;

