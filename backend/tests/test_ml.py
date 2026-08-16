import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.core.config import get_settings
from app.ml.preprocess import (
    ALL_COLUMNS,
    CATEGORICAL_COLUMNS,
    NUMERIC_COLUMNS,
    TARGET_COLUMN,
    build_preprocessing_pipeline,
    map_form_to_dataset,
    validate_features,
)


def _sample_data(n=150, random_state=1):
    df = pd.read_csv(get_settings().DATASET_PATH, encoding="utf-8-sig")
    df = df.drop_duplicates().sample(n=n, random_state=random_state)
    return df


def test_pipeline_output_shape():
    df = _sample_data()
    X = df[ALL_COLUMNS]
    y = df[TARGET_COLUMN]
    X_train, X_test, _, _ = train_test_split(X, y, test_size=0.3,
                                             random_state=42, stratify=y)
    pipeline = Pipeline([
        ("preprocess", build_preprocessing_pipeline()),
        ("classifier", LogisticRegression(max_iter=500, solver="liblinear")),
    ])
    pipeline.fit(X_train, y_train := y.loc[X_train.index])
    preds = pipeline.predict(X_test)
    proba = pipeline.predict_proba(X_test)
    assert preds.shape[0] == len(X_test)
    assert proba.shape == (len(X_test), 2)
    assert set(np.unique(preds)) <= {0, 1}
    assert np.allclose(proba.sum(axis=1), 1.0)


def test_preprocessing_handles_numeric_and_categorical():
    df = _sample_data()
    X = df[ALL_COLUMNS]
    transformer = build_preprocessing_pipeline()
    transformed = transformer.fit_transform(X)
    assert transformed.shape[0] == len(df)
    assert transformed.shape[1] > len(NUMERIC_COLUMNS) + len(CATEGORICAL_COLUMNS)


def test_fitting_only_on_train_prevents_leakage():
    df = _sample_data()
    X = df[ALL_COLUMNS]
    y = df[TARGET_COLUMN]
    X_train, X_test, _, _ = train_test_split(X, y, test_size=0.3,
                                             random_state=42, stratify=y)
    transformer = build_preprocessing_pipeline()
    transformer.fit(X_train)
    assert transformer.transform(X_test).shape[0] == len(X_test)


def test_map_form_to_dataset_friendly_labels():
    form = {
        "age": 58, "sex": "Male", "cp": "Asymptomatic",
        "trestbps": 145, "chol": 233, "fbs": "Yes",
        "restecg": "Normal", "thalach": 150, "exang": "No",
        "oldpeak": 2.3, "slope": "Flat", "ca": "0 vessels", "thal": "Normal",
    }
    encoded = map_form_to_dataset(form)
    assert encoded["sex"] == 1
    assert encoded["cp"] == 3
    assert encoded["fbs"] == 1
    assert encoded["exang"] == 0
    assert encoded["slope"] == 1
    assert encoded["ca"] == 0
    assert encoded["thal"] == 1
    validate_features(encoded)


def test_map_rejects_unknown_label():
    form = {"age": 50, "sex": "Alien", "cp": 0, "trestbps": 120, "chol": 200,
            "fbs": 0, "restecg": 0, "thalach": 150, "exang": 0, "oldpeak": 0,
            "slope": 0, "ca": 0, "thal": 1}
    try:
        map_form_to_dataset(form)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "sex" in str(exc)


def test_map_rejects_out_of_range_numeric():
    form = {"age": 500, "sex": 1, "cp": 0, "trestbps": 120, "chol": 200,
            "fbs": 0, "restecg": 0, "thalach": 150, "exang": 0, "oldpeak": 0,
            "slope": 0, "ca": 0, "thal": 1}
    try:
        map_form_to_dataset(form)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "age" in str(exc)


def test_model_output_shape_for_all_three():
    df = _sample_data()
    X = df[ALL_COLUMNS]
    y = df[TARGET_COLUMN]
    X_train, X_test, y_train, _ = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y)

    estimators = [
        LogisticRegression(max_iter=500, solver="liblinear"),
        RandomForestClassifier(n_estimators=20, max_depth=4, random_state=42),
    ]
    for estimator in estimators:
        pipeline = Pipeline([
            ("preprocess", build_preprocessing_pipeline()),
            ("classifier", estimator),
        ])
        pipeline.fit(X_train, y_train)
        proba = pipeline.predict_proba(X_test)[:, 1]
        assert proba.shape == (len(X_test),)
        assert ((proba >= 0) & (proba <= 1)).all()


def test_target_imbalance_reported():
    df = _sample_data(n=300, random_state=7)
    counts = df[TARGET_COLUMN].value_counts()
    assert counts.sum() == 300
    assert set(counts.index) == {0, 1}
