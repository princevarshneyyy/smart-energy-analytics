# Streamlit Cloud Free Deployment Guide

This guide provides step-by-step instructions to deploy the **Smart Energy Consumption Analytics & Anomaly Detection System** for free on **Streamlit Community Cloud** (`share.streamlit.io`) without requiring a paid or hosted MySQL server.

Course: *Data Mining and Warehousing Lab (24B15CS313)*, JIIT Noida.

---

## 1. How the Cloud Deployment Works

In local laboratory environments, the project connects to a live MySQL instance via SQLAlchemy and PyMySQL. For cloud hosting, Streamlit Community Cloud runs in ephemeral serverless containers where running a persistent local MySQL service is not supported.

To solve this cleanly, this repository implements an **automatic dual-mode data architecture**:
1. **Primary Mode (Live MySQL):** If MySQL connection credentials exist (via `.env` or Streamlit Secrets) and the MySQL server is reachable, the dashboard queries live MySQL star schema tables.
2. **Fallback Mode (Exported Offline Warehouse):** If MySQL is unreachable, the dashboard automatically loads from `deploy_data/`:
   - Queries `deploy_data/smart_energy_dw.sqlite` using SQLAlchemy/SQLite.
   - Computes all OLAP aggregations (Roll-up, Drill-down, Slice, Dice, and Pivot) in-memory with Pandas.
   - Preserves all 50 consumers, geographic distributions, model diagnostic plots, and benchmark anomaly alerts.
   - Displays a badge in the sidebar: `📦 Data Source: Exported warehouse data`.

The total size of `deploy_data/` is ~33 MB, well within GitHub's 100 MB file limit and Streamlit's 1 GB container memory envelope.

---

## 2. Step-by-Step Deployment Instructions

### Step 1: Generate or Refresh Deployment Assets Locally
Before pushing to GitHub, run the warehouse export script once to ensure `deploy_data/` contains all tables and views:
```bash
python src/10_export_deploy_data.py
```
*Expected terminal output:*
```
[INFO] DEPLOY DATA EXPORT COMPLETE! Total folder size: ~33 MB (< 50 MB target)
```

### Step 2: Test Fallback Mode Locally (With MySQL Stopped)
To guarantee your app will run seamlessly in the cloud:
1. Ensure MySQL is stopped, or set invalid dummy DB credentials in `.env`.
2. Launch the Streamlit dashboard locally:
   ```bash
   streamlit run dashboard/app.py
   ```
3. Open `http://localhost:8501` in your browser.
4. Verify:
   - Sidebar displays: `📦 Data Source: Exported warehouse data`.
   - Page 1 (Overview): KPIs and trend charts render without errors.
   - Page 2 (OLAP Explorer): All 5 tabs (Roll-Up, Drill-Down, Slice, Dice, Pivot) compute instantly.
   - Page 3 (Classification): Leaderboard, confusion matrices, and model comparison chart display.
   - Page 4 (Anomaly Alerts): Time-series chart highlights unusual readings (e.g. `CONS_001` 38 kWh spike).

### Step 3: Commit and Push Changes to GitHub
Push your deployment branch or merge it into `main`:
```bash
git add .
git commit -m "feat: configure zero-config cloud deployment assets and dual-mode data loading"
git push origin deployment
```
*(If you wish to deploy directly from main, merge `deployment` into `main` and push).*

### Step 4: Deploy on Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
2. Click **Create app** (or **New app**).
3. Fill in the deployment form:
   - **Repository:** `princevarshneyyy/smart-energy-analytics`
   - **Branch:** `deployment` (or `main`)
   - **Main file path:** `dashboard/app.py`
   - **App URL (optional):** Choose a custom subdomain (e.g., `smart-energy-analytics.streamlit.app`).
4. Click **Deploy!**
5. Streamlit Cloud will install packages from `requirements.txt` and launch the app in 1 to 2 minutes.

---

## 3. Optional: Connecting to a Hosted MySQL Server (Streamlit Secrets)

If you ever wish to connect the cloud deployment to a live hosted MySQL server (e.g., AWS RDS, Aiven, PlanetScale, or Clever Cloud):
1. Go to your app dashboard at `share.streamlit.io`.
2. Click the three dots `⋮` next to your app -> **Settings** -> **Secrets**.
3. Paste your credentials into the TOML editor:
   ```toml
   [mysql]
   host = "your-remote-db-host.com"
   port = 3306
   user = "your_db_username"
   password = "your_db_password"
   database = "smart_energy_dw"
   ```
4. Click **Save**. Streamlit will automatically restart the app and connect to your live MySQL database, switching the sidebar badge to `🟢 Data Source: Live MySQL warehouse`.

---

## 4. How to Wake a Sleeping App Before a Demo

Streamlit Community Cloud automatically puts inactive apps to sleep after several days of inactivity to conserve free server resources.

**Before your college viva or teacher demonstration:**
1. Open your public Streamlit app URL 10 minutes before the demo.
2. If the app is asleep, you will see a screen saying: *"This app has gone to sleep due to inactivity"*.
3. Click the blue **"Yes, get this app back up!"** button.
4. The container will wake up and load within 30 to 45 seconds.
5. Once loaded, click through the 4 pages once to warm up Streamlit's `@st.cache_data` memory cache for instant, snappy transitions during your presentation.

---

## 5. Common Cloud Deployment Errors & Fixes

### Error 1: `ModuleNotFoundError: No module named 'XYZ'`
- **Cause:** A package was imported in Python code but not listed in `requirements.txt`.
- **Fix:** Check `requirements.txt`. All dashboard dependencies (`streamlit`, `pandas`, `numpy`, `plotly`, `scikit-learn`, `matplotlib`, `seaborn`, `pillow`, `sqlalchemy`, `pymysql`, `python-dotenv`, `joblib`) are explicitly pinned.

### Error 2: `FileNotFoundError: No such file or directory: '...'`
- **Cause:** Using hard-coded OS paths (like `C:\Users\...` or `/home/...`).
- **Fix:** Always use Python's `pathlib.Path(__file__).resolve().parent` to resolve paths relative to repository root. This is already implemented across all scripts.

### Error 3: `Streamlit server exceeded resource limits (OOM - Out of Memory)`
- **Cause:** Attempting to load uncompressed 200,000+ raw time-series rows with dozens of feature columns simultaneously on free 1 GB RAM containers.
- **Fix:** In fallback mode, `deploy_data/fact_daily_summary.csv` and optimized `deploy_data/anomaly_detection_results.csv` contain pre-filtered, rounded measures that load in under 150 MB of memory.

### Error 4: App crashes because MySQL is not installed
- **Cause:** Unchecked DB connection calls throwing uncaught exceptions.
- **Fix:** `dashboard/utils.py` handles database imports and connection attempts inside safe `try-except` blocks. If MySQL fails, it gracefully falls back to `deploy_data/` without crashing.
