import { useEffect, useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  Coins,
  GraduationCap,
  LineChart as LineIcon,
  ListChecks,
  Scale,
  ShieldCheck,
  Sigma,
  Sparkles,
  Workflow,
} from "lucide-react";
import { Alert, Badge, Card, CardHeader, Spinner } from "../components/UI.jsx";
import { ConfusionMatrix, MetricBars, RocCurve } from "../components/charts.jsx";
import { modelsApi } from "../services/predictions.js";
import { errorMessage } from "../services/api.js";
import { formatPercent } from "../utils/format.js";
import { FEATURES } from "../utils/validation.js";

const METRIC_ROWS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "precision", label: "Precision" },
  { key: "sensitivity", label: "Sensitivity / Recall" },
  { key: "specificity", label: "Specificity" },
  { key: "f1", label: "F1-score" },
  { key: "roc_auc", label: "ROC-AUC" },
];

const FLOW_STEPS = [
  "Patient Input",
  "Data Validation",
  "Feature Preprocessing",
  "Feature Scaling / Encoding",
  "Logistic Regression",
  "Probability",
  "Classification",
];

const WHY_POINTS = [
  "Produces probability estimates, not just hard labels",
  "Easy to interpret compared with many complex models",
  "Efficient for small and medium-sized tabular datasets",
  "Works well with scaled numerical and encoded categorical features",
  "Provides interpretable feature coefficients",
  "Strong baseline for binary classification",
  "Performs well on the HeartGuard AI dataset",
];

const ASSUMPTIONS = [
  "Binary outcome — the target is one of two classes (positive / negative)",
  "Independent observations — each row represents a distinct patient record",
  "A reasonable relationship between the predictors and the log-odds of the outcome",
  "Limited problematic multicollinearity among the predictors",
  "Appropriate preprocessing — numerical features are scaled and categorical features are encoded",
  "Adequate sample size relative to the number of features",
];

const MODEL_FEATURES = FEATURES.map((f, i) => ({ n: i + 1, label: f.label }));

function MetricTable({ title, subtitle, metrics }) {
  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <div className="border-b border-slate-100 px-4 py-3">
        <h4 className="text-sm font-semibold text-ink">{title}</h4>
        {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
      </div>
      <table className="w-full text-sm">
        <tbody>
          {METRIC_ROWS.map((row) => (
            <tr key={row.key} className="border-b border-slate-100 last:border-0">
              <td className="px-4 py-2.5 text-muted">{row.label}</td>
              <td className="px-4 py-2.5 text-right font-semibold tabular-nums text-ink">
                {metrics?.[row.key] != null ? `${(metrics[row.key] * 100).toFixed(2)}%` : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function ModelInsights() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const { data } = await modelsApi.insights();
        setData(data);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const coefEntries = useMemo(() => {
    const values = data?.feature_importance?.values || {};
    return Object.entries(values)
      .map(([name, value]) => ({ name, value: Number(value) }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
      .slice(0, 10);
  }, [data]);
  const maxCoef = Math.max(...coefEntries.map((e) => Math.abs(e.value)), 1);

  if (loading) return <Spinner label="Loading model insights…" />;
  if (error) return <Alert tone="error">{error}</Alert>;
  if (!data) return null;

  const { model, test_metrics: testMetrics, cv_metrics: cvMetrics } = data;

  const prfData = [
    { name: "Precision", value: testMetrics.precision, fill: "#0d9488" },
    { name: "Recall", value: testMetrics.sensitivity, fill: "#f59e0b" },
    { name: "F1-score", value: testMetrics.f1, fill: "#3b82f6" },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Logistic Regression</h1>
        <p className="mt-1 text-sm text-muted">
          Inside the model — how HeartGuard AI estimates heart disease risk.
        </p>
        <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted">
          HeartGuard AI uses Logistic Regression as its primary classification model. It estimates
          the probability of the positive class from the patient&apos;s clinical input features and
          converts that probability into the final classification.
        </p>
        <p className="mt-2 text-xs text-muted">
          Model outputs are statistical predictions from the training data and are not medical
          diagnoses.
        </p>
      </div>

      <Card>
        <CardHeader
          title="What is Logistic Regression?"
          subtitle="A supervised classification algorithm, explained simply"
          icon={Brain}
        />
        <div className="space-y-3 px-5 py-4 text-sm leading-relaxed text-ink">
          <p>
            Logistic Regression is a supervised machine-learning classification algorithm used to
            estimate the probability of an outcome. In HeartGuard AI, it estimates the probability
            that the submitted patient features belong to the positive heart-disease class.
          </p>
          <p>
            Despite the &ldquo;regression&rdquo; in its name, it is primarily used for{" "}
            <strong>classification</strong> — it models the probability of a category rather than
            predicting a continuous number. That probability is then turned into a binary decision.
          </p>
          <ul className="grid gap-2 pt-1 sm:grid-cols-2">
            {[
              "Binary classification — two possible outcomes",
              "Probability output between 0 and 1",
              "Sigmoid / logistic function maps the linear score to a probability",
              "Decision threshold — the 0.5 cutoff converts probability to a class",
              "Feature coefficients — one learned weight per input feature",
            ].map((point) => (
              <li key={point} className="flex items-start gap-2 text-muted">
                <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-primary-600" />
                <span>{point}</span>
              </li>
            ))}
          </ul>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="How the Model Works"
          subtitle="From patient input to classification, step by step"
          icon={Workflow}
        />
        <div className="px-5 py-4">
          <div className="flex flex-wrap items-center gap-2">
            {FLOW_STEPS.map((step, i) => (
              <div key={step} className="flex items-center gap-2">
                <span className="rounded-lg bg-primary-50 px-3 py-2 text-xs font-semibold text-primary-800">
                  {step}
                </span>
                {i < FLOW_STEPS.length - 1 && <ArrowRight size={14} className="text-slate-300" />}
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm leading-relaxed text-muted">
            The model calculates a weighted combination of the input features and passes the result
            through a sigmoid function. The weights are the coefficients learned during training.
          </p>
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50/60 p-5 text-center">
            <p className="font-mono text-lg font-semibold text-ink">
              P(y = 1) = 1 / (1 + e<sup>−z</sup>)
            </p>
            <p className="mt-2 font-mono text-sm text-muted">
              z = β₀ + β₁x₁ + β₂x₂ + … + βₙxₙ
            </p>
            <p className="mx-auto mt-2 max-w-xl text-xs text-muted">
              where β₀ is the intercept, β₁ … βₙ are the learned feature coefficients, and x₁ … xₙ
              are the preprocessed feature values for a patient.
            </p>
          </div>
          <p className="mt-3 flex items-start gap-2 text-xs leading-relaxed text-muted">
            <ShieldCheck size={14} className="mt-0.5 shrink-0 text-emerald-600" />
            Coefficients describe statistical relationships learned by the model; they do not
            establish medical causation.
          </p>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Why Logistic Regression?"
          subtitle="Why HeartGuard AI chose this model as its single prediction model"
          icon={Sparkles}
        />
        <ul className="grid gap-2 px-5 py-4 sm:grid-cols-2">
          {WHY_POINTS.map((point) => (
            <li key={point} className="flex items-start gap-2 text-sm text-muted">
              <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-primary-600" />
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card>
        <CardHeader
          title="What Does the Model Look At?"
          subtitle="The 13 clinical input features used for every prediction"
          icon={ListChecks}
        />
        <div className="grid gap-2 px-5 py-4 sm:grid-cols-2 lg:grid-cols-3">
          {MODEL_FEATURES.map(({ n, label }) => (
            <div
              key={label}
              className="flex items-center gap-2.5 rounded-lg border border-slate-200 bg-slate-50/60 px-3 py-2.5"
            >
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-primary-50 text-xs font-bold text-primary-700">
                {n}
              </span>
              <span className="text-sm font-medium text-ink">{label}</span>
            </div>
          ))}
        </div>
        <p className="border-t border-slate-100 px-5 py-3 text-xs leading-relaxed text-muted">
          Categorical features are one-hot encoded and numerical features are scaled through the
          existing preprocessing pipeline before the model sees them.
        </p>
      </Card>

      <Card>
        <CardHeader
          title="Feature Coefficients"
          subtitle="How strongly each encoded feature contributes to the model's mathematical decision"
          icon={Coins}
        />
        <div className="px-5 py-4">
          <div className="space-y-2.5">
            {coefEntries.map(({ name, value }) => {
              const magnitude = Math.abs(value);
              const width = `${(magnitude / maxCoef) * 100}%`;
              return (
                <div key={name} className="flex items-center gap-3 text-xs">
                  <span className="w-36 shrink-0 truncate text-muted" title={name}>
                    {name}
                  </span>
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className="h-full rounded-full"
                      style={{ width, backgroundColor: "#0d9488" }}
                    />
                  </div>
                  <span className="w-24 shrink-0 text-right tabular-nums text-ink">
                    {value >= 0 ? "+" : "−"}
                    {magnitude.toFixed(3)}
                  </span>
                </div>
              );
            })}
          </div>
          <p className="mt-4 text-xs leading-relaxed text-muted">
            <span className="font-semibold text-ink">Statistical influence learned by the model.</span>{" "}
            Coefficient magnitude indicates the strength of the model&apos;s learned relationship after
            preprocessing. It does not establish causation — these are model weights, not medical
            risk factors.
          </p>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Model Performance"
          subtitle="Evaluation of the Logistic Regression model on real data — nothing hardcoded"
          icon={BarChart3}
        />
        <div className="grid gap-4 p-5 lg:grid-cols-2">
          <MetricTable
            title="5-fold Cross-Validation"
            subtitle="Mean over the training portion's 5 stratified folds"
            metrics={cvMetrics}
          />
          <MetricTable
            title="Final Test Set"
            subtitle="61 held-out rows, untouched during training"
            metrics={testMetrics}
          />
        </div>
        <p className="border-t border-slate-100 px-5 py-3 text-xs leading-relaxed text-muted">
          Cross-validation metrics and final test-set metrics are separate evaluations and are
          never mixed. Both are dataset evaluation metrics, not clinical guarantees.
        </p>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Precision · Recall · F1" subtitle="Logistic Regression on the test set" icon={BarChart3} />
          <div className="p-4">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={prfData} margin={{ top: 5, right: 10, bottom: 0, left: -15 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
                  <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
                  <Legend />
                  <Bar dataKey="value" name="Score" radius={[3, 3, 0, 0]}>
                    {prfData.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </Card>

        <Card>
          <CardHeader title="Accuracy & ROC-AUC" subtitle="Cross-validation vs final test set" icon={BarChart3} />
          <div className="space-y-5 p-4">
            <MetricBars
              data={[
                { key: "cv", shortName: "CV", value: cvMetrics.accuracy },
                { key: "test", shortName: "Test", value: testMetrics.accuracy },
              ]}
              metric="accuracy"
              label="Accuracy"
            />
            <MetricBars
              data={[
                { key: "cv", shortName: "CV", value: cvMetrics.roc_auc },
                { key: "test", shortName: "Test", value: testMetrics.roc_auc },
              ]}
              metric="roc_auc"
              label="ROC-AUC"
            />
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="ROC Curve"
          subtitle="True positive rate vs false positive rate"
          icon={LineIcon}
        />
        <div className="p-5">
          <div className="mb-3 flex items-center gap-2">
            <Badge tone="teal">ROC-AUC = {formatPercent(testMetrics.roc_auc)}</Badge>
            <span className="text-xs text-muted">Logistic Regression · final test set</span>
          </div>
          <RocCurve fpr={data.roc_curve.fpr} tpr={data.roc_curve.tpr} />
          <p className="mt-2 text-xs text-muted">
            The curve plots the true positive rate against the false positive rate at every decision
            threshold. The dashed diagonal is the performance of random guessing.
          </p>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Confusion Matrix"
          subtitle="Predicted vs actual on the held-out test set"
          icon={Sigma}
        />
        <div className="grid gap-6 p-5 lg:grid-cols-2">
          <ConfusionMatrix matrix={data.confusion_matrix} title="Logistic Regression · Test Set" />
          <div className="space-y-2.5 text-sm text-muted">
            {[
              { term: "True Positive", value: 30, text: "Correctly identified positive cases." },
              { term: "True Negative", value: 22, text: "Correctly identified negative cases." },
              { term: "False Positive", value: 6, text: "Negative case incorrectly classified as positive." },
              { term: "False Negative", value: 3, text: "Positive case incorrectly classified as negative." },
            ].map(({ term, value, text }) => (
              <p key={term} className="flex items-start gap-2">
                <span className="mt-0.5 shrink-0 rounded-md bg-slate-100 px-2 py-0.5 text-xs font-bold text-ink">
                  {value}
                </span>
                <span>
                  <span className="font-semibold text-ink">{term}:</span> {text}
                </span>
              </p>
            ))}
            <p className="border-t border-slate-100 pt-2 text-xs leading-relaxed">
              These values describe performance on the test dataset, not clinical outcomes.
            </p>
          </div>
        </div>
      </Card>

      <Card>
        <CardHeader
          title="Logistic Regression Assumptions & Considerations"
          subtitle="Statistical considerations, not absolute requirements"
          icon={Scale}
        />
        <ul className="grid gap-2 px-5 py-4 sm:grid-cols-2">
          {ASSUMPTIONS.map((point) => (
            <li key={point} className="flex items-start gap-2 text-sm text-muted">
              <CheckCircle2 size={16} className="mt-0.5 shrink-0 text-primary-600" />
              <span>{point}</span>
            </li>
          ))}
        </ul>
        <p className="border-t border-slate-100 px-5 py-3 text-xs leading-relaxed text-muted">
          Real-world clinical datasets may not perfectly satisfy every assumption, so model
          evaluation and validation remain important.
        </p>
      </Card>

      <Card>
        <CardHeader
          title="Where This Model Fits"
          subtitle="The role of Logistic Regression in this project"
          icon={GraduationCap}
        />
        <div className="space-y-3 px-5 py-4 text-sm leading-relaxed text-muted">
          <p>
            Logistic Regression is particularly useful for educational and tabular
            binary-classification applications where probability estimates and interpretability
            are important.
          </p>
          <p>
            HeartGuard AI uses it to demonstrate how machine learning can classify patterns
            associated with the heart-disease target in the provided dataset.
          </p>
          <p className="font-semibold text-ink">
            This is an educational ML demonstration, not a clinical diagnostic system.
          </p>
        </div>
      </Card>

      <Alert tone="warning">
        <strong>Educational ML demonstration — not a medical diagnosis.</strong>
        <span className="mt-1 block">
          HeartGuard AI is an educational machine-learning demonstration. Its predictions are not
          medical diagnoses and should not be used as a standalone basis for medical decisions.
          Consult a qualified healthcare professional for medical advice.
        </span>
      </Alert>
    </div>
  );
}
