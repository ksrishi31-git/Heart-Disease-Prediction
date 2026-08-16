import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Brain,
  ClipboardList,
  HeartPulse,
  ShieldCheck,
  Stethoscope,
  Thermometer,
  TestTube,
} from "lucide-react";
import { Alert, Card, CardHeader } from "../components/UI.jsx";
import { Field, RadioGroup, SelectInput, SubmitButton, TextInput } from "../components/FormControls.jsx";
import { predictionsApi } from "../services/predictions.js";
import { errorMessage } from "../services/api.js";
import { FEATURES, validateAll } from "../utils/validation.js";
import { formatPercent } from "../utils/format.js";

const DEFAULTS = {
  age: "", sex: "", cp: "", trestbps: "", chol: "", fbs: "",
  restecg: "", thalach: "", exang: "", oldpeak: "", slope: "", ca: "", thal: "",
};

const SECTIONS = [
  {
    id: "basic",
    title: "Basic Information",
    icon: Stethoscope,
    description: "Demographic details of the patient.",
    features: ["age", "sex"],
  },
  {
    id: "symptoms",
    title: "Symptoms",
    icon: Activity,
    description: "Chest pain characteristics.",
    features: ["cp", "exang"],
  },
  {
    id: "vitals",
    title: "Vital Measurements",
    icon: Thermometer,
    description: "Blood pressure, cholesterol, heart rate and ST depression.",
    features: ["trestbps", "chol", "thalach", "oldpeak"],
  },
  {
    id: "tests",
    title: "Medical Test Information",
    icon: TestTube,
    description: "Lab and ECG-derived results.",
    features: ["fbs", "restecg", "slope", "ca", "thal"],
  },
];

function featureByName(name) {
  return FEATURES.find((f) => f.name === name);
}

function PatientForm({ values, errors, onChange, onSubmit, loading }) {
  const handleChange = (name, value) => {
    const next = { ...values, [name]: value };
    const feature = featureByName(name);
    const error = feature ? validateFeatureLive(feature, value) : null;
    onChange(next, { ...errors, [name]: error });
  };

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-6">
      {SECTIONS.map((section) => (
        <Card key={section.id}>
          <CardHeader title={section.title} subtitle={section.description} icon={section.icon} />
          <div className="grid gap-5 p-5 sm:grid-cols-2">
            {section.features.map((name) => {
              const feature = featureByName(name);
              if (feature.kind === "numeric") {
                return (
                  <Field
                    key={name}
                    label={`${feature.label}${feature.unit ? ` (${feature.unit})` : ""}`}
                    helper={feature.helper}
                    error={errors[name]}
                    htmlFor={`field-${name}`}
                  >
                    <TextInput
                      id={`field-${name}`}
                      type="number"
                      inputMode="decimal"
                      step={feature.step}
                      min={feature.min}
                      max={feature.max}
                      placeholder={feature.unit ? `e.g. ${feature.min}–${feature.max}` : "e.g. 1.2"}
                      value={values[name]}
                      error={errors[name]}
                      onChange={(e) => handleChange(name, e.target.value)}
                    />
                  </Field>
                );
              }
              const isBinary = feature.options.length === 2;
              if (isBinary) {
                return (
                  <Field key={name} label={feature.label} helper={feature.helper} error={errors[name]}>
                    <RadioGroup
                      name={name}
                      groupLabel={feature.label}
                      options={feature.options}
                      value={values[name]}
                      onChange={(value) => handleChange(name, value)}
                    />
                  </Field>
                );
              }
              return (
                <Field key={name} label={feature.label} helper={feature.helper} error={errors[name]} htmlFor={`field-${name}`}>
                  <SelectInput
                    id={`field-${name}`}
                    options={feature.options}
                    value={values[name]}
                    error={errors[name]}
                    onChange={(e) => handleChange(name, e.target.value)}
                  />
                </Field>
              );
            })}
          </div>
        </Card>
      ))}

      <div className="flex flex-col items-center gap-3">
        <SubmitButton loading={loading} className="w-full max-w-md">
          {loading ? "Running prediction…" : "Run prediction"}
        </SubmitButton>
        <p className="text-center text-xs leading-relaxed text-muted">
          HeartGuard AI is an educational machine-learning system. Its predictions are{" "}
          <strong>not medical diagnoses</strong>. Do not use this result to make medical
          decisions. Consult a qualified healthcare professional for medical advice.
        </p>
      </div>
    </form>
  );
}

function validateFeatureLive(feature, value) {
  if (value === "" || value === null || value === undefined) return null;
  if (feature.kind === "numeric") {
    const num = Number(value);
    if (Number.isNaN(num)) return "Please enter a valid number.";
    if (num < feature.min) return `${feature.label} cannot be below ${feature.min}.`;
    if (num > feature.max) return `${feature.label} cannot exceed ${feature.max}.`;
  }
  return null;
}

function metricPercent(value) {
  if (value === null || value === undefined) return "—";
  return `${(value * 100).toFixed(2)}%`;
}

const PERFORMANCE_ROWS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "sensitivity", label: "Sensitivity / Recall" },
  { key: "specificity", label: "Specificity" },
  { key: "roc_auc", label: "ROC-AUC" },
  { key: "f1", label: "F1-score" },
];

function ResultPanel({ result }) {
  const positive = result.prediction === 1;
  const model = result.model;

  return (
    <div className="space-y-4">
      <Card className="overflow-hidden">
        <div className="px-5 py-6 text-center sm:px-8">
          <p className="text-xs font-semibold uppercase tracking-wide text-muted">Risk Classification</p>
          <div
            className={`mx-auto mt-4 inline-flex items-center gap-2 rounded-xl px-5 py-3 text-lg font-bold ring-1 ${
              positive
                ? "bg-rose-50 text-rose-700 ring-rose-200"
                : "bg-emerald-50 text-emerald-700 ring-emerald-200"
            }`}
          >
            {positive ? <AlertTriangle size={22} /> : <ShieldCheck size={22} />}
            <span>{result.classification}</span>
          </div>
          <p className="mx-auto mt-3 max-w-xl text-sm leading-relaxed text-muted">
            {positive
              ? "Model classified this input as the presence of the target heart-disease condition."
              : "Model classified this input as the absence of the target heart-disease condition."}
          </p>

          <div className="mx-auto mt-6 max-w-md rounded-xl border border-slate-200 bg-slate-50/60 px-5 py-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted">Model-estimated probability</p>
            <p className="mt-1 text-4xl font-bold text-ink">{formatPercent(result.probability)}</p>
            <p className="mt-1 text-xs leading-relaxed text-muted">
              Estimated probability of the positive class — a model output, not a medical
              certainty and not a 10-year cardiovascular event risk score.
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Prediction Model"
          subtitle="HeartGuard AI's fixed prediction model — used for every prediction"
          icon={Brain}
        />
        <div className="px-5 py-4">
          <p className="text-lg font-bold text-ink">{model.model_name}</p>
          <p className="mt-2 text-sm leading-relaxed text-ink">
            <span className="font-semibold">Why Logistic Regression?</span> HeartGuard AI uses
            Logistic Regression as its primary classification model because it provides
            probability-based binary classification and interpretable coefficients for this
            tabular dataset.
          </p>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Model Performance"
          subtitle="Real metrics measured on the held-out validation/test set during training — not hardcoded"
          icon={BarChart3}
        />
        <div className="px-5 py-4">
          <div className="overflow-hidden rounded-lg border border-slate-200">
            <table className="w-full text-sm">
              <tbody>
                {PERFORMANCE_ROWS.map((row) => (
                  <tr key={row.key} className="border-b border-slate-100 last:border-0">
                    <td className="px-4 py-2.5 text-muted">{row.label}</td>
                    <td className="px-4 py-2.5 text-right font-semibold tabular-nums text-ink">
                      {metricPercent(model.metrics?.[row.key])}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4 space-y-2 text-xs leading-relaxed text-muted">
            <p>
              <span className="font-semibold text-ink">Sensitivity / recall</span> measures how
              well the model identifies positive cases in the evaluation dataset. Higher
              sensitivity can be important in screening-oriented applications because missed
              positive cases may be more concerning.
            </p>
            <p>
              <span className="font-semibold text-ink">Specificity</span> measures how well the
              model identifies negative cases in the evaluation dataset.
            </p>
            <p>These are dataset evaluation metrics, not clinical guarantees.</p>
          </div>
        </div>
      </Card>

      <Alert tone="warning">
        <strong>Educational ML demonstration — not a medical diagnosis.</strong>
        <span className="mt-1 block">
          This result is based on patterns learned from the training data. It should not be used
          as a standalone basis for medical decisions. Clinical assessment and appropriate
          confirmatory testing by a qualified healthcare professional are required for real
          medical decision-making.
        </span>
      </Alert>
    </div>
  );
}

export default function Predict() {
  const [values, setValues] = useState(DEFAULTS);
  const [errors, setErrors] = useState({});
  const [result, setResult] = useState(null);
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const validationErrors = validateAll(values);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      setServerError("Please fix the highlighted fields before running the prediction.");
      return;
    }
    setLoading(true);
    setServerError("");
    try {
      const { data } = await predictionsApi.create(values);
      setResult(data);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (error) {
      setServerError(errorMessage(error, "Unable to process prediction. Please try again."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <span className="rounded-lg bg-primary-50 p-2 text-primary-700">
          <HeartPulse size={22} />
        </span>
        <div>
          <h1 className="text-2xl font-bold text-ink">New Prediction</h1>
          <p className="text-sm text-muted">
            Enter patient parameters — the backend processes the submitted features through the
            Logistic Regression model and returns a unified prediction.
          </p>
        </div>
      </div>

      {result ? (
        <>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 text-sm text-muted">
              <ShieldCheck size={16} className="text-emerald-600" />
              Result encrypted and stored securely in your history.
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => { setResult(null); setValues(DEFAULTS); setErrors({}); }}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-ink hover:border-slate-400"
              >
                New prediction
              </button>
              <Link to="/history" className="flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-ink hover:border-slate-400">
                <ClipboardList size={15} />
                History
              </Link>
            </div>
          </div>
          <ResultPanel result={result} />
        </>
      ) : (
        <>
          {serverError && <Alert tone="error">{serverError}</Alert>}
          <PatientForm
            values={values}
            errors={errors}
            onChange={(next, nextErrors) => { setValues(next); setErrors(nextErrors); }}
            onSubmit={handleSubmit}
            loading={loading}
          />
        </>
      )}
    </div>
  );
}
