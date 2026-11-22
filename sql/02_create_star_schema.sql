-- =====================================================================
-- 02_create_star_schema.sql
-- Smart Energy Consumption Analytics & Anomaly Detection System
-- Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida
--
-- Purpose:
--   Creates the Star Schema tables:
--   - Dimension Tables: Dim_Date, Dim_Time, Dim_Consumer, Dim_Location, Dim_Weather
--   - Fact Table: Fact_Energy_Consumption (grain: 1 consumer, 1 hour)
--   - Results Table: Anomaly_Detection_Results
--   Uses surrogate primary keys, explicit foreign keys, indexes, and CASCADE integrity.
-- =====================================================================

USE smart_energy_dw;

-- Disable foreign key checks during schema rebuild
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Anomaly_Detection_Results;
DROP TABLE IF EXISTS Fact_Energy_Consumption;
DROP TABLE IF EXISTS Dim_Weather;
DROP TABLE IF EXISTS Dim_Location;
DROP TABLE IF EXISTS Dim_Consumer;
DROP TABLE IF EXISTS Dim_Time;
DROP TABLE IF EXISTS Dim_Date;

SET FOREIGN_KEY_CHECKS = 1;

-- -------------------------------------------------------------
-- 1. Dim_Date (Date Dimension)
-- Surrogate Key: date_key (YYYYMMDD integer format for high performance)
-- -------------------------------------------------------------
CREATE TABLE Dim_Date (
    date_key INT PRIMARY KEY,               -- e.g. 20230115
    full_date DATE NOT NULL UNIQUE,
    day_of_month TINYINT NOT NULL,
    month_number TINYINT NOT NULL,
    month_name VARCHAR(15) NOT NULL,
    quarter_number TINYINT NOT NULL,
    quarter_name VARCHAR(5) NOT NULL,       -- e.g. Q1, Q2
    year_number SMALLINT NOT NULL,
    day_of_week_num TINYINT NOT NULL,       -- 0=Monday, 6=Sunday
    day_name VARCHAR(15) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    season VARCHAR(15) NOT NULL,            -- Winter, Spring, Summer, Autumn
    INDEX idx_date_year_month (year_number, month_number)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- 2. Dim_Time (Time-of-Day Dimension)
-- Surrogate Key: time_key (0 to 23 representing hours)
-- -------------------------------------------------------------
CREATE TABLE Dim_Time (
    time_key INT PRIMARY KEY,               -- e.g. 0 to 23
    hour_of_day TINYINT NOT NULL UNIQUE,
    time_label VARCHAR(10) NOT NULL,        -- e.g. '00:00', '14:00'
    period_of_day VARCHAR(20) NOT NULL,     -- Night, Morning, Afternoon, Evening, Peak Hours
    is_peak_hour BOOLEAN NOT NULL           -- Peak grid hours (18:00 - 22:00)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- 3. Dim_Consumer (Consumer Profile Dimension)
-- Surrogate Key: consumer_key (Auto-increment integer)
-- Natural Key: consumer_id (e.g. 'CONS_001')
-- -------------------------------------------------------------
CREATE TABLE Dim_Consumer (
    consumer_key INT AUTO_INCREMENT PRIMARY KEY,
    consumer_id VARCHAR(30) NOT NULL UNIQUE,
    consumer_name VARCHAR(100) NOT NULL,
    consumer_type VARCHAR(30) NOT NULL,     -- Residential, Commercial, Industrial
    tariff_category VARCHAR(30) NOT NULL,   -- Domestic LT, Commercial HT, Industrial HT
    connected_load_kw DECIMAL(8, 2) NOT NULL,
    meter_type VARCHAR(20) DEFAULT 'Smart Meter 3-Phase',
    contract_start_date DATE NOT NULL,
    INDEX idx_consumer_type (consumer_type)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- 4. Dim_Location (Geographic Dimension)
-- Surrogate Key: location_key (Auto-increment integer)
-- -------------------------------------------------------------
CREATE TABLE Dim_Location (
    location_key INT AUTO_INCREMENT PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    region VARCHAR(30) NOT NULL,            -- North, South, East, West, Central
    pincode VARCHAR(10) NOT NULL,
    climate_zone VARCHAR(30) NOT NULL,
    UNIQUE KEY uk_loc_city_pin (city, pincode)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- 5. Dim_Weather (Weather Dimension)
-- Surrogate Key: weather_key (Auto-increment integer)
-- -------------------------------------------------------------
CREATE TABLE Dim_Weather (
    weather_key INT AUTO_INCREMENT PRIMARY KEY,
    weather_condition VARCHAR(30) NOT NULL,  -- Sunny, Rain, Cloudy, Humid, Extreme Heat
    temperature_range VARCHAR(30) NOT NULL,  -- Cold (<15C), Mild (15-25C), Warm (25-35C), Hot (>35C)
    humidity_range VARCHAR(30) NOT NULL      -- Low (<40%), Medium (40-70%), High (>70%)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- 6. Fact_Energy_Consumption (Fact Table)
-- Grain: One record per consumer per hour (Single Consumer x Single Hour)
-- -------------------------------------------------------------
CREATE TABLE Fact_Energy_Consumption (
    fact_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    date_key INT NOT NULL,
    time_key INT NOT NULL,
    consumer_key INT NOT NULL,
    location_key INT NOT NULL,
    weather_key INT NOT NULL,
    
    -- Measures
    energy_kwh DECIMAL(10, 4) NOT NULL,
    voltage_v DECIMAL(6, 2) NOT NULL,
    global_reactive_power_kwh DECIMAL(8, 4) DEFAULT 0.0,
    peak_demand_kw DECIMAL(8, 2) NOT NULL,
    carbon_emissions_kg DECIMAL(8, 4) NOT NULL, -- energy_kwh * 0.82 (standard emission factor)

    -- Flags & Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Foreign Keys
    CONSTRAINT fk_fact_date FOREIGN KEY (date_key) REFERENCES Dim_Date(date_key) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_time FOREIGN KEY (time_key) REFERENCES Dim_Time(time_key) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_consumer FOREIGN KEY (consumer_key) REFERENCES Dim_Consumer(consumer_key) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_location FOREIGN KEY (location_key) REFERENCES Dim_Location(location_key) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_fact_weather FOREIGN KEY (weather_key) REFERENCES Dim_Weather(weather_key) ON DELETE RESTRICT ON UPDATE CASCADE,

    -- High performance analytical indexes
    INDEX idx_fact_date_consumer (date_key, consumer_key),
    INDEX idx_fact_location_date (location_key, date_key),
    INDEX idx_fact_consumer_time (consumer_key, time_key)
) ENGINE=InnoDB;

-- -------------------------------------------------------------
-- 7. Anomaly_Detection_Results (Separate analytical results table)
-- Architectural note: Separating anomaly flags keeps the fact table lean
-- and allows appending new model runs without altering historical fact rows.
-- -------------------------------------------------------------
CREATE TABLE Anomaly_Detection_Results (
    result_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    fact_id BIGINT NOT NULL,
    date_key INT NOT NULL,
    consumer_key INT NOT NULL,
    energy_kwh DECIMAL(10, 4) NOT NULL,
    is_anomaly_iqr BOOLEAN NOT NULL DEFAULT 0,
    is_anomaly_zscore BOOLEAN NOT NULL DEFAULT 0,
    is_anomaly_kmeans BOOLEAN NOT NULL DEFAULT 0,
    anomaly_consensus_count TINYINT NOT NULL DEFAULT 0, -- Sum of flags (0 to 3)
    investigation_status VARCHAR(30) DEFAULT 'Needs Investigation',
    detection_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_anom_fact FOREIGN KEY (fact_id) REFERENCES Fact_Energy_Consumption(fact_id) ON DELETE CASCADE,
    INDEX idx_anom_consensus (anomaly_consensus_count)
) ENGINE=InnoDB;

