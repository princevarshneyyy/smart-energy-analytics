"""
Page 3: Supervised Classification Results & Model Diagnostics.
"""

import streamlit as st
import pandas as pd
from PIL import Image
from pathlib import Path
from dashboard.utils import load_classification_metrics, render_datasource_badge
import config

# Render active data source badge in sidebar
render_datasource_badge()

st.title("🎯 Supervised Consumption Classification")
st.markdown("""
Classifies smart meter consumption into **Low, Normal, or High** tiers without target data leakage.
Models compared: **Decision Tree, Naive Bayes, k-Nearest Neighbors (kNN), and Support Vector Machine (Linear SVM)**.
""")

metrics_df = load_classification_metrics()

if not metrics_df.empty:
    st.subheader("📋 Model Benchmark Leaderboard")
    st.dataframe(metrics_df, use_container_width=True)

    # Show saved model comparison chart
    comp_img_path = config.FIGURES_DIR / "model_comparison.png"
    if comp_img_path.exists():
        st.subheader("📊 Comparative Evaluation Across Metrics")
        st.image(str(comp_img_path), use_column_width=True)

    # Show confusion matrices
    st.subheader("🔍 Confusion Matrices (Test Partition)")
    col1, col2 = st.columns(2)
    with col1:
        dt_cm = config.FIGURES_DIR / "confusion_matrix_decision_tree.png"
        if dt_cm.exists():
            st.image(str(dt_cm), caption="Decision Tree Confusion Matrix")

        knn_cm = config.FIGURES_DIR / "confusion_matrix_knn.png"
        if knn_cm.exists():
            st.image(str(knn_cm), caption="kNN Confusion Matrix")

    with col2:
        nb_cm = config.FIGURES_DIR / "confusion_matrix_naive_bayes.png"
        if nb_cm.exists():
            st.image(str(nb_cm), caption="Naive Bayes Confusion Matrix")

        svm_cm = config.FIGURES_DIR / "confusion_matrix_svm_linear.png"
        if svm_cm.exists():
            st.image(str(svm_cm), caption="Linear SVM Confusion Matrix")
else:
    st.warning("Classification metrics not generated yet. Please run `python run_pipeline.py` first.")

