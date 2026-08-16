import uuid

from app.ml.model_manager import MODEL_KEY, ModelManager


def test_create_prediction_returns_single_unified_result(
        client, auth_headers, valid_payload, models_ready):
    response = client.post("/api/predictions", json=valid_payload,
                           cookies=auth_headers["cookies"])
    assert response.status_code == 201
    data = response.json()
    assert "models" not in data
    assert data["prediction"] in (0, 1)
    assert data["classification"] in ("Heart Disease Detected",
                                      "No Heart Disease Detected")
    assert data["label"] in ("Positive", "Negative")
    assert 0.0 <= data["probability"] <= 1.0
    assert 0.0 <= data["risk_score_percent"] <= 100.0

    model = data["model"]
    assert model["model_key"] == "logistic_regression"
    assert model["model_name"] == "Logistic Regression"
    metrics = model["metrics"]
    assert set(metrics) == {"accuracy", "precision", "sensitivity",
                            "specificity", "f1", "roc_auc"}
    assert 0.0 < metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["sensitivity"] <= 1.0
    assert 0.0 <= metrics["specificity"] <= 1.0
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    assert 0.0 <= metrics["f1"] <= 1.0


def test_prediction_metrics_are_real_cv_means(
        client, auth_headers, valid_payload, models_ready, created_prediction):
    manager = ModelManager.get_instance()
    cv = manager.metrics()["cv"][MODEL_KEY]
    metrics = created_prediction["model"]["metrics"]
    assert metrics["accuracy"] == cv["accuracy"]["mean"]
    assert metrics["sensitivity"] == cv["recall"]["mean"]
    assert metrics["specificity"] == cv["specificity"]["mean"]
    assert metrics["roc_auc"] == cv["roc_auc"]["mean"]
    assert metrics["f1"] == cv["f1"]["mean"]


def test_prediction_requires_auth(client, valid_payload):
    response = client.post("/api/predictions", json=valid_payload)
    assert response.status_code == 401


def test_age_out_of_range_rejected(client, auth_headers, valid_payload,
                                   models_ready):
    payload = dict(valid_payload, age=200)
    response = client.post("/api/predictions", json=payload,
                           cookies=auth_headers["cookies"])
    assert response.status_code == 422
    assert "age" in response.json()["detail"].lower()


def test_invalid_label_rejected(client, auth_headers, valid_payload,
                                models_ready):
    payload = dict(valid_payload, cp="Not a real pain type")
    response = client.post("/api/predictions", json=payload,
                           cookies=auth_headers["cookies"])
    assert response.status_code == 422


def test_missing_field_rejected(client, auth_headers, valid_payload,
                                models_ready):
    payload = dict(valid_payload)
    del payload["thal"]
    response = client.post("/api/predictions", json=payload,
                           cookies=auth_headers["cookies"])
    assert response.status_code == 422


def test_list_and_detail(client, auth_headers, valid_payload, models_ready,
                         created_prediction):
    list_response = client.get("/api/predictions",
                               cookies=auth_headers["cookies"])
    assert list_response.status_code == 200
    assert list_response.json()["total"] >= 1

    pid = created_prediction["prediction_id"]
    detail = client.get(f"/api/predictions/{pid}",
                        cookies=auth_headers["cookies"])
    assert detail.status_code == 200
    assert detail.json()["input_features"]["sex"] == "Male"
    assert detail.json()["model_version"]
    assert detail.json()["classification"] in ("Heart Disease Detected",
                                                "No Heart Disease Detected")
    assert detail.json()["model"]["model_name"] == "Logistic Regression"


def test_other_user_cannot_access(client, auth_headers, valid_payload,
                                  models_ready, created_prediction):
    email = f"other{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPass1"
    other = client.post("/api/auth/register", json={
        "name": "Other User", "email": email,
        "password": password, "confirm_password": password})
    assert other.status_code == 201

    pid = created_prediction["prediction_id"]
    response = client.get(f"/api/predictions/{pid}",
                          cookies=other.cookies)
    assert response.status_code == 404


def test_other_user_cannot_delete(client, auth_headers, valid_payload,
                                  models_ready, created_prediction):
    email = f"other2{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPass1"
    other = client.post("/api/auth/register", json={
        "name": "Other2", "email": email,
        "password": password, "confirm_password": password})
    pid = created_prediction["prediction_id"]
    response = client.delete(f"/api/predictions/{pid}", cookies=other.cookies)
    assert response.status_code == 404


def test_delete_prediction(client, auth_headers, valid_payload, models_ready,
                           created_prediction):
    pid = created_prediction["prediction_id"]
    response = client.delete(f"/api/predictions/{pid}",
                             cookies=auth_headers["cookies"])
    assert response.status_code == 200
    detail = client.get(f"/api/predictions/{pid}",
                        cookies=auth_headers["cookies"])
    assert detail.status_code == 404


def test_unknown_prediction_404(client, auth_headers):
    response = client.get("/api/predictions/nonexistent-id",
                          cookies=auth_headers["cookies"])
    assert response.status_code == 404


def test_dashboard_stats(client, auth_headers, valid_payload, models_ready,
                         created_prediction):
    response = client.get("/api/predictions/stats",
                          cookies=auth_headers["cookies"])
    assert response.status_code == 200
    stats = response.json()
    assert stats["total_predictions"] >= 1
    assert stats["latest"]["prediction_id"] == created_prediction["prediction_id"]
