# Machine Learning Explained — HeartGuard AI

This document explains, in plain language, every machine-learning concept used
in this project. It is written so a college student can explain the whole
pipeline to an examiner — from dataset to deployed prediction.

---

## 1. What is the problem?

Heart disease is a binary classification problem: given a patient's clinical
measurements, we want to predict whether that patient belongs to the **heart
disease class** (`target = 1`) or not (`target = 0`).

This is a *supervised* learning problem because we have a dataset where every
row already has the correct answer (the `target` column). The models learn
patterns from these labelled examples.

## 2. What is the input?

Each patient is described by 13 **features** (also called *attributes* or
*variables*):

| Feature | Meaning | Type |
| --- | --- | --- |
| `age` | Age in years | numeric |
| `sex` | Sex (0 = female, 1 = male) | categorical |
| `cp` | Chest pain type (0–3) | categorical |
| `trestbps` | Resting blood pressure (mm Hg) | numeric |
| `chol` | Serum cholesterol (mg/dl) | numeric |
| `fbs` | Fasting blood sugar > 120 mg/dl (0/1) | categorical |
| `restecg` | Resting ECG result (0–2) | categorical |
| `thalach` | Maximum heart rate achieved (bpm) | numeric |
| `exang` | Exercise-induced angina (0/1) | categorical |
| `oldpeak` | ST depression induced by exercise | numeric |
| `slope` | Slope of peak-exercise ST segment (0–2) | categorical |
| `ca` | Major vessels coloured by fluoroscopy (0–4) | categorical |
| `thal` | Thalassemia (0–3) | categorical |

> In the web form you never type these raw numbers — the form shows friendly
> labels ("Male", "Asymptomatic", "Yes/No") and the backend maps them to the
> encodings above. The backend mapping is the authoritative validation.

## 3. What is the output?

A binary prediction: **Positive** (heart disease) or **Negative** (no heart
disease), plus a **probability** for each model (e.g. "82% chance of the
positive class").

## 4. Why Logistic Regression?

Logistic Regression is one of the simplest classification algorithms. It
computes a weighted sum of the features, passes that sum through a **sigmoid
function**, and gets a probability between 0 and 1:

```
z = w0 + w1·age + w2·trestbps + ... + w13·thal
probability = 1 / (1 + e^-z)
```

- If the probability ≥ 0.5 the model predicts class 1 (Positive).
- The weights are learned from the training data by minimising the
  *log-loss*.
- It is a *linear* model: it draws a straight decision boundary in
  feature space.
- Its **coefficients** tell us the direction and strength of each feature's
  influence — easy to interpret.

## 5. Why a Decision Tree?

A Decision Tree makes predictions with a series of if-else questions:

```
age > 55?
 ├── yes → thalach < 140?
 │        ├── yes → Positive
 │        └── no  → ...
 └── no  → ...
```

- At each node the algorithm picks the feature and threshold that best
  separates the classes (using *Gini impurity* or *entropy*).
- Trees are **transparent** — you can read every rule — and handle mixed
  numeric/categorical features naturally.
- They are prone to **overfitting** if allowed to grow unboundedly, so we
  limit `max_depth`, `min_samples_split` and `min_samples_leaf`.

## 6. Why a Random Forest?

A Random Forest is an **ensemble** of many decision trees. It trains, say,
100 trees, each on a random subset of the rows and features (this is called
*bootstrap aggregating* or *bagging* plus *feature randomness*). Each tree
votes, and the majority wins.

- Combining many slightly different trees **reduces variance** and
  generalises better than a single tree.
- It is more robust but less transparent than one tree; we still get
  **feature importances** by averaging the impurity decreases across trees.

## 7. What is training?

**Training** means showing the model labelled examples and adjusting its
internal parameters so its predictions match the labels. In this project we
give each model 241 rows (80% of the dataset) and let it learn.

We split the data **before** any scaling or encoding — the preprocessing
pipeline is *fitted only on the training split*. Fitting it on the whole
dataset first would be **data leakage**: the test set would no longer be
unseen.

## 8. What is testing?

The remaining 61 rows (20%) are **held out** during training. After training
we ask each model to predict these unseen rows and compare its predictions to
the true labels. This estimates how the model will behave on new patients it
has never seen. Stratification keeps the class balance identical in train and
test.

## 9. What is overfitting?

Overfitting is when a model memorises the training data (including its noise)
instead of learning general patterns. Symptoms: excellent training accuracy
but poor test accuracy. We limit overfitting here with `max_depth`,
`min_samples_split`, and by using a Random Forest ensemble.

## 10. What is accuracy?

Accuracy = (correct predictions) / (all predictions). On our test set,
Logistic Regression achieves ~82%.

## 11. What is precision?

Of the patients the model flagged as "Positive", how many actually were
Positive?

```
precision = TP / (TP + FP)
```

Low precision → many false alarms.

## 12. What is recall?

Of the patients who actually had heart disease, how many did the model catch?

```
recall = TP / (TP + FN)
```

Low recall → the model misses real cases (dangerous in medicine).

## 13. What is the F1 score?

The harmonic mean of precision and recall — one number that balances both:

```
F1 = 2 · (precision · recall) / (precision + recall)
```

## 14. What is ROC-AUC?

The ROC curve plots the *true positive rate* against the *false positive
rate* for every possible decision threshold. The **AUC** is the area under
that curve:

- AUC = 1.0 → perfect separation.
- AUC = 0.5 → no better than random guessing.

AUC is threshold-independent, which makes it a good summary of a model's
ranking ability. That is why the comparison dashboard defaults to ROC-AUC
when picking the "best" model.

## 15. Why should healthcare ML not rely on accuracy alone?

Accuracy hides what kind of mistakes a model makes. If 90% of patients were
healthy, a model that always says "Negative" would be 90% accurate but
useless — it would miss every sick patient. In health screening, **recall**
matters a lot: failing to detect a real condition (a false negative) is
usually more harmful than a false alarm. That is why this project reports
precision, recall, F1 and ROC-AUC alongside accuracy, and uses
`class_weight="balanced"` to handle the (mild) class imbalance in the data.

## 16. Model probability vs model accuracy

- **Probability** (per prediction): what the model thinks about *one specific
  patient* — e.g. "82% chance of heart disease".
- **Accuracy** (per test set): how often the model was correct *overall* on
  the held-out data.

Neither is a guarantee. Both are statistical statements, not medical
diagnoses.

## 17. The full pipeline in one diagram

```
heart.csv (303 rows, 13 features, target)
   │
   ├─ drop duplicates → 302 rows
   ├─ train/test split (80/20, stratified, random_state=42)
   │
   ├─ ColumnTransformer fitted on TRAIN only
   │     numeric   → StandardScaler
   │     categorical → OneHotEncoder
   │
   ├─ Logistic Regression ─┐
   ├─ Decision Tree       ─┤  each wrapped in a Pipeline
   └─ Random Forest       ─┘
   │
   ├─ evaluate on the held-out TEST set
   │     accuracy, precision, recall, F1, ROC-AUC, confusion matrix
   ├─ save metrics.json
   └─ serialize + AES-256-GCM encrypt → encrypted_models/*.enc
```

At prediction time the API decrypts these models in memory, transforms the
new patient's features with the *same* fitted pipeline, and runs all three
models.
