"""
Pipeline Orchestration Script.

Purpose:
  Executes the entire Data Mining & Data Warehousing pipeline (Steps 1 through 9)
  sequentially with comprehensive logging, execution timing, and error handling.
  Ensures idempotent, reproducible end-to-end execution.

Usage:
  python run_pipeline.py

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import time
import logging
import importlib
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("PipelineOrchestrator")


def run_step_module(module_name: str, func_name: str):
    """Dynamically loads and invokes functions from numbered modules."""
    mod = importlib.import_module(f"src.{module_name}")
    func = getattr(mod, func_name)
    return func()


def main():
    start_total = time.time()
    logger.info("==================================================================")
    logger.info("  STARTING SMART ENERGY ANALYTICS & ANOMALY DETECTION PIPELINE  ")
    logger.info("  Course: Data Mining & Warehousing Lab (24B15CS313), JIIT Noida   ")
    logger.info("==================================================================")

    steps = [
        ("Step 1: Data Integration & Ingestion", "01_data_integration", "run_data_integration"),
        ("Step 2: Preprocessing & Data Quality Audit", "02_preprocessing", "run_preprocessing"),
        ("Step 3: Feature Engineering & Class Derivation", "03_feature_engineering", "run_feature_engineering"),
        ("Step 4: Star Schema Data Warehouse ETL", "04_warehouse_etl", "run_warehouse_etl"),
        ("Step 5: Online Analytical Processing (OLAP)", "05_olap_operations", "run_olap"),
        ("Step 6: Supervised Classification (DT, NB, kNN, SVM)", "06_classification", "run_classification"),
        ("Step 7: Unsupervised Anomaly Detection (IQR, Z-Score, KMeans)", "07_anomaly_detection", "run_anomaly_detection"),
        ("Step 8: Model Evaluation & Visualizations", "08_model_evaluation", "run_model_evaluation"),
        ("Step 9: WEKA ARFF Exporter", "09_export_arff", "run_arff_export")
    ]

    for step_desc, mod_name, func_name in steps:
        logger.info("\n>>> EXECUTING %s ...", step_desc.upper())
        t0 = time.time()
        try:
            run_step_module(mod_name, func_name)
            logger.info(">>> COMPLETED %s in %.2f seconds.", step_desc, time.time() - t0)
        except Exception as e:
            logger.error("!!! ERROR in %s: %s", step_desc, str(e), exc_info=True)
            sys.exit(1)

    total_time = time.time() - start_total
    logger.info("==================================================================")
    logger.info("  PIPELINE EXECUTED SUCCESSFULLY IN %.2f SECONDS!  ", total_time)
    logger.info("  All artifacts, databases, tables, figures, and ARFF files ready.")
    logger.info("  To launch the dashboard: streamlit run dashboard/app.py")
    logger.info("==================================================================")


if __name__ == "__main__":
    main()
