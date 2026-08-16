from app.ml.model_manager import MODEL_KEY, MODEL_NAME, ModelManager, ModelNotReadyError

CLASSIFICATION_LABELS = {
    1: "Heart Disease Detected",
    0: "No Heart Disease Detected",
}

MODEL_LABELS = {1: "Positive", 0: "Negative"}


def run_prediction(features: dict) -> dict:
    manager = ModelManager.get_instance()
    metrics = manager.metrics()
    if metrics is None:
        raise ModelNotReadyError(
            "Model evaluation metrics are not available. Run "
            "`python -m app.ml.train` first."
        )

    probability, prediction = manager.predict_single(features)

    return {
        "prediction": prediction,
        "classification": CLASSIFICATION_LABELS[prediction],
        "label": MODEL_LABELS[prediction],
        "probability": probability,
        "risk_score_percent": round(probability * 100, 1),
        "model": {
            "model_key": MODEL_KEY,
            "model_name": MODEL_NAME,
            "metrics": _model_metrics(metrics),
        },
    }


def _model_metrics(metrics_doc: dict) -> dict:
    cv = metrics_doc.get("cv", {}).get(MODEL_KEY, {})
    if isinstance(cv.get("accuracy"), dict) and "mean" in cv["accuracy"]:
        return {
            "accuracy": cv["accuracy"]["mean"],
            "precision": cv["precision"]["mean"],
            "sensitivity": cv["recall"]["mean"],
            "specificity": cv["specificity"]["mean"],
            "f1": cv["f1"]["mean"],
            "roc_auc": cv["roc_auc"]["mean"],
        }
    raw = metrics_doc.get("models", {}).get(MODEL_KEY, {})
    return {
        "accuracy": raw.get("accuracy"),
        "precision": raw.get("precision"),
        "sensitivity": raw.get("recall"),
        "specificity": raw.get("specificity"),
        "f1": raw.get("f1"),
        "roc_auc": raw.get("roc_auc"),
    }
