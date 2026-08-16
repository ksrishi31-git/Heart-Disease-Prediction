import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserRegister(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: EmailStr
    created_at: dt.datetime
    is_active: bool


class TokenResponse(BaseModel):
    access_token_expires_in: int
    token_type: str = "bearer"
    user: UserOut


class PasswordChange(BaseModel):
    old_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class SessionOut(BaseModel):
    id: int
    created_at: dt.datetime
    expires_at: dt.datetime
    revoked: bool
    ip_hash: str | None = None


class MessageOut(BaseModel):
    message: str


class PredictionRequest(BaseModel):
    age: int | float
    sex: str | int
    cp: str | int
    trestbps: int | float
    chol: int | float
    fbs: str | int | bool
    restecg: str | int
    thalach: int | float
    exang: str | int | bool
    oldpeak: int | float
    slope: str | int
    ca: str | int
    thal: str | int


class PredictionModelOut(BaseModel):
    model_key: str
    model_name: str
    metrics: dict[str, float]


class PredictionResultOut(BaseModel):
    prediction_id: str
    created_at: dt.datetime
    model_version: str
    prediction: int
    classification: str
    label: str
    probability: float
    risk_score_percent: float
    model: PredictionModelOut


class PredictionListItem(BaseModel):
    prediction_id: str
    created_at: dt.datetime
    consensus: str
    best_model: str
    best_model_name: str
    probability: float
    model_version: str


class PredictionDetailOut(PredictionResultOut):
    input_features: dict[str, Any]


class PredictionListOut(BaseModel):
    total: int
    items: list[PredictionListItem]


class FeatureOption(BaseModel):
    value: int
    label: str


class FeatureDefinitionOut(BaseModel):
    name: str
    kind: str
    label: str
    unit: str
    min: float | None
    max: float | None
    step: float
    options: list[FeatureOption]
    helper: str


class ModelMetricsOut(BaseModel):
    key: str
    human_name: str
    accuracy: float
    precision: float
    recall: float
    specificity: float
    f1: float
    roc_auc: float
    true_positives: int
    true_negatives: int
    false_positives: int
    false_negatives: int
    confusion_matrix: list[list[int]]
    roc_curve: dict[str, list[float]]
    feature_importance: dict


class MetricSetOut(BaseModel):
    accuracy: float
    precision: float
    sensitivity: float
    specificity: float
    f1: float
    roc_auc: float


class ModelInsightsOut(BaseModel):
    version: str
    training_date: str
    dataset: dict
    model: dict[str, Any]
    test_metrics: MetricSetOut
    cv_metrics: dict[str, float]
    confusion_matrix: list[list[int]]
    roc_curve: dict[str, list[float]]
    feature_importance: dict
    feature_names: list[str]


class HealthOut(BaseModel):
    status: str
    database: str
    models: str
    version: str
