import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  Brain,
  ClipboardList,
  Database,
  Gauge,
  HeartPulse,
  Lock,
  Menu,
  ShieldCheck,
  X,
  Zap,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth.jsx";
import { modelsApi } from "../services/predictions.js";
import { formatPercent } from "../utils/format.js";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/predict", label: "Predict" },
  { to: "/history", label: "History" },
  { to: "/model-insights", label: "Model Insights" },
  { to: "/security", label: "Security" },
];

const FEATURES = [
  {
    n: "01",
    icon: ClipboardList,
    title: "Simple Input",
    text: "Enter key health and clinical parameters through a clear, guided interface.",
  },
  {
    n: "02",
    icon: Brain,
    title: "Machine Learning",
    text: "HeartGuard AI uses Logistic Regression to analyse patterns in the provided data.",
  },
  {
    n: "03",
    icon: Zap,
    title: "Instant Insights",
    text: "Receive a straightforward prediction and model-estimated probability.",
  },
  {
    n: "04",
    icon: ShieldCheck,
    title: "Privacy & Security",
    text: "Sensitive prediction data is protected using the application's existing security architecture.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Enter Your Information",
    text: "Provide the required health and clinical parameters through a guided form.",
  },
  {
    n: "02",
    title: "Analyse",
    text: "The Logistic Regression model processes the submitted information.",
  },
  {
    n: "03",
    title: "View Your Result",
    text: "Receive a clear model prediction with supporting performance information.",
  },
];

const SECURITY_POINTS = [
  {
    icon: Lock,
    title: "Encrypted Data",
    text: "Patient inputs and results are encrypted with AES-256-GCM before storage.",
  },
  {
    icon: ShieldCheck,
    title: "Secure Authentication",
    text: "Argon2id password hashing with HttpOnly JWT cookies and refresh-token rotation.",
  },
  {
    icon: Gauge,
    title: "Protected API Access",
    text: "Rate limiting and per-user authorization guard every request.",
  },
  {
    icon: Database,
    title: "Secure Data Storage",
    text: "The trained model file is stored encrypted and decrypted only in memory.",
  },
];

const METRIC_CARDS = [
  { key: "accuracy", label: "Accuracy" },
  { key: "sensitivity", label: "Sensitivity" },
  { key: "specificity", label: "Specificity" },
  { key: "roc_auc", label: "ROC-AUC" },
];

const DEMO_METRICS = [
  { label: "Resting BP", value: "128 mm Hg" },
  { label: "Max HR", value: "172 bpm" },
  { label: "Cholesterol", value: "214 mg/dl" },
  { label: "Age", value: "54 yrs" },
];

function Logo() {
  return (
    <Link to="/" className="flex items-center gap-2" aria-label="HeartGuard AI home">
      <span className="rounded-lg bg-primary-700 p-1.5 text-white">
        <HeartPulse size={20} />
      </span>
      <span className="text-lg font-bold tracking-tight text-ink">
        HeartGuard <span className="text-primary-700">AI</span>
      </span>
    </Link>
  );
}

function Header() {
  const { user, loading } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Logo />

        <div className="flex items-center gap-2">
          {loading ? (
            <div className="h-9 w-28 animate-pulse rounded-lg bg-slate-100" aria-hidden="true" />
          ) : user ? (
            <>
              <Link
                to="/dashboard"
                className="hidden rounded-lg px-3.5 py-2 text-sm font-semibold text-primary-800 transition-colors hover:bg-primary-50 sm:inline-flex"
              >
                Dashboard
              </Link>
              <Link
                to="/predict"
                className="inline-flex rounded-lg bg-primary-700 px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-800"
              >
                Start a Prediction
              </Link>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="hidden rounded-lg px-3.5 py-2 text-sm font-semibold text-primary-800 transition-colors hover:bg-primary-50 sm:inline-flex"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="inline-flex rounded-lg bg-primary-700 px-3.5 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-800"
              >
                Get Started
              </Link>
            </>
          )}
          <button
            className="rounded-lg p-2 text-muted transition-colors hover:bg-slate-100 lg:hidden"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={menuOpen}
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      {menuOpen && (
        <nav className="border-t border-slate-100 bg-white px-4 py-2 sm:px-6 lg:hidden" aria-label="Mobile">
          {!loading && (
            <div className="flex flex-col gap-1 pb-2">
              {user ? (
                <>
                  <Link
                    to="/dashboard"
                    onClick={() => setMenuOpen(false)}
                    className="rounded-lg px-3 py-2.5 text-sm font-medium text-primary-800 hover:bg-primary-50"
                  >
                    Dashboard
                  </Link>
                  <Link
                    to="/predict"
                    onClick={() => setMenuOpen(false)}
                    className="rounded-lg bg-primary-700 px-3 py-2.5 text-center text-sm font-semibold text-white hover:bg-primary-800"
                  >
                    Start a Prediction
                  </Link>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    onClick={() => setMenuOpen(false)}
                    className="rounded-lg px-3 py-2.5 text-sm font-medium text-primary-800 hover:bg-primary-50"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setMenuOpen(false)}
                    className="rounded-lg bg-primary-700 px-3 py-2.5 text-center text-sm font-semibold text-white hover:bg-primary-800"
                  >
                    Get Started
                  </Link>
                </>
              )}
            </div>
          )}
        </nav>
      )}
    </header>
  );
}

function HeroVisual() {
  const radius = 74;
  const circumference = 2 * Math.PI * radius;
  const risk = 0.38;

  return (
    <div className="relative mx-auto w-full max-w-md lg:max-w-none">
      <div
        className="absolute -inset-4 rounded-[2.5rem] bg-gradient-to-br from-primary-100/70 via-primary-50/40 to-transparent blur-2xl"
        aria-hidden="true"
      />
      <div className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-medium text-muted">Risk Assessment</p>
            <p className="mt-0.5 text-sm font-semibold text-ink">Heart health profile</p>
          </div>
          <span className="rounded-full bg-primary-50 px-2.5 py-1 text-[11px] font-semibold text-primary-800 ring-1 ring-primary-200">
            Logistic Regression
          </span>
        </div>

        <div className="relative mx-auto mt-6 flex h-44 w-44 items-center justify-center">
          <svg width="176" height="176" viewBox="0 0 176 176" className="-rotate-90" aria-hidden="true">
            <circle cx="88" cy="88" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="12" />
            <circle
              cx="88"
              cy="88"
              r={radius}
              fill="none"
              stroke="#059669"
              strokeWidth="12"
              strokeLinecap="round"
              strokeDasharray={`${circumference * risk} ${circumference}`}
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <span className="text-3xl font-bold tabular-nums text-ink">38%</span>
            <span className="text-xs font-medium text-emerald-600">Low risk</span>
          </div>
        </div>

        <div className="mt-6 grid grid-cols-2 gap-2">
          {DEMO_METRICS.map(({ label, value }) => (
            <div key={label} className="rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2">
              <p className="text-[11px] text-muted">{label}</p>
              <p className="text-sm font-semibold tabular-nums text-ink">{value}</p>
            </div>
          ))}
        </div>

        <div className="mt-5 flex items-center justify-center gap-1.5 border-t border-slate-100 pt-4 text-[11px] text-muted">
          <Activity size={13} className="text-primary-600" />
          Illustrative assessment — not based on your data
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  const { user, loading } = useAuth();
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    let cancelled = false;
    modelsApi
      .insights()
      .then(({ data }) => {
        if (!cancelled) setMetrics(data.test_metrics);
      })
      .catch(() => {
        /* metrics section is optional — hide it if unavailable */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const authed = !loading && Boolean(user);

  return (
    <div className="min-h-screen bg-surface">
      <Header />

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-7xl px-4 pt-16 pb-20 sm:px-6 sm:pt-20 sm:pb-24 lg:px-8 lg:pt-28 lg:pb-32">
          <div className="grid items-center gap-14 lg:grid-cols-2 lg:gap-16">
            <div className="animate-fade-up max-w-xl">
              <span
                className="inline-flex animate-fade-up items-center gap-2 rounded-full border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary-800"
                style={{ animationDelay: "40ms" }}
              >
                <Activity size={13} />
                AI-Powered Health Insights
              </span>
              <h1
                className="mt-6 animate-fade-up text-4xl font-extrabold leading-[1.08] tracking-tight text-ink sm:text-5xl lg:text-[3.4rem]"
                style={{ animationDelay: "110ms" }}
              >
                Understand Your Heart Health{" "}
                <span className="text-primary-700">with Intelligent Risk Insights</span>
              </h1>
              <p
                className="mt-6 animate-fade-up text-base leading-relaxed text-muted sm:text-lg"
                style={{ animationDelay: "180ms" }}
              >
                HeartGuard AI uses a machine-learning model to analyse key health parameters and
                provide an easy-to-understand risk prediction in seconds.
              </p>
              <div
                className="mt-8 flex animate-fade-up flex-wrap items-center gap-3"
                style={{ animationDelay: "250ms" }}
              >
                <Link
                  to={authed ? "/predict" : "/register"}
                  className="inline-flex items-center gap-2 rounded-lg bg-primary-700 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors duration-200 hover:bg-primary-800"
                >
                  {authed ? "Start a Prediction" : "Get Started"}
                  <ArrowRight size={16} />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-ink transition-colors duration-200 hover:border-slate-400 hover:bg-slate-50"
                >
                  Explore How It Works
                </a>
              </div>
              <p
                className="mt-6 flex animate-fade-up items-start gap-2 text-xs leading-relaxed text-muted"
                style={{ animationDelay: "320ms" }}
              >
                <ShieldCheck size={14} className="mt-0.5 shrink-0 text-primary-600" />
                Educational machine-learning tool. Predictions are not medical diagnoses and should
                not replace professional medical advice.
              </p>
            </div>

            <div className="animate-fade-up" style={{ animationDelay: "160ms" }}>
              <HeroVisual />
            </div>
          </div>
        </div>
      </section>

      {/* Product value */}
      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
              Built for Clearer Health Insights
            </h2>
            <p className="mt-4 text-base leading-relaxed text-muted sm:text-lg">
              A focused, transparent way to turn structured health information into an
              understandable prediction.
            </p>
          </div>
          <div className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map(({ n, icon: Icon, title, text }) => (
              <div
                key={n}
                className="group rounded-xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <span className="inline-flex rounded-lg bg-primary-50 p-2.5 text-primary-700">
                    <Icon size={20} />
                  </span>
                  <span className="text-xs font-bold tracking-widest text-slate-300">{n}</span>
                </div>
                <h3 className="mt-4 text-base font-semibold text-ink">{title}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="scroll-mt-24">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
              How HeartGuard AI Works
            </h2>
            <p className="mt-4 text-base leading-relaxed text-muted sm:text-lg">
              Three simple steps from information to insight.
            </p>
          </div>
          <div className="relative mx-auto mt-14 grid max-w-4xl gap-10 md:grid-cols-3 md:gap-8">
            <div
              className="absolute inset-x-0 top-6 z-0 hidden h-px bg-slate-200 md:block"
              aria-hidden="true"
            />
            {STEPS.map((step) => (
              <div key={step.n} className="relative z-10 flex flex-col items-center text-center">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-700 text-sm font-bold text-white shadow-sm">
                  {step.n}
                </span>
                <h3 className="mt-5 text-base font-semibold text-ink">{step.title}</h3>
                <p className="mt-2 max-w-xs text-sm leading-relaxed text-muted">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Model */}
      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
          <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
            <div>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-semibold text-primary-800">
                <Brain size={13} />
                Machine Learning
              </span>
              <h2 className="mt-5 text-3xl font-bold tracking-tight text-ink sm:text-4xl">
                Powered by Logistic Regression
              </h2>
              <p className="mt-4 max-w-xl text-base leading-relaxed text-muted">
                HeartGuard AI uses Logistic Regression, a widely used classification algorithm, to
                estimate the likelihood of the positive class from the health parameters provided.
              </p>
              <Link
                to="/model-insights"
                className="mt-8 inline-flex items-center gap-2 rounded-lg bg-primary-700 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors duration-200 hover:bg-primary-800"
              >
                Explore the Model
                <ArrowRight size={16} />
              </Link>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50/60 p-8 text-center sm:p-10">
              <p className="font-mono text-xl font-semibold text-ink sm:text-2xl">
                P(y = 1) = 1 / (1 + e<sup>−z</sup>)
              </p>
              <p className="mt-3 font-mono text-sm text-muted">
                z = β₀ + β₁x₁ + β₂x₂ + … + βₙxₙ
              </p>
              <p className="mx-auto mt-4 max-w-md text-xs leading-relaxed text-muted">
                The logistic function maps a weighted combination of the patient&apos;s features to
                a probability between 0 and 1.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Security */}
      <section>
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-[1fr_1.1fr] lg:gap-16">
            <div className="max-w-xl">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-primary-200 bg-primary-50 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary-800">
                <Lock size={13} />
                Privacy &amp; Security
              </span>
              <h2 className="mt-5 text-3xl font-bold tracking-tight text-ink sm:text-4xl">
                Designed With Privacy in Mind
              </h2>
              <p className="mt-4 text-base leading-relaxed text-muted">
                HeartGuard AI is designed with security-conscious handling of application data,
                authentication, encrypted storage, and protected client-server communication.
              </p>
              <p className="mt-3 text-sm leading-relaxed text-muted">
                Built on the application&apos;s existing security architecture.
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              {SECURITY_POINTS.map(({ icon: Icon, title, text }) => (
                <div
                  key={title}
                  className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary-200 hover:shadow-md"
                >
                  <span className="inline-flex rounded-lg bg-primary-50 p-2.5 text-primary-700">
                    <Icon size={20} />
                  </span>
                  <h3 className="mt-3 text-sm font-semibold text-ink">{title}</h3>
                  <p className="mt-1.5 text-xs leading-relaxed text-muted">{text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Model performance — real metrics from the API, never hardcoded */}
      {metrics && (
        <section className="border-y border-slate-200 bg-white">
          <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
                Model Performance
              </h2>
              <p className="mt-4 text-base leading-relaxed text-muted sm:text-lg">
                Real evaluation metrics computed from the model&apos;s held-out test dataset.
              </p>
            </div>
            <div className="mx-auto mt-14 grid max-w-4xl gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {METRIC_CARDS.map(({ key, label }) => (
                <div key={key} className="rounded-xl border border-slate-200 bg-surface p-6 text-center shadow-sm">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted">{label}</p>
                  <p className="mt-2 text-3xl font-bold tabular-nums text-ink">
                    {formatPercent(metrics[key])}
                  </p>
                </div>
              ))}
            </div>
            <p className="mx-auto mt-6 max-w-xl text-center text-xs leading-relaxed text-muted">
              Evaluation metrics from the model&apos;s held-out test dataset — dataset performance
              figures, not clinical accuracy.
            </p>
          </div>
        </section>
      )}

      {/* Final CTA */}
      <section>
        <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-24 lg:px-8">
          <div className="mx-auto max-w-3xl rounded-2xl border border-primary-100 bg-gradient-to-b from-primary-50/70 to-white px-6 py-14 text-center shadow-sm sm:px-12 sm:py-16">
            <h2 className="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
              Ready to Explore Your Health Insights?
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-base leading-relaxed text-muted">
              Explore HeartGuard AI and see how machine learning can turn structured health
              information into an understandable prediction.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/predict"
                className="inline-flex items-center gap-2 rounded-lg bg-primary-700 px-6 py-3 text-sm font-semibold text-white shadow-sm transition-colors duration-200 hover:bg-primary-800"
              >
                Start a Prediction
                <ArrowRight size={16} />
              </Link>
              <Link
                to="/model-insights"
                className="inline-flex items-center justify-center rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-ink transition-colors duration-200 hover:border-slate-400 hover:bg-slate-50"
              >
                Learn About the Model
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
          <div className="flex flex-col gap-10 md:flex-row md:items-start md:justify-between">
            <div className="max-w-xs">
              <Logo />
              <p className="mt-3 text-sm leading-relaxed text-muted">
                An educational machine-learning demonstration for heart-health prediction.
              </p>
            </div>
            <nav
              className="grid grid-cols-2 gap-x-12 gap-y-2.5 sm:grid-cols-3 md:grid-cols-2 lg:grid-cols-5"
              aria-label="Footer"
            >
              {NAV_ITEMS.map(({ to, label }) => (
                <Link
                  key={to}
                  to={to}
                  className="text-sm text-muted transition-colors hover:text-primary-800"
                >
                  {label}
                </Link>
              ))}
            </nav>
          </div>
          <div className="mt-10 border-t border-slate-100 pt-6">
            <p className="text-xs leading-relaxed text-muted">
              HeartGuard AI is an educational machine-learning system. Its predictions are not
              medical diagnoses and should not be used as a substitute for professional medical
              advice.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
