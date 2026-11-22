# System Architecture: End-to-End Data Pipeline

## 1. High-Level Architectural Flowchart

```
+---------------------------------------------------------------------------------------------+
|                                    1. DATA INGESTION & RAW STORAGE                           |
|  - UCI Household Power Consumption Benchmark (archive.ics.uci.edu)                          |
|  - Synthetic Multi-Consumer Grid Generator (data/generate_synthetic_data.py)                |
+---------------------------------------------------------------------------------------------+
                                              |
                                              v
+---------------------------------------------------------------------------------------------+
|                                    2. DATA CLEANING & AUDIT (src/02_preprocessing.py)       |
|  - Removal of smart meter duplicate retransmissions                                         |
|  - Type coercion: '?' sentinel values coerced to NaN                                        |
|  - Consumer-specific median imputation for energy_kwh; nominal grid median for voltage_v    |
|  - Generates Before/After data quality audit report                                         |
+---------------------------------------------------------------------------------------------+
                                              |
                                              v
+---------------------------------------------------------------------------------------------+
|                           3. FEATURE ENGINEERING & ENRICHMENT (src/03_feature_engineering.py)|
|  - Calendar features: hour, day, month, season, peak-hour flag (18-22 hrs)                  |
|  - Historical lag features: energy_lag_1, energy_lag_2, 6-period rolling mean & std         |
|  - Target Class: Low / Normal / High (consumer-type quantile cutoffs)                        |
|  - ZERO DATA LEAKAGE ENFORCEMENT: energy_kwh is isolated from model training features       |
+---------------------------------------------------------------------------------------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
+-----------------------------------------+   +-----------------------------------------------+
| 4. DATA WAREHOUSE & STAR SCHEMA (ETL)   |   | 6 & 7. MINING & MACHINE LEARNING MODELS       |
| (src/04_warehouse_etl.py)               |   |                                               |
| - Dimensions:                           |   | - Supervised Classification (src/06):         |
|   * Dim_Date (date_key YYYYMMDD)        |   |   * Decision Tree (CART / C4.5 analog)        |
|   * Dim_Time (hour_key 0..23)           |   |   * Naive Bayes (GaussianNB)                  |
|   * Dim_Consumer (surrogate keys)       |   |   * k-Nearest Neighbors (kNN)                 |
|   * Dim_Location (cities, pincodes)     |   |   * Support Vector Machine (LinearSVC)        |
|   * Dim_Weather (weather_key)           |   |   * Time-aware chronological train/test split |
| - Fact Table:                           |   |   * Hyperparameter tuning via GridSearchCV    |
|   * Fact_Energy_Consumption             |   |                                               |
|     (Grain: 1 consumer x 1 hour)        |   | - Unsupervised Anomaly Detection (src/07):    |
| - Separate Results Table:               |   |   * Interquartile Range (IQR per consumer)    |
|   * Anomaly_Detection_Results           |   |   * Z-Score rule (|Z| > 3.0 per consumer)     |
| - Target RDBMS: MySQL (SQLite fallback) |   |   * K-Means clustering centroid distance      |
+-----------------------------------------+   +-----------------------------------------------+
                     |                                                 |
                     v                                                 v
+-----------------------------------------+   +-----------------------------------------------+
| 5. OLAP ANALYTICAL ENGINE               |   | 8 & 9. EVALUATION & WEKA EXPORTER             |
| (src/05_olap_operations.py)             |   | (src/08_model_evaluation.py & 09_export_arff) |
| - Roll-up (Hour -> Day -> Month -> Year)|   | - Confusion matrices & comparison charts      |
| - Drill-down (Year -> City -> Sector)   |   | - Synthetic anomaly validation & consensus    |
| - Slice (Consumer Type = Commercial)    |   | - WEKA .arff generation for train/test splits |
| - Dice (Noida/Delhi + Res + Summer)     |   +-----------------------------------------------+
| - Pivot / Cube View (City vs Sector)    |                            |
+-----------------------------------------+                            |
                     |                                                 |
                     +------------------------+------------------------+
                                              |
                                              v
+---------------------------------------------------------------------------------------------+
|                                    10. INTERACTIVE STREAMLIT DASHBOARD                      |
|                                         (dashboard/app.py)                                  |
|  - Page 1: High-level KPIs, daily/monthly temporal trends, carbon metrics                   |
|  - Page 2: Interactive OLAP Data Cube Explorer (Roll-up, Drill-down, Slice, Dice, Pivot)    |
|  - Page 3: Supervised Classification Leaderboard, Confusion Matrices, and Comparisons      |
|  - Page 4: Anomaly Alert Console with time-series markers & field inspection tables         |
+---------------------------------------------------------------------------------------------+
```

---

## 2. Key Architectural Tenets

1. **Modularity (Single Responsibility Principle):**
   Every file in `src/` executes exactly one stage of the pipeline. No monolith scripts.
2. **Strict Freedom from Target Data Leakage:**
   When predicting consumption level (`Low`, `Normal`, `High`), the current timestamp's active power (`energy_kwh`) is excluded from model feature sets. The models use calendar cues, weather, consumer capacity, and *past* consumption lags.
3. **Reproducibility:**
   All synthetic generation, k-fold splits, clustering initializations, and model training enforce `RANDOM_SEED = 42`.
4. **Idempotence:**
   ETL and preprocessing scripts can be rerun safely without creating duplicate database rows or duplicate keys.

