from dataclasses import dataclass, field

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_COLUMNS = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL_COLUMNS = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]
ALL_COLUMNS = NUMERIC_COLUMNS + CATEGORICAL_COLUMNS
TARGET_COLUMN = "target"


@dataclass(frozen=True)
class FeatureDef:
    name: str
    kind: str
    label: str
    unit: str = ""
    min: float | None = None
    max: float | None = None
    step: float = 1
    options: dict[int, str] = field(default_factory=dict)
    helper: str = ""


FEATURE_DEFINITIONS: list[FeatureDef] = [
    FeatureDef("age", "numeric", "Age", "years", 1, 120, 1,
               helper="Patient's age in years."),
    FeatureDef("sex", "categorical", "Sex", options={0: "Female", 1: "Male"},
               helper="Biological sex."),
    FeatureDef("cp", "categorical", "Chest pain type",
               options={0: "Typical angina", 1: "Atypical angina",
                        2: "Non-anginal pain", 3: "Asymptomatic"},
               helper="Type of chest pain reported."),
    FeatureDef("trestbps", "numeric", "Resting blood pressure", "mm Hg", 90, 200, 1,
               helper="Resting blood pressure on admission."),
    FeatureDef("chol", "numeric", "Serum cholesterol", "mg/dl", 100, 600, 1,
               helper="Serum cholesterol level."),
    FeatureDef("fbs", "categorical", "Fasting blood sugar > 120 mg/dl",
               options={0: "No", 1: "Yes"},
               helper="Whether fasting blood sugar exceeds 120 mg/dl."),
    FeatureDef("restecg", "categorical", "Resting ECG result",
               options={0: "Normal", 1: "ST-T wave abnormality",
                        2: "Left ventricular hypertrophy"},
               helper="Result of the resting electrocardiogram."),
    FeatureDef("thalach", "numeric", "Maximum heart rate achieved", "bpm", 60, 220, 1,
               helper="Highest heart rate reached during exercise."),
    FeatureDef("exang", "categorical", "Exercise-induced angina",
               options={0: "No", 1: "Yes"},
               helper="Angina triggered by exercise."),
    FeatureDef("oldpeak", "numeric", "ST depression (oldpeak)", "", 0, 6.5, 0.1,
               helper="ST depression induced by exercise relative to rest."),
    FeatureDef("slope", "categorical", "Slope of the peak exercise ST segment",
               options={0: "Upsloping", 1: "Flat", 2: "Downsloping"},
               helper="Slope of the ST segment during peak exercise."),
    FeatureDef("ca", "categorical", "Major vessels coloured by fluoroscopy",
               options={0: "0 vessels", 1: "1 vessel", 2: "2 vessels",
                        3: "3 vessels", 4: "4 vessels"},
               helper="Number of major vessels visualised by fluoroscopy."),
    FeatureDef("thal", "categorical", "Thalassemia",
               options={0: "Unknown / not reported", 1: "Normal",
                        2: "Fixed defect", 3: "Reversible defect"},
               helper="Thalassemia blood-flow result."),
]


def build_preprocessing_pipeline() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_COLUMNS),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False),
             CATEGORICAL_COLUMNS),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def get_feature_names(pipeline) -> list[str]:
    names = list(pipeline.named_steps["preprocess"].get_feature_names_out())
    select = pipeline.named_steps.get("select")
    if select is not None:
        support = select.get_support()
        names = [n for n, keep in zip(names, support) if keep]
    return names


def map_form_to_dataset(form_data: dict) -> dict:
    mapping: dict[str, dict] = {}
    for feature in FEATURE_DEFINITIONS:
        if feature.kind == "categorical":
            mapping[feature.name] = {
                label: value for value, label in feature.options.items()
            }

    result: dict = {}
    for feature in FEATURE_DEFINITIONS:
        raw = form_data.get(feature.name)
        if raw is None:
            raise ValueError(f"Missing value for '{feature.name}'")
        if feature.kind == "numeric":
            value = float(raw)
            if feature.min is not None and value < feature.min:
                raise ValueError(f"'{feature.name}' is below the minimum "
                                 f"({feature.min})")
            if feature.max is not None and value > feature.max:
                raise ValueError(f"'{feature.name}' is above the maximum "
                                 f"({feature.max})")
            result[feature.name] = value
        else:
            if isinstance(raw, bool) or isinstance(raw, int):
                candidate = int(raw)
                if candidate in feature.options:
                    result[feature.name] = candidate
                    continue
            label = str(raw)
            if label not in mapping[feature.name]:
                raise ValueError(
                    f"Invalid value '{label}' for '{feature.name}'. "
                    f"Expected one of: {', '.join(mapping[feature.name])}"
                )
            result[feature.name] = mapping[feature.name][label]
    return result


def validate_features(features: dict) -> None:
    for feature in FEATURE_DEFINITIONS:
        if feature.name not in features:
            raise ValueError(f"Missing feature '{feature.name}'")
        value = features[feature.name]
        if feature.kind == "numeric":
            value = float(value)
            if feature.min is not None and value < feature.min:
                raise ValueError(f"'{feature.name}' below minimum {feature.min}")
            if feature.max is not None and value > feature.max:
                raise ValueError(f"'{feature.name}' above maximum {feature.max}")
        else:
            if int(value) not in feature.options:
                raise ValueError(f"'{feature.name}' has invalid value {value}")
