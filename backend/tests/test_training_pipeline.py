import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline

from app.core.config import get_settings
from app.ml.evaluate import CV_METRICS, compute_metrics, cross_validate
from app.ml.preprocess import ALL_COLUMNS, TARGET_COLUMN, build_preprocessing_pipeline, get_feature_names
from app.ml.train import (
    MODEL_CONFIGS,
    build_final_pipeline,
    build_model_pipeline,
    compare_class_weight,
    compare_feature_selection,
    default_estimator,
    tune_hyperparameters,
)
from app.ml import train as train_module


def _sample_data(n=150, random_state=1):
    df = pd.read_csv(get_settings().DATASET_PATH, encoding="utf-8-sig")
    df = df.drop_duplicates().sample(n=n, random_state=random_state)
    return df


def _split_sample(n=150):
    from sklearn.model_selection import train_test_split

    df = _sample_data(n=n)
    X = df[ALL_COLUMNS]
    y = df[TARGET_COLUMN]
    return train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)


def test_audit_dataset_reports_expected_fields():
    df = _sample_data()
    report = train_module.audit_dataset(df, raw_rows=len(df))
    assert report["features"] == 13
    assert report["duplicate_rows"] == 0
    assert set(report["target_distribution"]) == {0, 1}
    assert len(report["numeric_features"]) == 5
    assert len(report["categorical_features"]) == 8
    assert "iqr_outliers" in report
    assert len(df) == report["rows_after_dedup"]


def test_cross_validate_reports_all_metrics():
    X_train, X_test, y_train, y_test = _split_sample()
    pipe = build_model_pipeline(
        LogisticRegression(max_iter=500, solver="liblinear"))
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    result = cross_validate(pipe, X_train, y_train, cv)
    assert set(result.keys()) == set(CV_METRICS)
    for metric, stats in result.items():
        assert 0.0 <= stats["mean"] <= 1.0
        assert stats["std"] >= 0.0


def test_cross_validate_fits_only_on_training_fold():
    X_train, X_test, y_train, y_test = _split_sample()
    pipe = build_model_pipeline(
        LogisticRegression(max_iter=500, solver="liblinear"))
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cross_validate(pipe, X_train, y_train, cv)
    assert not hasattr(pipe.named_steps["classifier"], "classes_")


def test_compute_metrics_includes_specificity():
    X_train, X_test, y_train, y_test = _split_sample()
    pipe = build_model_pipeline(
        LogisticRegression(max_iter=500, solver="liblinear"))
    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]
    metrics = compute_metrics(y_test, y_pred, y_proba)
    assert "specificity" in metrics
    assert 0.0 <= metrics["specificity"] <= 1.0
    assert "confusion_matrix" in metrics


def test_tune_hyperparameters_stays_within_grid():
    X_train, X_test, y_train, y_test = _split_sample()
    config = MODEL_CONFIGS[0]
    best_params, search = tune_hyperparameters(config, X_train, y_train)
    c_values = [0.01, 0.1, 1, 10, 100]
    assert best_params["classifier__C"] in c_values
    assert best_params["classifier__class_weight"] in (None, "balanced")
    assert 0.0 <= search.best_score_ <= 1.0


def test_compare_class_weight_returns_both_variants():
    X_train, X_test, y_train, y_test = _split_sample()
    config = MODEL_CONFIGS[0]
    results = compare_class_weight(config, X_train, y_train)
    assert set(results.keys()) == {"class_weight=None", "class_weight=balanced"}
    for cv_result in results.values():
        assert "roc_auc" in cv_result


def test_compare_feature_selection_returns_decision():
    X_train, X_test, y_train, y_test = _split_sample()
    config = MODEL_CONFIGS[0]
    estimator = default_estimator(config)
    use_selection, comparison = compare_feature_selection(
        config, estimator, X_train, y_train)
    assert isinstance(use_selection, bool)
    assert comparison["all_features"] >= 0.0
    assert comparison["selected_features"] >= 0.0


def test_build_final_pipeline_with_and_without_selection():
    X_train, X_test, y_train, y_test = _split_sample()
    config = MODEL_CONFIGS[0]
    estimator = default_estimator(config)

    plain = build_final_pipeline(config, estimator, use_selection=False)
    plain.fit(X_train, y_train)
    assert plain.predict(X_test).shape[0] == len(X_test)
    assert "select" not in plain.named_steps

    selected = build_final_pipeline(config, estimator, use_selection=True)
    selected.fit(X_train, y_train)
    assert "select" in selected.named_steps
    names = get_feature_names(selected)
    assert len(names) > 0
    assert all(name in get_feature_names(plain) for name in names)


def test_pipeline_serializes_full_preprocessing_and_classifier():
    import io

    import joblib

    X_train, X_test, y_train, y_test = _split_sample()
    config = MODEL_CONFIGS[0]
    estimator = default_estimator(config)
    pipeline = build_final_pipeline(config, estimator, use_selection=False)
    pipeline.fit(X_train, y_train)

    buffer = io.BytesIO()
    joblib.dump(pipeline, buffer)
    buffer.seek(0)
    reloaded = joblib.load(buffer)
    assert isinstance(reloaded, Pipeline)
    assert "preprocess" in reloaded.named_steps
    assert "classifier" in reloaded.named_steps
    assert reloaded.predict(X_test).shape[0] == len(X_test)


def test_metrics_json_format():
    import json

    settings = get_settings()
    metrics = json.loads(settings.METRICS_PATH.read_text())
    assert metrics["version"] == settings.MODEL_VERSION
    assert metrics["dataset"]["rows_after_cleanup"] == 302
    for values in metrics["models"].values():
        for key in ("accuracy", "precision", "recall", "f1", "roc_auc",
                    "confusion_matrix", "roc_curve", "feature_importance",
                    "hyperparameters", "cv"):
            assert key in values
        assert 0.0 <= values["roc_auc"] <= 1.0
    lr = metrics["models"]["logistic_regression"]
    assert 0.0 < lr["roc_auc"] <= 1.0
    assert lr["confusion_matrix"][0][0] + lr["confusion_matrix"][0][1] > 0


def test_metrics_json_distinguishes_cv_and_test_metrics():
    import json

    settings = get_settings()
    metrics = json.loads(settings.METRICS_PATH.read_text())

    assert set(metrics["cv"].keys()) == set(metrics["models"].keys())
    for key in metrics["cv"]:
        cv_block = metrics["cv"][key]
        test_block = metrics["models"][key]
        for metric in ("accuracy", "precision", "recall", "specificity",
                       "f1", "roc_auc"):
            assert "mean" in cv_block[metric]
            assert "std" in cv_block[metric]
        assert 0.0 <= test_block["roc_auc"] <= 1.0
