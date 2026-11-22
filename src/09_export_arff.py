"""
Step 9: WEKA ARFF Exporter Module.

Purpose:
  1. Exports the clean, feature-engineered energy consumption dataset into
     standard Attribute-Relation File Format (.arff) required by WEKA (Waikato
     Environment for Knowledge Analysis).
  2. Ensures strict WEKA data format compliance:
     - Generates valid @relation, @attribute headers.
     - Formats nominal attributes properly: @attribute consumer_type {Residential,Commercial,Industrial}
     - Formats target class: @attribute consumption_class {Low,Normal,High}
     - Properly encodes missing or special values.
  3. Exports both a training split (energy_classification_train.arff)
     and testing split (energy_classification_test.arff) so students can replicate
     the exact experiment inside the WEKA Explorer GUI.

Inputs:
  - data/processed/featured_energy_data.csv
Outputs:
  - data/processed/energy_classification_train.arff
  - data/processed/energy_classification_test.arff

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("09_ExportARFF")


def df_to_arff(df: pd.DataFrame, relation_name: str, output_path: Path):
    """
    Writes a pandas DataFrame into valid WEKA ARFF format.
    """
    logger.info("Writing WEKA ARFF to: %s", output_path)

    # Feature subset matching scikit-learn experiment (Strictly excluding energy_kwh to prevent data leakage)
    arff_cols = [
        "hour", "day_of_week", "month", "quarter", "is_weekend", "is_peak_hour",
        "temperature_c", "humidity_pct", "weather_condition",
        "consumer_type", "connected_load_kw",
        "energy_lag_1", "energy_lag_2", "energy_rolling_mean_6",
        "consumption_class"
    ]

    export_df = df[arff_cols].copy()

    with open(output_path, "w", encoding="utf-8") as f:
        # Header
        f.write(f"% WEKA ARFF Dataset: Smart Energy Consumption Analytics\n")
        f.write(f"% Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida\n")
        f.write(f"% Notice: energy_kwh is isolated to ensure Zero Data Leakage.\n\n")
        f.write(f"@relation {relation_name}\n\n")

        # Attribute definitions
        f.write("@attribute hour numeric\n")
        f.write("@attribute day_of_week numeric\n")
        f.write("@attribute month numeric\n")
        f.write("@attribute quarter numeric\n")
        f.write("@attribute is_weekend {0,1}\n")
        f.write("@attribute is_peak_hour {0,1}\n")
        f.write("@attribute temperature_c numeric\n")
        f.write("@attribute humidity_pct numeric\n")
        
        weather_vals = ",".join(sorted(export_df["weather_condition"].unique()))
        f.write(f"@attribute weather_condition {{{weather_vals}}}\n")
        
        ctype_vals = ",".join(sorted(export_df["consumer_type"].unique()))
        f.write(f"@attribute consumer_type {{{ctype_vals}}}\n")
        
        f.write("@attribute connected_load_kw numeric\n")
        f.write("@attribute energy_lag_1 numeric\n")
        f.write("@attribute energy_lag_2 numeric\n")
        f.write("@attribute energy_rolling_mean_6 numeric\n")
        
        # Target nominal class
        f.write("@attribute consumption_class {Low,Normal,High}\n\n")

        # Data Section
        f.write("@data\n")
        for _, row in export_df.iterrows():
            vals = [
                str(int(row["hour"])),
                str(int(row["day_of_week"])),
                str(int(row["month"])),
                str(int(row["quarter"])),
                str(int(row["is_weekend"])),
                str(int(row["is_peak_hour"])),
                f"{float(row['temperature_c']):.1f}",
                f"{float(row['humidity_pct']):.1f}",
                str(row["weather_condition"]),
                str(row["consumer_type"]),
                f"{float(row['connected_load_kw']):.1f}",
                f"{float(row['energy_lag_1']):.4f}",
                f"{float(row['energy_lag_2']):.4f}",
                f"{float(row['energy_rolling_mean_6']):.4f}",
                str(row["consumption_class"])
            ]
            f.write(",".join(vals) + "\n")

    logger.info("Successfully exported ARFF with %d instances to %s", len(export_df), output_path)


def export_weka_files(input_csv: Path = config.FEATURE_ENGINEERED_CSV):
    """
    Creates both train and test ARFF files matching chronological split.
    """
    logger.info("Reading featured data from %s...", input_csv)
    df = pd.read_csv(input_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # 80/20 Chronological Split
    split_idx = int(len(df) * 0.80)
    train_df = df.iloc[:split_idx]
    test_df = df.iloc[split_idx:]

    df_to_arff(train_df, "energy_consumption_train", config.ARFF_TRAIN_FILE)
    df_to_arff(test_df, "energy_consumption_test", config.ARFF_TEST_FILE)


def run_arff_export():
    """Main execution entrypoint for Step 9."""
    logger.info("=== STEP 9: STARTING WEKA ARFF EXPORT ===")
    export_weka_files()
    logger.info("=== STEP 9 COMPLETE ===")


if __name__ == "__main__":
    run_arff_export()

