# Smart Energy Consumption Analytics & Anomaly Detection System

A complete, production-grade, modular Data Mining and Data Warehousing laboratory project for 3rd-year B.Tech CSE students at Jaypee Institute of Information Technology (JIIT), Noida.

**Course:** Data Mining and Warehousing Lab (24B15CS313)  
**Project Title:** Smart Energy Consumption Analytics & Anomaly Detection System  
**Author:** 3rd-Year B.Tech CSE Student, JIIT Noida

---

## 1. Project Overview & Architecture

Electricity consumption data is generated continuously by households, commercial facilities, and manufacturing industries. Managing and optimizing power delivery requires an integrated end-to-end analytics platform that cleans incoming smart meter feeds, models consumption in a multidimensional data warehouse, enables fast OLAP slicing, classifies usage patterns, detects unusual anomalies, and visualizes insights via an interactive dashboard.

```
[Raw Ingestion]           [Data Cleaning]           [Star Schema Warehouse]         [Mining & ML]             [Analytics Console]
UCI Benchmark    ===>     Duplicates Removed ===>   Dim_Date, Dim_Time       ===>   Decision Tree, NB   ===>  Streamlit App
Synthetic Grid            '?' Coerced to NaN        Dim_Consumer, Location          kNN, Linear SVM           Interactive OLAP
(50 Consumers)            Median Imputation         Fact_Energy_Consumption         IQR, Z-Score, KMeans      Anomaly Alerts
```

---

## 2. Directory Structure

```
smart-energy-analytics/
├── README.md                      # Complete project documentation and guide
├── requirements.txt               # Python package dependencies
├── .env.example                   # Environment variable template
├── config.py                      # Centralized configuration and paths
├── run_pipeline.py                # Idempotent master pipeline orchestrator
│
├── data/
│   ├── raw/                       # Raw input CSVs and UCI archives
│   ├── processed/                 # Cleaned datasets and WEKA ARFF files
│   ├── generate_synthetic_data.py # Multi-consumer synthetic grid generator
│   └── README_data.md             # Dataset documentation and column guide
│
├── sql/
│   ├── 01_create_database.sql     # Database initialization script
│   ├── 02_create_star_schema.sql  # Star schema DDL (Fact & Dimension tables)
│   ├── 03_olap_queries.sql        # Pure-SQL OLAP operations (Roll-up, Slice, etc.)
│   └── 04_views.sql              # Pre-aggregated analytical SQL views
│
├── src/
│   ├── __init__.py
│   ├── db_connection.py           # SQLAlchemy manager (MySQL with SQLite fallback)
│   ├── 01_data_integration.py     # Data integration and schema alignment
│   ├── 02_preprocessing.py        # Data cleaning and before/after quality audit
│   ├── 03_feature_engineering.py  # Lag features, class derivation, zero leakage
│   ├── 04_warehouse_etl.py        # Star schema ETL with surrogate keys
│   ├── 05_olap_operations.py      # Roll-up, Drill-down, Slice, Dice, Pivot
│   ├── 06_classification.py       # Decision Tree, Naive Bayes, kNN, Linear SVM
│   ├── 07_anomaly_detection.py    # IQR, Z-Score, K-Means clustering per consumer
│   ├── 08_model_evaluation.py     # Confusion matrices, comparison charts, reports
│   └── 09_export_arff.py          # Standard WEKA ARFF dataset generator
│
├── dashboard/
│   ├── app.py                     # Streamlit entrypoint and system overview
│   ├── pages/
│   │   ├── 1_Overview.py          # KPIs, daily/monthly temporal trends
│   │   ├── 2_OLAP_Explorer.py     # Interactive roll-up, drill-down, slice, dice
│   │   ├── 3_Classification.py    # Classifier leaderboard & confusion matrices
│   │   └── 4_Anomaly_Alerts.py    # Anomaly alert table & highlighted time-series
│   └── utils.py                   # Cached data fetchers and shared utilities
│
├── weka/
│   └── WEKA_INSTRUCTIONS.md       # Step-by-step WEKA Explorer GUI walkthrough
│
├── notebooks/
│   └── exploration.ipynb          # Exploratory Data Analysis (EDA) notebook
│
├── outputs/
│   ├── figures/                   # Confusion matrices, comparison bar charts
│   ├── tables/                    # CSV performance metrics and reports
│   └── models/                    # Serialized model artifacts (.joblib)
│
└── docs/
    ├── 01_architecture.md         # Detailed pipeline data flow diagram
    ├── 02_data_warehouse_design.md# Star schema documentation & Mermaid ER diagram
    ├── 03_file_by_file_guide.md   # File guide with one-line defenses for teachers
    ├── 04_algorithms_explained.md # Mathematical explanations & formulas
    ├── 05_viva_questions.md       # 32 model viva voce questions & answers
    └── 06_demo_script.md          # 5-minute lab presentation script
```

---

## 3. Tech Stack

- **Programming Language:** Python 3.10+
- **Data Processing & Engineering:** Pandas, NumPy
- **Machine Learning & Data Mining:** Scikit-Learn, WEKA (ARFF exports)
- **Database Engine:** MySQL 8.0+ (PyMySQL + SQLAlchemy) with automatic SQLite fallback
- **Visual Analytics:** Matplotlib, Seaborn, Plotly
- **Interactive Web Dashboard:** Streamlit

---

## 4. Setup & Installation Instructions

### Step 1: Clone or Navigate to Project Directory
```bash
cd /Users/princevarshney/projects/smart-energy-analytics
```

### Step 2: Create and Activate Virtual Environment (Recommended)
```bash
python3 -m venv venv
# On macOS / Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Database (Optional)
If you have MySQL running locally, create `.env` from the example template:
```bash
cp .env.example .env
```
Update your MySQL credentials in `.env`:
```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=smart_energy_dw
```
*Note: If MySQL is not running or credentials are not supplied, the system automatically runs seamlessly using embedded SQLite (`data/processed/smart_energy_dw.sqlite`) without throwing errors.*

---

## 5. Execution Order

### Option A: Run Entire Pipeline in One Command
```bash
python run_pipeline.py
```

### Option B: Execute Steps Individually (For Explaining to Teacher)
```bash
# 1. Integrate raw inputs & synthetic grid
python src/01_data_integration.py

# 2. Clean dirty data & view Quality Audit Report
python src/02_preprocessing.py

# 3. Engineer temporal features & derive target class
python src/03_feature_engineering.py

# 4. Populate Star Schema Warehouse tables
python src/04_warehouse_etl.py

# 5. Execute OLAP operations (Roll-up, Drill-down, Slice, Dice, Pivot)
python src/05_olap_operations.py

# 6. Train Decision Tree, Naive Bayes, kNN, and SVM models
python src/06_classification.py

# 7. Run IQR, Z-Score, and K-Means anomaly detectors
python src/07_anomaly_detection.py

# 8. Generate confusion matrices & evaluation charts
python src/08_model_evaluation.py

# 9. Export ARFF files for WEKA
python src/09_export_arff.py
```

### Option C: Launch Interactive Streamlit Dashboard
```bash
streamlit run dashboard/app.py
```

---

## 6. Key Design Highlights

1. **Grain of Fact Table:** One individual consumer reading per one hour (`Fact_Energy_Consumption`).
2. **Zero Data Leakage:** When predicting consumption class (`Low`, `Normal`, `High`), the current timestamp's active power (`energy_kwh`) is strictly excluded from features.
3. **Domain-Specific Anomaly Detection:** IQR and Z-scores are computed **per consumer**, preserving personal baselines so that industrial loads are not falsely flagged and residential surges are detected.
4. **Wording Standard:** Anomalies are explicitly labeled as *"unusual readings that need investigation"*, avoiding unverified claims of energy theft.
5. **Benchmark Verification:** Reproduces the test case where Consumer `CONS_001` jumps from 8-15 kWh to 38 kWh, successfully flagged across all three detectors.

