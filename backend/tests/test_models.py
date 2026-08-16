from app.ml.model_manager import MODEL_KEY, ModelManager


def test_insights_returns_only_logistic_regression(client, models_ready):
    response = client.get("/api/models/insights")
    assert response.status_code == 200
    data = response.json()
    assert data["model"]["key"] == "logistic_regression"
    assert data["model"]["name"] == "Logistic Regression"
    assert "models" not in data
    assert "selected_model" not in data
    assert "best_model" not in data

    for section in ("test_metrics", "cv_metrics"):
        metrics = data[section]
        for key in ("accuracy", "sensitivity", "specificity", "f1", "roc_auc"):
            assert 0 <= metrics[key] <= 1

    cm = data["confusion_matrix"]
    assert len(cm) == 2 and all(len(row) == 2 for row in cm)
    assert sum(sum(row) for row in cm) == 61
    assert "fpr" in data["roc_curve"] and "tpr" in data["roc_curve"]
    assert data["feature_importance"]["type"] == "coefficients"
    assert data["feature_importance"]["values"]


def test_get_model_returns_logistic_regression(client, models_ready):
    response = client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "logistic_regression"
    assert data["human_name"] == "Logistic Regression"
    assert data["confusion_matrix"] == [
        [data["true_negatives"], data["false_positives"]],
        [data["false_negatives"], data["true_positives"]],
    ]
    assert 0 <= data["accuracy"] <= 1
    assert 0 <= data["roc_auc"] <= 1
    assert "specificity" in data
    assert "roc_curve" in data
    assert "feature_importance" in data


def test_unknown_models_return_404(client, models_ready):
    for name in ("decision_tree", "random_forest", "does_not_exist"):
        response = client.get(f"/api/models/{name}/metrics")
        assert response.status_code == 404


def test_feature_definitions(client, models_ready):
    response = client.get("/api/models/features")
    assert response.status_code == 200
    features = response.json()
    assert len(features) == 13
    names = {f["name"] for f in features}
    assert {"age", "cp", "thal", "ca"} <= names
    cp = next(f for f in features if f["name"] == "cp")
    assert {o["value"] for o in cp["options"]} == {0, 1, 2, 3}


def test_metrics_not_hardcoded():
    import json

    from app.core.config import get_settings

    settings = get_settings()
    metrics = json.loads(settings.METRICS_PATH.read_text())
    assert metrics["version"] == settings.MODEL_VERSION
    assert metrics["dataset"]["rows_after_cleanup"] == 302
    lr = metrics["models"][MODEL_KEY]
    assert 0.5 < lr["accuracy"] <= 1.0
    assert lr["confusion_matrix"][1][1] + lr["confusion_matrix"][1][0] > 0


def test_manager_serves_only_logistic_regression(client, models_ready):
    manager = ModelManager.get_instance()
    assert manager.is_loaded
    metrics = manager.model_metrics(MODEL_KEY)
    assert metrics["key"] == MODEL_KEY
    try:
        manager.model_metrics("random_forest")
        assert False, "expected KeyError for a non-existent model"
    except KeyError:
        pass
