-- =====================================================================
-- 01_create_database.sql
-- Smart Energy Consumption Analytics & Anomaly Detection System
-- Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida
--
-- Purpose:
--   Creates the dedicated relational database for the Smart Energy
--   Data Warehouse. Sets character encoding to UTF8mb4 for unicode compatibility.
-- =====================================================================

CREATE DATABASE IF NOT EXISTS smart_energy_dw
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE smart_energy_dw;

