"""
Configuration Module for Smart Energy Analytics & Anomaly Detection System.
Centralizes all paths, database credentials, model hyperparameters, and constants.

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env if present
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------
# DIRECTORY PATHS
# ---------------------------------------------------------
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = BASE_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
MODELS_DIR = OUTPUTS_DIR / "models"
SQL_DIR = BASE_DIR / "sql"
WEKA_DIR = BASE_DIR / "weka"

# Ensure runtime output directories exist
for p in [RAW_DATA_DIR, PROCESSED_DATA_DIR, FIGURES_DIR, TABLES_DIR, MODELS_DIR]:
    p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------
SYNTHETIC_RAW_CSV = RAW_DATA_DIR / "synthetic_energy_data.csv"
UCI_RAW_ZIP = RAW_DATA_DIR / "household_power_consumption.zip"
UCI_RAW_TXT = RAW_DATA_DIR / "household_power_consumption.txt"

INTEGRATED_CSV = PROCESSED_DATA_DIR / "integrated_energy_data.csv"
CLEANED_CSV = PROCESSED_DATA_DIR / "cleaned_energy_data.csv"
FEATURE_ENGINEERED_CSV = PROCESSED_DATA_DIR / "featured_energy_data.csv"
WAREHOUSE_FACT_CSV = PROCESSED_DATA_DIR / "fact_energy_consumption.csv"
ANOMALY_RESULTS_CSV = PROCESSED_DATA_DIR / "anomaly_detection_results.csv"

ARFF_TRAIN_FILE = PROCESSED_DATA_DIR / "energy_classification_train.arff"
ARFF_TEST_FILE = PROCESSED_DATA_DIR / "energy_classification_test.arff"

# ---------------------------------------------------------
# DATABASE CONFIGURATION (MySQL / SQLite Fallback)
# ---------------------------------------------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "smart_energy_dw")

# SQLite fallback path if MySQL server is not locally running
SQLITE_DB_PATH = PROCESSED_DATA_DIR / "smart_energy_dw.sqlite"

# ---------------------------------------------------------
# REPRODUCIBILITY & MODEL HYPERPARAMETERS
# ---------------------------------------------------------
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))

# Classification Quantile Boundaries (applied per consumer type on training data)
LOW_QUANTILE = 0.33
HIGH_QUANTILE = 0.67

# Anomaly Detection Thresholds
ZSCORE_THRESHOLD = float(os.getenv("ANOMALY_ZSCORE_THRESHOLD", 3.0))
IQR_MULTIPLIER = float(os.getenv("ANOMALY_IQR_MULTIPLIER", 1.5))
KMEANS_CLUSTERS = 3
KMEANS_ANOMALY_PERCENTILE = 98.0  # Top 2% distance to centroid flagged as anomaly

