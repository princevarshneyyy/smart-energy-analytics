# Data Mining & Warehousing Algorithms Explained

This reference explains the mathematical foundations, operational mechanics, and formulas for all mining and warehousing techniques used in this project.

---

## 1. Dimensional Warehousing & OLAP Mechanics

### Star Schema vs Snowflake Schema
- **Star Schema:** Dimension tables are completely denormalized. Each dimension connects directly to the central Fact Table via a foreign key (1-hop join). This minimizes SQL join overhead and simplifies OLAP slicing.
- **Snowflake Schema:** Dimensions are normalized into sub-tables (e.g. `Dim_City` connects to `Dim_State` which connects to `Dim_Country`). While it reduces redundancy, it degrades OLAP performance due to complex multi-table joins.

### OLAP Operations
1. **Roll-Up:** Performs summarization by climbing up a concept hierarchy or reducing dimensions (e.g., aggregating hourly meter readings into daily or monthly totals: $\sum \text{kWh}$).
2. **Drill-Down:** The inverse of Roll-Up. Steps down from higher-level summaries into granular details (e.g., breaking down 2023 total power into individual cities and consumer types).
3. **Slice:** Performs a selection on one dimension of a data cube, yielding a 2D sub-plane (e.g., $\text{Consumer Type} = \text{'Commercial'}$).
4. **Dice:** Defines a sub-cube by applying selection criteria simultaneously across two or more dimensions (e.g., $\text{City} \in \{\text{Noida, Delhi}\} \land \text{Season} = \text{'Summer'} \land \text{IsPeak} = 1$).
5. **Pivot (Rotate):** Rotates the data axes in space to provide an alternative presentation of data (e.g., City on rows, Consumer Sector on columns).

---

## 2. Supervised Classification Algorithms

### A. Decision Tree (CART / C4.5)
- **Concept:** Recursively partitions the feature space into orthogonal rectangles by selecting splits that maximize impurity reduction.
- **Splitting Criterion (Gini Impurity):**
  $$Gini(D) = 1 - \sum_{i=1}^{k} p_i^2$$
  where $p_i$ is the probability of class $i$ in partition $D$.
- **Why it fits:** Decision trees handle non-linear time boundaries (e.g., day vs night consumption jumps) and require no feature scaling.

### B. Naive Bayes (Gaussian NB)
- **Concept:** Applies Bayes' theorem with the strong ("naive") assumption of conditional feature independence given the class label $C_k$:
  $$P(C_k \mid X) = \frac{P(C_k) \prod_{j=1}^{d} P(x_j \mid C_k)}{P(X)}$$
- Continuous variables are modeled using Gaussian normal probability distributions:
  $$P(x_j \mid C_k) = \frac{1}{\sqrt{2\pi\sigma_k^2}} \exp\left(-\frac{(x_j - \mu_k)^2}{2\sigma_k^2}\right)$$
- **Why it fits:** Extremely fast training; provides a probabilistic baseline.

### C. k-Nearest Neighbors (k-NN)
- **Concept:** Non-parametric instance-based classifier. Assigns an unlabeled query instance $x$ to the majority class among its $k$ closest neighbors in Euclidean space:
  $$d(x, x') = \sqrt{\sum_{j=1}^{d} (x_j - x_j')^2}$$
- **Crucial Requirement:** Features MUST be standardized (using `StandardScaler` where $z = \frac{x - \mu}{\sigma}$). Unscaled features with large ranges (e.g., connected load 200 kW) would otherwise completely dominate features with small ranges (e.g., temperature or lag values).

### D. Support Vector Machine (Linear SVM)
- **Concept:** Constructs a hyperplane $\mathbf{w}^T \mathbf{x} + b = 0$ that maximizes the geometric margin between classes while minimizing classification penalties:
  $$\min_{\mathbf{w}, b, \xi} \frac{1}{2}\|\mathbf{w}\|^2 + C \sum_{i=1}^{n} \xi_i \quad \text{subject to } y_i(\mathbf{w}^T \mathbf{x}_i + b) \ge 1 - \xi_i$$
- **Crucial Requirement:** Like k-NN, SVM is highly sensitive to feature scaling; standard scaling is applied inside the pipeline.

---

## 3. The Zero-Data-Leakage Architectural Rule

### What is Data Leakage?
Data leakage occurs when information from outside the training partition (or from the target itself) is inadvertently shared with the model during training, producing unrealistically inflated validation performance that fails in production.

### How We Prevented It:
In our dataset, the target variable `consumption_class` (`Low`, `Normal`, `High`) is derived from the active energy measure `energy_kwh`. If `energy_kwh` or contemporaneous derivatives (like `peak_demand_kw` from the same hour) were passed as input features, the model would achieve trivial 100% accuracy simply by memorizing the cutoff rules!

**Our Solution:**
- `energy_kwh` and current-hour demand are **STRICTLY EXCLUDED** from the model feature matrix $X$.
- The model is supplied **ONLY** with:
  1. Temporal indicators (`hour`, `day_of_week`, `month`, `is_peak_hour`).
  2. Weather parameters (`temperature_c`, `humidity_pct`, `weather_condition`).
  3. Consumer master attributes (`consumer_type`, `connected_load_kw`).
  4. Historical past lags (`energy_lag_1`, `energy_lag_2`, `energy_rolling_mean_6`).

---

## 4. Unsupervised Anomaly Detection Formulations

### A. Interquartile Range (IQR) Method
- Computes the first quartile $Q_1$ (25th percentile) and third quartile $Q_3$ (75th percentile) of consumption.
- $$IQR = Q_3 - Q_1$$
- Upper bound: $\text{Threshold} = Q_3 + (1.5 \times IQR)$
- An instance is flagged as unusual if $\text{energy\_kwh} > \text{Threshold}$.

### B. Z-Score (Standard Score) Method
- Measures how many standard deviations an observation deviates from the consumer mean:
  $$Z = \frac{x - \mu}{\sigma}$$
- Flagged as unusual reading if $|Z| > 3.0$ (corresponding to readings beyond 99.73% of normal distribution).

### C. K-Means Centroid Distance Clustering
- Partitions data into $K$ spherical clusters minimizing within-cluster sum of squares:
  $$J = \sum_{k=1}^{K} \sum_{x \in S_k} \|x - \mu_k\|^2$$
- For each data point $x$, compute Euclidean distance to its assigned cluster centroid $\mu_k$:
  $$\text{dist}(x) = \|x - \mu_k\|$$
- Points exceeding the 98th percentile of centroid distances are flagged as potential cluster anomalies.

### Why Statistics Must Be Computed Per Consumer:
In a multi-consumer grid, an Industrial consumer normally consumes $80 \text{ to } 200 \text{ kWh/hour}$, while a Residential consumer consumes $1 \text{ to } 4 \text{ kWh/hour}$. If IQR or Z-score were computed globally across the entire table:
1. Every industrial reading would be falsely flagged as an anomaly.
2. A residential customer experiencing a massive 30-fold surge (e.g. from 1.5 kWh to 38 kWh) would remain undetected because 38 kWh is well within global ranges!
Computing statistics per consumer preserves each meter's individual baseline.

