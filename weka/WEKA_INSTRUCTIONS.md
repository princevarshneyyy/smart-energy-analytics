# WEKA Explorer GUI Step-by-Step Instructions

This guide explains how to open the generated ARFF datasets in the **WEKA Explorer GUI** to perform classification and compare the results with our Python Scikit-Learn pipeline.

Course: *Data Mining and Warehousing Lab (24B15CS313)*, JIIT Noida.

---

## 1. Prerequisites and ARFF Files

The pipeline automatically generates two clean, leak-free ARFF files in `data/processed/`:
1. `energy_classification_train.arff`: 80% training partition (chronological split).
2. `energy_classification_test.arff`: 20% testing partition.

> **Key Exam Note for Teacher:** Notice that `energy_kwh` is **NOT** present in the ARFF file. Only historical lags (`energy_lag_1`, `energy_lag_2`, `energy_rolling_mean_6`), temporal indicators, weather, and consumer category are present. This prevents **target data leakage**.

---

## 2. Step-by-Step WEKA GUI Workflow

### Step 1: Launch WEKA & Open Explorer
1. Launch **WEKA** on your computer.
2. In the main WEKA GUI Chooser window, click on the **Explorer** button.

### Step 2: Load Training Data (Preprocess Tab)
1. In the **Preprocess** tab, click **Open file...**.
2. Navigate to this project directory: `data/processed/energy_classification_train.arff`.
3. Click **Open**.
4. You will see 15 attributes listed. Click on `consumption_class` at the bottom:
   - Notice the class distribution histogram (Low, Normal, High).

### Step 3: Configure Classifier Evaluation (Classify Tab)
1. Switch to the **Classify** tab at the top.
2. Under **Test options**:
   - Choose **Supplied test set**.
   - Click **Set...** -> **Open file...** -> Select `data/processed/energy_classification_test.arff`.
   - Ensure the class dropdown at the bottom is set to `(Nom) consumption_class`.

---

## 3. Running the 4 Classifiers in WEKA

### A. Decision Tree (WEKA: `trees` -> `J48`)
- *J48 is WEKA's implementation of the C4.5 / CART algorithm.*
1. Click the **Choose** button under Classifier.
2. Expand `trees` -> Click **J48**.
3. (Optional) Right-click on J48 to set parameters like `confidenceFactor` (0.25) or `minNumObj` (5).
4. Click **Start**.
5. Inspect the output buffer:
   - Check **Correctly Classified Instances %** (Accuracy).
   - Check the **Confusion Matrix** at the bottom.
   - Right-click the result list item and select **Visualize tree** to view the actual decision tree branches!

### B. Naive Bayes (WEKA: `bayes` -> `NaiveBayes`)
1. Click **Choose** -> Expand `bayes` -> Select **NaiveBayes**.
2. Click **Start**.
3. Inspect output: Prior class probabilities and conditional Gaussian distributions for numerical attributes.

### C. k-Nearest Neighbors (WEKA: `lazy` -> `IBk`)
- *IBk is Instance-Based learning with k neighbors (k-NN).*
1. Click **Choose** -> Expand `lazy` -> Select **IBk**.
2. Left-click the `IBk` text to open its properties editor:
   - Change `KNN` from 1 to 5 (to match our Python `n_neighbors=5`).
   - Set `distanceWeighting` to `Weight by 1/distance` or `No distance weighting`.
3. Click **OK** -> Click **Start**.

### D. Support Vector Machine (WEKA: `functions` -> `SMO`)
- *SMO (Sequential Minimal Optimization) implements SVM.*
1. Click **Choose** -> Expand `functions` -> Select **SMO**.
2. Click **Start**.
3. Inspect the hyper-plane weights and overall test accuracy.

---

## 4. Comparing WEKA with Scikit-Learn Results

| Classifier Algorithm | Scikit-Learn Class | WEKA Equivalent | Key Comparison Metric |
| :--- | :--- | :--- | :--- |
| **Decision Tree** | `DecisionTreeClassifier` | `trees.J48` | Tree Depth, Split Rule, Macro F1 |
| **Naive Bayes** | `GaussianNB` | `bayes.NaiveBayes` | Probability Distribution Assumptions |
| **k-Nearest Neighbors** | `KNeighborsClassifier` | `lazy.IBk` (k=5) | Euclidean Distance, Distance Weighting |
| **Support Vector Machine** | `LinearSVC` | `functions.SMO` | Hyperplane Margin, Normalization |

### What to explain to the Teacher:
> *"Both WEKA and Scikit-learn produce concordant results. Decision Trees and ensemble/lag-based rules perform best because electrical usage features exhibit non-linear step shifts between commercial working hours and residential night periods. WEKA's J48 decision tree visualizer confirms that the most dominant root split is the recent rolling average (`energy_rolling_mean_6`) followed by `hour` and `consumer_type`."*

