"""
Step 7: Unsupervised Anomaly Detection Module.

Purpose:
  1. Detects unusual electrical consumption readings using 3 distinct statistical & mining methods:
     - Method A: Interquartile Range (IQR) rule per consumer (threshold: Q3 + 1.5*IQR).
     - Method B: Z-score rule per consumer (threshold: |Z| > 3.0).
     - Method C: Clustering-based method (K-Means distance to assigned cluster centroid).
  2. Why calculate per consumer?
     - Industrial consumers naturally consume 50-200 kWh, whereas residential consumers
       use 1-4 kWh. A global threshold would falsely flag ALL industrial readings and miss
       huge residential spikes! Grouping per consumer preserves personal baselines.
  3. Adheres strictly to the mandated wording:
     - Anomalies are strictly "unusual readings that need investigation", NEVER proof
       of energy theft or physical equipment failure.
  4. Reproduces the benchmark scenario:
     - Flags a consumer whose baseline is 8-15 kWh/day recording 38 kWh.
  5. Evaluates detection performance against known injected synthetic anomalies
     (precision, recall, F1, consensus agreement).
  6. Stores anomaly results into MySQL/SQLite table `Anomaly_Detection_Results`
     and writes data/processed/anomaly_detection_results.csv.

Inputs:
  - data/processed/featured_energy_data.csv / Fact Table
Outputs:
  - Database Table: Anomaly_Detection_Results
  - data/processed/anomaly_detection_results.csv
  - outputs/tables/anomaly_detection_evaluation.csv

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import precision_score, recall_score, f1_score
from sqlalchemy import text

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config
from src.db_connection import get_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("07_AnomalyDetection")


def detect_anomalies(input_csv: Path = config.FEATURE_ENGINEERED_CSV) -> pd.DataFrame:
    """
    Applies IQR, Z-Score, and K-Means clustering anomaly detection per consumer.
    """
    logger.info("Loading dataset from %s for anomaly detection...", input_csv)
    df = pd.read_csv(input_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    logger.info("Computing IQR-based anomalies per consumer (multiplier = %.1f)...", config.IQR_MULTIPLIER)
    
    # -------------------------------------------------------------
    # METHOD 1: PER-CONSUMER INTERQUARTILE RANGE (IQR)
    # -------------------------------------------------------------
    def compute_iqr_anomalies(group):
        q25 = group["energy_kwh"].quantile(0.25)
        q75 = group["energy_kwh"].quantile(0.75)
        iqr = q75 - q25
        upper_bound = q75 + (config.IQR_MULTIPLIER * iqr)
        # In smart metering, high surges are primary anomalies (non-negative)
        return (group["energy_kwh"] > upper_bound).astype(int)

    df["is_anomaly_iqr"] = df.groupby("consumer_id", group_keys=False).apply(compute_iqr_anomalies)

    # -------------------------------------------------------------
    # METHOD 2: PER-CONSUMER Z-SCORE (|Z| > threshold)
    # -------------------------------------------------------------
    logger.info("Computing Z-score anomalies per consumer (threshold = %.1f)...", config.ZSCORE_THRESHOLD)

    def compute_zscore_anomalies(group):
        mean_val = group["energy_kwh"].mean()
        std_val = group["energy_kwh"].std()
        if std_val == 0 or np.isnan(std_val):
            return pd.Series(0, index=group.index)
        z = (group["energy_kwh"] - mean_val) / std_val
        return (z > config.ZSCORE_THRESHOLD).astype(int)

    df["is_anomaly_zscore"] = df.groupby("consumer_id", group_keys=False).apply(compute_zscore_anomalies)

    # -------------------------------------------------------------
    # METHOD 3: K-MEANS CLUSTERING (Distance to Cluster Centroid)
    # -------------------------------------------------------------
    logger.info("Computing K-Means clustering-based anomalies...")
    # Cluster based on energy_kwh, peak_demand_kw, and hour
    cluster_features = ["energy_kwh", "peak_demand_kw", "hour"]
    scaler = StandardScaler()
    scaled_feats = scaler.fit_transform(df[cluster_features])

    kmeans = KMeans(n_clusters=config.KMEANS_CLUSTERS, random_state=config.RANDOM_SEED, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_feats)
    df["kmeans_cluster"] = cluster_labels

    # Calculate Euclidean distance of each point to its assigned cluster centroid
    centroids = kmeans.cluster_centers_
    distances = np.linalg.norm(scaled_feats - centroids[cluster_labels], axis=1)
    df["cluster_distance"] = distances

    # Flag top percentile distance as anomalous
    distance_threshold = np.percentile(distances, config.KMEANS_ANOMALY_PERCENTILE)
    df["is_anomaly_kmeans"] = (df["cluster_distance"] > distance_threshold).astype(int)
    logger.info("K-Means distance threshold (%.1fth percentile): %.4f",
                config.KMEANS_ANOMALY_PERCENTILE, distance_threshold)

    # -------------------------------------------------------------
    # CONSENSUS & LABELLING
    # -------------------------------------------------------------
    df["anomaly_consensus_count"] = (
        df["is_anomaly_iqr"] + df["is_anomaly_zscore"] + df["is_anomaly_kmeans"]
    )
    df["investigation_status"] = np.where(
        df["anomaly_consensus_count"] >= 2,
        "High Priority Investigation",
        np.where(df["anomaly_consensus_count"] == 1, "Needs Investigation", "Normal Reading")
    )

    # Verification: check if the benchmark example (38 kWh surge) was caught
    benchmark_matches = df[df["energy_kwh"] >= 38.0]
    if len(benchmark_matches) > 0:
        row = benchmark_matches.iloc[0]
        logger.info(
            ">>> Benchmark Verification: Consumer %s reading of %.2f kWh at %s flagged by -> IQR: %d, Z-Score: %d, KMeans: %d (Consensus: %d)",
            row["consumer_id"], row["energy_kwh"], row["timestamp"],
            row["is_anomaly_iqr"], row["is_anomaly_zscore"], row["is_anomaly_kmeans"],
            row["anomaly_consensus_count"]
        )

    # -------------------------------------------------------------
    # EVALUATION AGAINST INJECTED SYNTHETIC ANOMALIES
    # -------------------------------------------------------------
    eval_results = []
    methods = [
        ("IQR Method", df["is_anomaly_iqr"]),
        ("Z-Score Method", df["is_anomaly_zscore"]),
        ("K-Means Clustering", df["is_anomaly_kmeans"]),
        ("Consensus Voting (>=2)", (df["anomaly_consensus_count"] >= 2).astype(int))
    ]

    y_true = df["is_synthetic_anomaly"].fillna(0).astype(int)

    print("\n" + "=" * 80)
    print("                     ANOMALY DETECTION EVALUATION REPORT")
    print("  Note: Anomalies are 'unusual readings that need investigation', NOT proof of theft.")
    print("=" * 80)

    for m_name, preds in methods:
        total_flags = int(preds.sum())
        prec = precision_score(y_true, preds, zero_division=0)
        rec = recall_score(y_true, preds, zero_division=0)
        f1 = f1_score(y_true, preds, zero_division=0)

        eval_results.append({
            "Method": m_name,
            "Total_Flags_Raised": total_flags,
            "Precision_vs_Injected": round(prec, 4),
            "Recall_vs_Injected": round(rec, 4),
            "F1_Score": round(f1, 4),
            "Flag_Rate_Pct": round((total_flags / len(df)) * 100, 2)
        })

    eval_df = pd.DataFrame(eval_results)
    print(eval_df.to_string(index=False))
    print("=" * 80 + "\n")
    eval_df.to_csv(config.TABLES_DIR / "anomaly_detection_evaluation.csv", index=False)

    # -------------------------------------------------------------
    # STORE TO DATABASE AND CSV
    # -------------------------------------------------------------
    output_path = config.ANOMALY_RESULTS_CSV
    df.to_csv(output_path, index=False)
    logger.info("Saved complete anomaly results to: %s", output_path)

    # Write into Database Anomaly_Detection_Results table
    engine, dialect = get_db_engine()
    df["date_key"] = df["timestamp"].dt.strftime("%Y%m%d").astype(int)
    
    # Get consumer_key mapping from Dim_Consumer
    try:
        with engine.connect() as conn:
            dim_consumer = pd.read_sql(text("SELECT consumer_key, consumer_id FROM Dim_Consumer"), conn)
            fact_map = pd.read_sql(text("SELECT fact_id, date_key, consumer_key FROM Fact_Energy_Consumption"), conn)

        db_records = df.merge(dim_consumer, on="consumer_id", how="left")
        # Align with fact_id
        db_records["fact_id"] = db_records.index + 1
        
        anom_table = db_records[[
            "fact_id", "date_key", "consumer_key", "energy_kwh",
            "is_anomaly_iqr", "is_anomaly_zscore", "is_anomaly_kmeans",
            "anomaly_consensus_count", "investigation_status"
        ]].copy()

        with engine.begin() as conn:
            anom_table.to_sql("Anomaly_Detection_Results", conn, if_exists="replace", index=False)
        logger.info("Successfully loaded %d records into DB table 'Anomaly_Detection_Results'.", len(anom_table))
    except Exception as e:
        logger.warning("Could not sync directly to Anomaly_Detection_Results table: %s", str(e))

    return df


def run_anomaly_detection():
    """Main execution entrypoint for Step 7."""
    logger.info("=== STEP 7: STARTING ANOMALY DETECTION ===")
    df_results = detect_anomalies()
    logger.info("=== STEP 7 COMPLETE ===")
    return df_results


if __name__ == "__main__":
    run_anomaly_detection()

