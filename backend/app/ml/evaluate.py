import numpy as np
from sklearn.base import clone
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

CV_METRICS = ["accuracy", "precision", "recall", "specificity", "f1", "roc_auc"]


def compute_metrics(y_true, y_pred, y_proba) -> dict:
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    specificity = (tn / (tn + fp)) if (tn + fp) > 0 else 0.0

    metrics = {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "specificity": round(float(specificity), 4),
        "f1": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, y_proba)), 4),
        "true_positives": int(tp),
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]],
    }

    fpr, tpr, _ = roc_curve(y_true, y_proba)
    step = max(1, len(fpr) // 100)
    metrics["roc_curve"] = {
        "fpr": [round(float(v), 4) for v in fpr[::step]],
        "tpr": [round(float(v), 4) for v in tpr[::step]],
    }
    return metrics


def cross_validate(estimator, X, y, cv) -> dict:
    scores = {metric: [] for metric in CV_METRICS}
    for train_idx, val_idx in cv.split(X, y):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

        pipe = clone(estimator)
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_val)
        y_proba = pipe.predict_proba(X_val)[:, 1]
        metrics = compute_metrics(y_val, y_pred, y_proba)
        for metric in CV_METRICS:
            scores[metric].append(metrics[metric])

    return {
        metric: {
            "mean": round(float(np.mean(values)), 4),
            "std": round(float(np.std(values)), 4),
        }
        for metric, values in scores.items()
    }


def format_metrics_table(metrics: dict[str, dict]) -> str:
    headers = ["Model", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]
    rows = []
    for name, m in metrics.items():
        rows.append([name, m["accuracy"], m["precision"], m["recall"],
                     m["f1"], m["roc_auc"]])
    widths = [max(len(str(r[i])) for r in rows + [headers]) for i in range(len(headers))]
    line = " | ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))
    sep = "-+-".join("-" * w for w in widths)
    out = [line, sep]
    for row in rows:
        out.append(" | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)))
    return "\n".join(out)
