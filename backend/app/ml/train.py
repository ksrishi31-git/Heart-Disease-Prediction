import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.tree import DecisionTreeClassifier

from app.core.config import get_settings
from app.core.encryption import encrypt_bytes
from app.ml.evaluate import compute_metrics, cross_validate, format_metrics_table
from app.ml.preprocess import (
    ALL_COLUMNS,
    CATEGORICAL_COLUMNS,
    NUMERIC_COLUMNS,
    TARGET_COLUMN,
    build_preprocessing_pipeline,
    get_feature_names,
)

CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
TEST_SIZE = 0.2
RANDOM_STATE = 42
SEARCH_N_JOBS = -1

MODEL_CONFIGS = [
    {
        "key": "logistic_regression",
        "human_name": "Logistic Regression",
        "estimator_cls": LogisticRegression,
        "base_params": {"solver": "liblinear", "max_iter": 1000, "random_state": RANDOM_STATE},
        "param_grid": {
            "classifier__C": [0.01, 0.1, 1, 10, 100],
            "classifier__class_weight": [None, "balanced"],
        },
        "n_iter": 10,
    },
    {
        "key": "decision_tree",
        "human_name": "Decision Tree",
        "estimator_cls": DecisionTreeClassifier,
        "base_params": {"random_state": RANDOM_STATE},
        "param_grid": {
            "classifier__criterion": ["gini", "entropy"],
            "classifier__max_depth": [3, 4, 5, 6, 8, 10, None],
            "classifier__min_samples_split": [2, 5, 10],
            "classifier__min_samples_leaf": [1, 2, 4],
            "classifier__class_weight": [None, "balanced"],
        },
        "n_iter": 60,
    },
    {
        "key": "random_forest",
        "human_name": "Random Forest",
        "estimator_cls": RandomForestClassifier,
        "base_params": {"random_state": RANDOM_STATE, "n_jobs": -1},
        "param_grid": {
            "classifier__n_estimators": [100, 200, 300],
            "classifier__max_depth": [3, 5, 7, 10, None],
            "classifier__min_samples_split": [2, 5, 10],
            "classifier__min_samples_leaf": [1, 2, 4],
            "classifier__max_features": ["sqrt", "log2", None],
            "classifier__class_weight": [None, "balanced"],
        },
        "n_iter": 80,
    },
]

SELECT_K = 15


def load_dataset(path: Path) -> tuple[pd.DataFrame, int]:
    df = pd.read_csv(path, encoding="utf-8-sig")
    before = len(df)
    df = df.drop_duplicates()
    print(f"Dataset loaded: {before} rows ({before - len(df)} duplicate(s) removed)")
    return df, before


def audit_dataset(df: pd.DataFrame, raw_rows: int) -> dict:
    missing = {col: int(df[col].isna().sum()) for col in df.columns}
    missing = {k: v for k, v in missing.items() if v > 0}
    outliers = {}
    for col in NUMERIC_COLUMNS:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers[col] = int(((df[col] < lo) | (df[col] > hi)).sum())

    report = {
        "raw_rows": raw_rows,
        "rows_after_dedup": int(len(df)),
        "features": int(df.shape[1] - 1),
        "missing_values": missing,
        "duplicate_rows": int(raw_rows - len(df)),
        "target_distribution": df[TARGET_COLUMN].value_counts().to_dict(),
        "positive_share": round(float(df[TARGET_COLUMN].mean()), 4),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "numeric_features": NUMERIC_COLUMNS,
        "categorical_features": CATEGORICAL_COLUMNS,
        "iqr_outliers": outliers,
    }
    print("\n===== DATA AUDIT =====")
    print(f"Raw rows: {report['raw_rows']} | After dedup: {report['rows_after_dedup']}")
    print(f"Features: {report['features']} ({len(NUMERIC_COLUMNS)} numeric, "
          f"{len(CATEGORICAL_COLUMNS)} categorical)")
    print(f"Missing values: {report['missing_values'] or 'none'}")
    print(f"Duplicate rows removed: {report['duplicate_rows']}")
    print(f"Target distribution: {report['target_distribution']} "
          f"(positive share {report['positive_share']})")
    print(f"IQR outliers (reported, not removed): {report['iqr_outliers']}")
    print("======================\n")
    return report


def build_model_pipeline(estimator) -> Pipeline:
    return Pipeline([
        ("preprocess", build_preprocessing_pipeline()),
        ("classifier", estimator),
    ])


def default_estimator(config: dict, class_weight=None):
    params = {**config["base_params"]}
    if class_weight is not None:
        params["class_weight"] = class_weight
    return config["estimator_cls"](**params)


def compare_class_weight(config: dict, X_train, y_train) -> dict:
    print(f"\n--- Class-imbalance comparison: {config['human_name']} ---")
    results = {}
    for label, class_weight in (("class_weight=None", None),
                                ("class_weight=balanced", "balanced")):
        pipe = build_model_pipeline(default_estimator(config, class_weight))
        cv = cross_validate(pipe, X_train, y_train, CV)
        results[label] = cv
        print(f"  {label:<20} ROC-AUC {cv['roc_auc']['mean']:.4f} +/- "
              f"{cv['roc_auc']['std']:.4f} | accuracy {cv['accuracy']['mean']:.4f} "
              f"| sensitivity {cv['recall']['mean']:.4f} | "
              f"specificity {cv['specificity']['mean']:.4f}")
    return results


def tune_hyperparameters(config: dict, X_train, y_train) -> tuple[dict, Pipeline]:
    print(f"\n--- Tuning {config['human_name']} "
          f"({config['n_iter']} random combinations, 5-fold CV, score=ROC-AUC) ---")
    search = RandomizedSearchCV(
        estimator=build_model_pipeline(config["estimator_cls"](**config["base_params"])),
        param_distributions=config["param_grid"],
        n_iter=config["n_iter"],
        scoring="roc_auc",
        cv=CV,
        random_state=RANDOM_STATE,
        n_jobs=SEARCH_N_JOBS,
        refit=False,
    )
    search.fit(X_train, y_train)
    best_params = search.best_params_
    print(f"  Best params: {best_params}")
    print(f"  Best CV ROC-AUC: {search.best_score_:.4f}")
    return best_params, search


def build_final_estimator(config: dict, best_params: dict):
    classifier_params = {
        key.replace("classifier__", ""): value
        for key, value in best_params.items()
    }
    return config["estimator_cls"](**{**config["base_params"], **classifier_params})


def compare_feature_selection(config: dict, estimator, X_train, y_train) -> tuple[bool, dict]:
    full_pipe = build_model_pipeline(estimator)
    full_cv = cross_validate(full_pipe, X_train, y_train, CV)

    select_pipe = Pipeline([
        ("preprocess", build_preprocessing_pipeline()),
        ("select", SelectKBest(mutual_info_classif, k=SELECT_K)),
        ("classifier", clone(estimator)),
    ])
    select_cv = cross_validate(select_pipe, X_train, y_train, CV)

    comparison = {
        "all_features": full_cv["roc_auc"]["mean"],
        "selected_features_k": SELECT_K,
        "selected_features": select_cv["roc_auc"]["mean"],
    }
    use_selection = select_cv["roc_auc"]["mean"] > full_cv["roc_auc"]["mean"]
    print(f"\n--- Feature-selection test: {config['human_name']} ---")
    print(f"  All features CV ROC-AUC:      {full_cv['roc_auc']['mean']:.4f}")
    print(f"  SelectKBest(k={SELECT_K}) CV ROC-AUC: {select_cv['roc_auc']['mean']:.4f}")
    print(f"  -> keeping {'selected features' if use_selection else 'ALL features'}")
    return use_selection, comparison


def build_final_pipeline(config: dict, estimator, use_selection: bool) -> Pipeline:
    steps = [("preprocess", build_preprocessing_pipeline())]
    if use_selection:
        steps.append(("select", SelectKBest(mutual_info_classif, k=SELECT_K)))
    steps.append(("classifier", estimator))
    return Pipeline(steps)


def feature_importance_for(pipeline: Pipeline) -> dict:
    feature_names = get_feature_names(pipeline)
    classifier = pipeline.named_steps["classifier"]
    if isinstance(classifier, LogisticRegression):
        coefs = np.ravel(classifier.coef_)
        return {
            "type": "coefficients",
            "values": {name: round(float(c), 4)
                       for name, c in zip(feature_names, coefs)},
        }
    importances = classifier.feature_importances_
    return {
        "type": "importance",
        "values": {name: round(float(v), 4)
                   for name, v in zip(feature_names, importances)},
    }


def train() -> dict:
    settings = get_settings()
    df, raw_rows = load_dataset(settings.DATASET_PATH)
    audit = audit_dataset(df, raw_rows)

    X = df[ALL_COLUMNS]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y,
    )
    print(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")

    all_metrics: dict[str, dict] = {}
    saved_models: list[dict] = []
    feature_names: list[str] = []
    cv_reports: dict[str, dict] = {}
    imbalance_reports: dict[str, dict] = {}
    selection_reports: dict[str, dict] = {}

    for config in MODEL_CONFIGS:
        key = config["key"]
        print(f"\n{'=' * 60}\nTraining {config['human_name']}\n{'=' * 60}")

        baseline_pipe = build_model_pipeline(default_estimator(config))
        baseline_cv = cross_validate(baseline_pipe, X_train, y_train, CV)
        print(f"Baseline CV (defaults): ROC-AUC {baseline_cv['roc_auc']['mean']:.4f} "
              f"+/- {baseline_cv['roc_auc']['std']:.4f} | "
              f"accuracy {baseline_cv['accuracy']['mean']:.4f} | "
              f"sensitivity {baseline_cv['recall']['mean']:.4f} | "
              f"specificity {baseline_cv['specificity']['mean']:.4f}")

        imbalance_reports[key] = compare_class_weight(config, X_train, y_train)

        best_params, search = tune_hyperparameters(config, X_train, y_train)
        estimator = build_final_estimator(config, best_params)

        tuned_pipe = build_model_pipeline(estimator)
        final_cv = cross_validate(tuned_pipe, X_train, y_train, CV)
        cv_reports[key] = final_cv
        print(f"Tuned CV: ROC-AUC {final_cv['roc_auc']['mean']:.4f} +/- "
              f"{final_cv['roc_auc']['std']:.4f} | "
              f"accuracy {final_cv['accuracy']['mean']:.4f} | "
              f"sensitivity {final_cv['recall']['mean']:.4f} | "
              f"specificity {final_cv['specificity']['mean']:.4f}")

        use_selection, selection_reports[key] = compare_feature_selection(
            config, estimator, X_train, y_train)

        final_pipeline = build_final_pipeline(config, estimator, use_selection)
        final_pipeline.fit(X_train, y_train)
        y_proba = final_pipeline.predict_proba(X_test)[:, 1]
        y_pred = final_pipeline.predict(X_test)
        metrics = compute_metrics(y_test, y_pred, y_proba)
        metrics["feature_importance"] = feature_importance_for(final_pipeline)
        metrics["hyperparameters"] = best_params
        metrics["cv"] = {
            metric: {"mean": values["mean"], "std": values["std"]}
            for metric, values in final_cv.items()
        }
        metrics["cv"]["selection"] = selection_reports[key]
        all_metrics[key] = metrics
        print(f"\nFINAL TEST-SET ({config['human_name']}):")
        print(f"  Accuracy: {metrics['accuracy']} | Precision: {metrics['precision']} | "
              f"Sensitivity: {metrics['recall']} | Specificity: {metrics['specificity']} | "
              f"F1: {metrics['f1']} | ROC-AUC: {metrics['roc_auc']}")
        print(f"  Confusion matrix: {metrics['confusion_matrix']}")

        if not feature_names:
            feature_names = get_feature_names(final_pipeline)

        buffer = io.BytesIO()
        joblib.dump(final_pipeline, buffer)
        encrypted = encrypt_bytes(buffer.getvalue())
        out_path = settings.ENCRYPTED_MODELS_DIR / f"{key}.enc"
        out_path.write_bytes(encrypted)
        saved_models.append({
            "key": key,
            "human_name": config["human_name"],
            "algorithm": config["estimator_cls"].__name__,
            "path": str(out_path.relative_to(settings.ENCRYPTED_MODELS_DIR)),
            "encrypted": True,
        })
        print(f"  Encrypted pipeline saved -> {out_path.name}")

    print("\n" + format_metrics_table(all_metrics))
    print("\nThe application uses Logistic Regression as its single prediction"
          "model (the other pipelines above are produced for comparison during"
          "training only and are never used at runtime).")

    metrics_doc = {
        "version": settings.MODEL_VERSION,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "source": settings.DATASET_PATH.name,
            "rows_after_cleanup": int(len(df)),
            "train_rows": int(len(X_train)),
            "test_rows": int(len(X_test)),
            "target_distribution": df[TARGET_COLUMN].value_counts().to_dict(),
            "audit": audit,
        },
        "cv": cv_reports,
        "models": all_metrics,
        "feature_names": feature_names,
    }
    settings.METRICS_PATH.write_text(json.dumps(metrics_doc, indent=2))
    print(f"\nMetrics saved -> {settings.METRICS_PATH}")

    registry = {"version": settings.MODEL_VERSION, "models": saved_models}
    settings.ENCRYPTED_MODELS_DIR.joinpath("registry.json").write_text(
        json.dumps(registry, indent=2))
    print("Models encrypted successfully.")
    return metrics_doc


if __name__ == "__main__":
    print("Training Heart Disease Models...")
    try:
        train()
    except Exception as exc:
        print(f"Training failed: {exc}", file=sys.stderr)
        sys.exit(1)
