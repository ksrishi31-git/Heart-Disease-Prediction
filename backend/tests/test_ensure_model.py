import inspect

import pytest

from app.core.config import get_settings
from app.ml import ensure_model


def test_ensure_model_never_trains_other_models():
    """The production startup module must only ever prepare Logistic
    Regression — Decision Tree and Random Forest must not appear in it."""
    source = inspect.getsource(ensure_model)
    assert "DecisionTree" not in source
    assert "RandomForest" not in source
    assert "logistic_regression" in source
    assert "MODEL_CONFIGS[0]" in source or "c[\"key\"] == MODEL_KEY" in source


def test_ensure_model_skips_when_production_model_present():
    model_path = get_settings().ENCRYPTED_MODELS_DIR / "logistic_regression.enc"
    if not model_path.exists():
        pytest.skip("encrypted Logistic Regression model is not present")
    assert ensure_model._model_is_ready() is True
    assert ensure_model.ensure_production_model() == {}
