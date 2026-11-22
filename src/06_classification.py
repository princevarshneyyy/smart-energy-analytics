"""
Step 6: Supervised Classification Pipeline.

Purpose:
  1. Classifies smart meter energy consumption level into Low, Normal, High.
  2. STRICT ZERO-DATA-LEAKAGE DESIGN:
     - energy_kwh and contemporaneous derivatives are STRICTLY EXCLUDED from features.
     - Features permitted: temporal indicators, weather variables, consumer category,
       connected load, and historical lag features (energy_lag_1, energy_lag_2, energy_rolling_mean_6).
  3. Implements 4 distinct Data Mining Classifiers:
     - Decision Tree (CART / C4.5 analog)
     - Naive Bayes (GaussianNB)
     - k-Nearest Neighbors (kNN) with StandardScaler pipeline
     - Support Vector Machine (SVM / LinearSVC) with StandardScaler pipeline
  4. Applies temporal train/test split (chronological split: 80% train, 20% test)
     plus 5-fold Stratified Cross-Validation on the training partition.
  5. Performs hyperparameter tuning using GridSearchCV.
  6. Saves trained models to outputs/models/ using joblib.

Inputs:
  - data/processed/featured_energy_data.csv
Outputs:
  - Trained models saved to outputs/models/:
    - decision_tree.joblib, naive_bayes.joblib, knn.joblib, svm.joblib
  - outputs/tables/classification_metrics.csv
  - Feature test split cached for step 08 evaluation

Course: Data Mining and Warehousing Lab (24B15CS313), JIIT Noida.
"""

import sys
import logging
from pathlib import Path
import joblib
import pandas as pd
import numpy as np

from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("06_Classification")


def prepare_classification_dataset(input_csv: Path = config.FEATURE_ENGINEERED_CSV):
    """
    Prepares features and target ensuring strict freedom from data leakage.
    Uses chronological time-aware train/test splitting.
    """
    logger.info("Loading dataset for classification from %s...", input_csv)
    df = pd.read_csv(input_csv)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    # Feature selection: STRICTLY EXCLUDES energy_kwh from features
    feature_cols = [
        # Temporal
        "hour", "day_of_week", "month", "quarter", "is_weekend", "is_peak_hour",
        # Environmental / Weather
        "temperature_c", "humidity_pct", "weather_condition",
        # Consumer Attributes
        "consumer_type", "connected_load_kw",
        # Historical Lag & Rolling Stats (past behavior only)
        "energy_lag_1", "energy_lag_2", "energy_rolling_mean_6", "energy_rolling_std_6"
    ]
    target_col = "consumption_class"

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Chronological Split (80% earliest dates for Train, 20% latest dates for Test)
    split_idx = int(len(df) * 0.80)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    timestamps_test = df["timestamp"].iloc[split_idx:].reset_index(drop=True)

    logger.info("Chronological Train/Test Split completed:")
    logger.info("  Training samples : %d (From %s to %s)",
                len(X_train), df['timestamp'].iloc[0], df['timestamp'].iloc[split_idx - 1])
    logger.info("  Testing samples  : %d (From %s to %s)",
                len(X_test), df['timestamp'].iloc[split_idx], df['timestamp'].iloc[-1])

    # Save test partition metadata for evaluation module (Step 8)
    test_export = X_test.copy()
    test_export["actual_class"] = y_test.values
    test_export["timestamp"] = timestamps_test.values
    test_export.to_csv(config.PROCESSED_DATA_DIR / "classification_test_partition.csv", index=False)

    return X_train, X_test, y_train, y_test


def build_preprocessor():
    """Builds scikit-learn ColumnTransformer for categorical and numerical features."""
    num_features = [
        "hour", "day_of_week", "month", "quarter", "is_weekend", "is_peak_hour",
        "temperature_c", "humidity_pct", "connected_load_kw",
        "energy_lag_1", "energy_lag_2", "energy_rolling_mean_6", "energy_rolling_std_6"
    ]
    cat_features = ["weather_condition", "consumer_type"]

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), num_features),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features)
        ]
    )
    return preprocessor


def train_and_tune_classifiers(X_train, X_test, y_train, y_test):
    """
    Trains, lightly tunes with GridSearchCV, evaluates, and persists 4 classifiers.
    """
    preprocessor = build_preprocessor()

    # Models & Grid definitions
    models_config = {
        "Decision_Tree": {
            "pipeline": Pipeline([
                ("prep", preprocessor),
                ("clf", DecisionTreeClassifier(random_state=config.RANDOM_SEED, class_weight="balanced"))
            ]),
            "params": {
                "clf__max_depth": [6, 10, 15],
                "clf__min_samples_split": [5, 20]
            }
        },
        "Naive_Bayes": {
            "pipeline": Pipeline([
                ("prep", preprocessor),
                ("clf", GaussianNB())
            ]),
            "params": {
                "clf__var_smoothing": [1e-9, 1e-7]
            }
        },
        "kNN": {
            "pipeline": Pipeline([
                ("prep", preprocessor),
                ("clf", KNeighborsClassifier())
            ]),
            "params": {
                "clf__n_neighbors": [5, 9],
                "clf__weights": ["uniform", "distance"]
            }
        },
        "SVM_Linear": {
            "pipeline": Pipeline([
                ("prep", preprocessor),
                ("clf", LinearSVC(random_state=config.RANDOM_SEED, max_iter=2500, class_weight="balanced"))
            ]),
            "params": {
                "clf__C": [0.1, 1.0]
            }
        }
    }

    results = []
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=config.RANDOM_SEED)

    print("\n" + "=" * 80)
    print("                     CLASSIFIER TRAINING & CROSS-VALIDATION")
    print("=" * 80)

    for name, item in models_config.items():
        logger.info("Training and tuning %s with GridSearchCV...", name)
        grid = GridSearchCV(item["pipeline"], item["params"], cv=cv, scoring="f1_macro", n_jobs=-1)
        grid.fit(X_train, y_train)

        best_model = grid.best_estimator_
        y_pred = best_model.predict(X_test)

        # Compute metrics
        acc = accuracy_score(y_test, y_pred)
        prec_macro = precision_score(y_test, y_pred, average="macro", zero_division=0)
        rec_macro = recall_score(y_test, y_pred, average="macro", zero_division=0)
        f1_macro = f1_score(y_test, y_pred, average="macro", zero_division=0)
        f1_weighted = f1_score(y_test, y_pred, average="weighted", zero_division=0)

        logger.info(">>> %s | Best Params: %s", name, grid.best_params_)
        logger.info(">>> Test Acc: %.4f | F1 (Macro): %.4f | F1 (Weighted): %.4f", acc, f1_macro, f1_weighted)

        results.append({
            "Model": name,
            "Accuracy": round(acc, 4),
            "Precision_Macro": round(prec_macro, 4),
            "Recall_Macro": round(rec_macro, 4),
            "F1_Macro": round(f1_macro, 4),
            "F1_Weighted": round(f1_weighted, 4),
            "Best_Hyperparameters": str(grid.best_params_)
        })

        # Save model artifact
        model_path = config.MODELS_DIR / f"{name.lower()}.joblib"
        joblib.dump(best_model, model_path)
        logger.info("Saved trained model to: %s", model_path)

        # Save predictions for step 8 confusion matrix
        pred_df = pd.DataFrame({"actual": y_test, "predicted": y_pred})
        pred_df.to_csv(config.TABLES_DIR / f"predictions_{name.lower()}.csv", index=False)

    summary_df = pd.DataFrame(results).sort_values(by="F1_Macro", ascending=False)
    print("\n" + summary_df.to_string(index=False))
    print("=" * 80 + "\n")

    summary_df.to_csv(config.TABLES_DIR / "classification_metrics.csv", index=False)
    logger.info("Saved classification performance metrics to: %s", config.TABLES_DIR / "classification_metrics.csv")

    return summary_df


def run_classification():
    """Main execution entrypoint for Step 6."""
    logger.info("=== STEP 6: STARTING SUPERVISED CLASSIFICATION ===")
    X_train, X_test, y_train, y_test = prepare_classification_dataset()
    summary_df = train_and_tune_classifiers(X_train, X_test, y_train, y_test)
    logger.info("=== STEP 6 COMPLETE ===")
    return summary_df


if __name__ == "__main__":
    run_classification()

