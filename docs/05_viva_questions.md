# Viva Voce Examination Questions & Model Answers

**Subject:** Data Mining and Warehousing Lab (24B15CS313)  
**Institution:** Jaypee Institute of Information Technology (JIIT), Noida

This document compiles 32 high-yield viva questions with concise model answers to help you ace your lab defense.

---

### Q1: What is a Data Warehouse, and how does it differ from an operational database (OLTP)?
**Answer:** A Data Warehouse (OLAP) is a subject-oriented, integrated, time-variant, and non-volatile data repository designed for analytical query processing and decision-making. Operational databases (OLTP) are optimized for real-time transaction processing, high concurrency, and normalized updates (3NF), whereas warehouses are denormalized (star/snowflake) for analytical read performance.

### Q2: What is a Star Schema?
**Answer:** A dimensional data model where a single central Fact Table containing numerical measures is surrounded by multiple denormalized Dimension Tables containing contextual business attributes, connected via 1-hop primary-to-foreign key relationships.

### Q3: What is the grain of your Fact Table?
**Answer:** The grain of our `Fact_Energy_Consumption` table is **one individual consumer meter reading per one calendar hour**.

### Q4: What is the difference between a Star Schema and a Snowflake Schema?
**Answer:** In a star schema, dimension tables are completely denormalized (single table per dimension). In a snowflake schema, dimensions are normalized into hierarchies of sub-tables (e.g., city linking to state linking to country). Star schemas give superior query speed due to fewer joins.

### Q5: What is a Surrogate Key, and why do we use it instead of Natural Keys?
**Answer:** A surrogate key is an artificially generated integer identifier (e.g., `date_key`, `consumer_key`) managed entirely by the data warehouse. We use surrogate keys to decouple warehouse history from operational source system changes, protect against natural key modifications, handle slowly changing dimensions (SCD), and improve join performance using compact integer keys.

### Q6: What are the core OLAP operations?
**Answer:** 
1. **Roll-up:** Summarizing data by climbing up a hierarchy (e.g., Day -> Month -> Year).
2. **Drill-down:** Breaking down summaries into finer details (e.g., Year -> City -> Sector).
3. **Slice:** Selecting a 2D sub-plane by fixing one dimension (e.g., Consumer Type = 'Commercial').
4. **Dice:** Selecting a sub-cube by filtering multiple dimensions simultaneously.
5. **Pivot:** Rotating axes for multi-perspective tabular viewing.

### Q7: What is the difference between Additive, Semi-Additive, and Non-Additive facts?
**Answer:**
- **Additive:** Can be summed across all dimensions (e.g., `energy_kwh`, `carbon_emissions_kg`).
- **Semi-Additive:** Can be summed across some dimensions but not time (e.g., `peak_demand_kw` or bank account balance).
- **Non-Additive:** Cannot be meaningfully summed across any dimension (e.g., `voltage_v` or unit price; must use average, min, or max).

### Q8: What is ETL vs. ELT?
**Answer:** In ETL (Extract, Transform, Load), data is transformed on an external processing server (like Python/Pandas) before loading into the warehouse. In ELT (Extract, Load, Transform), raw data is loaded directly into the target database engine, and transformations are executed using the database's internal compute power.

### Q9: Why is the ETL pipeline in this project described as "idempotent"?
**Answer:** An idempotent pipeline can be executed multiple times without altering the result beyond the initial run. Our ETL script drops/replaces tables or verifies keys before insertion, preventing duplicate records or primary key collisions when rerun.

### Q10: What is Data Leakage in machine learning, and how did you prevent it?
**Answer:** Data leakage occurs when the model is trained with features that directly reveal the target label or wouldn't be available at inference time. Since our target `consumption_class` was derived from `energy_kwh`, we strictly excluded `energy_kwh` from model inputs. The models rely only on temporal indicators, weather, consumer capacity, and historical past lags (`lag_1`, `lag_2`, `rolling_mean`).

### Q11: Why did you use a chronological (time-aware) train/test split instead of a random shuffle split?
**Answer:** Smart meter energy data is a sequential time-series with strong temporal autocorrelation. A random shuffle split would cause temporal leakage (testing on past data while training on future data). Using an 80/20 chronological split trains on earlier dates (2023) and evaluates on later dates (2024), mimicking real-world deployment.

### Q12: Why must features be scaled for k-NN and SVM, but not for Decision Trees?
**Answer:** k-NN relies on Euclidean distance, and SVM relies on maximizing geometric margins. If features have vastly different numerical scales (e.g. connected load in 100s of kW vs. temperature in 10s of °C), large-scale features dominate the distance calculations. Decision trees, however, evaluate one feature at a time using orthogonal threshold splits, making them scale-invariant.

### Q13: What splitting criteria does a Decision Tree use?
**Answer:** Decision trees typically use **Gini Impurity** (in CART) or **Information Gain / Gain Ratio** (in ID3/C4.5). Our implementation in Scikit-Learn uses Gini impurity, which measures the probability of misclassifying a randomly chosen element.

### Q14: What is the core assumption of Naive Bayes?
**Answer:** It assumes that all input features are conditionally independent given the class label ($P(X \mid C) = \prod P(x_i \mid C)$). Although this assumption is violated in real-world correlated data, Naive Bayes often performs well as a quick baseline classifier.

### Q15: What is the difference between Macro F1-score and Weighted F1-score?
**Answer:** Macro F1 calculates the unweighted mean of F1 scores across all classes, treating all classes equally regardless of frequency. Weighted F1 weights each class score by its support (number of true instances), which can mask poor performance on minority classes.

### Q16: How did you define the target classes: Low, Normal, and High?
**Answer:** We computed the 33rd and 67th percentile quantile thresholds of historical consumption **per consumer type** on the training partition. Readings $\le 33\text{rd}$ percentile are 'Low', between 33rd and 67th are 'Normal', and $> 67\text{th}$ percentile are 'High'.

### Q17: Why did you calculate classification quantile thresholds per consumer type rather than globally?
**Answer:** Because an Industrial consumer using 50 kWh might be at their baseline 'Low' load, whereas a Residential household using 50 kWh is at an extreme peak 'High' load. Partitioning cutoffs by consumer category reflects sectoral operational realities.

### Q18: What is the Interquartile Range (IQR) rule for outlier detection?
**Answer:** $IQR = Q_3 - Q_1$, where $Q_1$ is the 25th percentile and $Q_3$ is the 75th percentile. Any reading exceeding $Q_3 + (1.5 \times IQR)$ is flagged as an upper outlier.

### Q19: What is the Z-score method for anomaly detection?
**Answer:** The Z-score measures how many standard deviations an observation $x$ lies from the mean $\mu$: $Z = (x - \mu) / \sigma$. An observation with $|Z| > 3.0$ is flagged as anomalous, corresponding to the outer 0.27% tails of a normal distribution.

### Q20: How does K-Means clustering identify anomalies?
**Answer:** After fitting $K$ cluster centroids on multivariate features (`energy_kwh`, `peak_demand_kw`, `hour`), we compute the Euclidean distance of each reading to its assigned cluster centroid. Data points falling beyond the 98th percentile of distances are flagged as cluster anomalies.

### Q21: Why must anomaly detection statistics be computed per consumer rather than across the entire dataset?
**Answer:** Individual consumers have vastly different consumption baselines. If computed globally, all industrial readings would be falsely flagged as anomalies, while major anomalies in residential meters (e.g. a jump from 2 kWh to 38 kWh) would be missed because 38 kWh is small compared to industrial loads.

### Q22: Why must anomalies be worded as "unusual readings that need investigation" rather than "electricity theft"?
**Answer:** Data mining models detect statistical deviations, not human intent or physical reality. An unusual spike could be caused by meter sensor faults, wiring issues, legitimate temporary equipment usage (e.g. welding machine, wedding lights), or grid surges. Labeling it "theft" is a legal claim unsupported by data alone.

### Q23: How did you evaluate the unsupervised anomaly detection models when real data lacks ground-truth anomaly labels?
**Answer:** We injected a known set of synthetic anomalies (1.5% of readings, including a benchmark 38 kWh spike for consumer CONS_001) into a benchmark dataset and evaluated precision, recall, and F1-score of each method against those known injected labels. We also evaluated consensus agreement across the three methods.

### Q24: What is consensus voting in anomaly detection?
**Answer:** Combining multiple independent detectors (IQR, Z-score, K-Means). If at least 2 out of 3 methods flag a reading, it is tagged as a "High Priority Investigation", reducing false positive alert fatigue for grid operators.

### Q25: What is an ARFF file in WEKA?
**Answer:** Attribute-Relation File Format (.arff) is an ASCII text file format developed for WEKA that describes a list of instances sharing a set of attributes, structured into an `@relation` header, `@attribute` definitions (numeric, nominal, string), and a `@data` section.

### Q26: Which WEKA algorithms correspond to Scikit-Learn's Decision Tree, Naive Bayes, k-NN, and SVM?
**Answer:**
- Decision Tree $\rightarrow$ `trees.J48` (C4.5 implementation)
- Naive Bayes $\rightarrow$ `bayes.NaiveBayes`
- k-NN $\rightarrow$ `lazy.IBk`
- SVM $\rightarrow$ `functions.SMO` (Sequential Minimal Optimization)

### Q27: How does GridSearchCV prevent overfitting?
**Answer:** GridSearchCV uses $k$-fold cross-validation across hyperparameter combinations on the training set only. Performance is averaged across folds, preventing the model from fitting to idiosyncrasies of a single train/validation split.

### Q28: What is a Confusion Matrix?
**Answer:** A cross-tabulation table where rows represent actual ground-truth classes and columns represent model predicted classes. The diagonal cells represent correct classifications (True Positives/True Negatives), while off-diagonal cells represent misclassifications (False Positives/False Negatives).

### Q29: What is Precision vs. Recall?
**Answer:**
- **Precision:** Of all instances the model predicted as positive, how many were actually positive? ($\frac{TP}{TP + FP}$)
- **Recall (Sensitivity):** Of all actual positive instances, how many did the model correctly identify? ($\frac{TP}{TP + FN}$)

### Q30: What is a Data Mart?
**Answer:** A subset of a data warehouse focused on a specific business line or department (e.g., Billing Data Mart, Outage Data Mart). Our star schema can serve as an enterprise-wide energy data mart.

### Q31: What is Slowly Changing Dimension (SCD)?
**Answer:** A dimension whose attributes change gradually over time (e.g., a consumer changing from Residential to Commercial tariff). Types include SCD Type 1 (overwrite old value), Type 2 (add new row with effective date range and surrogate key), and Type 3 (add previous-value column).

### Q32: How does the system handle database connectivity if MySQL is not installed on the evaluation machine?
**Answer:** `src/db_connection.py` uses SQLAlchemy to ping MySQL first. If MySQL is unreachable, it logs a clear notification and automatically switches to an embedded SQLite database (`smart_energy_dw.sqlite`), allowing zero-configuration evaluation on any machine.

