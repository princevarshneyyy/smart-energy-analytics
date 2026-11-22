# 5-Minute Lab Demo Script & Walkthrough

Use this exact chronological script to demonstrate the project to your lab instructor, external examiner, or faculty evaluator within 5 minutes.

---

### Step 0: Terminal Setup & Execution (Minute 0:00 - 0:45)
1. Open your terminal in the project root:
   ```bash
   cd smart-energy-analytics
   python run_pipeline.py
   ```
2. **What to say while it runs:**
   > *"Good morning/afternoon, Sir/Ma'am. I am running `run_pipeline.py`, which orchestrates all 9 steps of our Data Mining and Warehousing system. As you can see from the logs, it integrates raw smart meter data, executes an automated data quality audit that removes duplicate meter transmissions, performs feature engineering with zero data leakage, populates our Star Schema data warehouse, runs pure-SQL and Pandas OLAP queries, trains four supervised classifiers, detects anomalies using three statistical and clustering techniques, and exports WEKA ARFF datasets. The entire pipeline runs idempotently in under 30 seconds."*

---

### Step 1: Data Warehouse & OLAP Operations (Minute 0:45 - 1:45)
1. Open `sql/02_create_star_schema.sql` and `sql/03_olap_queries.sql` in VS Code / Editor.
2. **What to say:**
   > *"Here is our Star Schema design. At the center is `Fact_Energy_Consumption` with a grain of one consumer reading per one hour, containing measures like active power in kWh, peak demand, and carbon emissions. Surrounding it are `Dim_Date`, `Dim_Time`, `Dim_Consumer`, `Dim_Location`, and `Dim_Weather`, using integer surrogate keys for fast analytical joins.*
   > 
   > *In `sql/03_olap_queries.sql`, we have implemented five OLAP operations: Roll-up across time hierarchies, Drill-down into specific cities, Slice fixing Commercial consumers, Dice across multiple dimensions simultaneously, and Pivot/Cube cross-tabulations. Notice that we also maintain a separate `Anomaly_Detection_Results` table so analytical model iterations do not tamper with historical fact data."*

---

### Step 2: Supervised Classification & Zero Data Leakage (Minute 1:45 - 2:45)
1. Launch the interactive dashboard:
   ```bash
   streamlit run dashboard/app.py
   ```
2. Navigate to **Page 3: Classification**.
3. **What to say:**
   > *"On the Classification page, we evaluate four classifiers: Decision Tree, Naive Bayes, k-Nearest Neighbors, and Linear SVM. The target is consumption tier: Low, Normal, or High.*
   > 
   > *A key strength of our design is strict avoidance of data leakage: `energy_kwh` is completely excluded from the training feature matrix. Instead, the models predict consumption using temporal variables, ambient weather, consumer capacity, and historical lag features. Decision Tree achieved our top macro F1-score because tree splits effectively capture non-linear step shifts during peak diurnal hours."*

---

### Step 3: Anomaly Detection & Benchmark Scenario (Minute 2:45 - 3:45)
1. Navigate to **Page 4: Anomaly Alerts**.
2. Select **Consumer CONS_001** and show the time-series graph with red markers.
3. **What to say:**
   > *"Here is our Anomaly Detection Console. We implement three distinct unsupervised techniques: the IQR rule per consumer, the Z-Score rule with threshold 3.0, and K-Means centroid distance clustering.*
   > 
   > *Computing statistics per consumer is critical: an industrial baseline is 100 kWh, whereas a residential baseline is 2 kWh. Notice our benchmark test case on screen: Consumer CONS_001, whose normal baseline is 8 to 15 kWh, suddenly recorded 38 kWh. Our consensus detector flagged this reading immediately.*
   > 
   > *Per engineering ethics standards, we strictly report these flags as 'unusual readings that need investigation', rather than unverified accusations of electricity theft or equipment tampering."*

---

### Step 4: OLAP Explorer & Interactive Dashboard (Minute 3:45 - 4:30)
1. Switch to **Page 2: OLAP Explorer**.
2. Toggle between **Roll-Up** (Year to Quarter to Month) and **Dice** (selecting Noida & Delhi, Residential, Summer).
3. **What to say:**
   > *"On the OLAP Explorer page, the evaluator or grid operator can dynamically slice, dice, roll up, and drill down through the data cube in real-time. Streamlit caches the star schema queries via `st.cache_data`, providing sub-second analytical pivots."*

---

### Step 5: WEKA Replication & Conclusion (Minute 4:30 - 5:00)
1. Open `weka/WEKA_INSTRUCTIONS.md` and show the generated ARFF files in `data/processed/`.
2. **What to say:**
   > *"Finally, step 9 generated `energy_classification_train.arff` and `test.arff`. Using WEKA Explorer GUI, we load these files into the Classify tab, run J48, NaiveBayes, IBk, and SMO, and verify that the confusion matrices and accuracy numbers closely mirror our Scikit-Learn findings.*
   > 
   > *Thank you, Sir/Ma'am! I am happy to answer any questions about our database schema, preprocessing, or mining algorithms."*

