import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  ArrowRight,
  HeartPulse,
  PieChart as PieIcon,
  ShieldCheck,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";
import {
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import StatCard from "../components/StatCard.jsx";
import { Alert, Card, CardHeader, ConsensusBadge, EmptyState, Spinner } from "../components/UI.jsx";
import { modelsApi, predictionsApi } from "../services/predictions.js";
import { errorMessage } from "../services/api.js";
import { formatPercent, formatDateTime } from "../utils/format.js";

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [insights, setInsights] = useState(null);
  const [recent, setRecent] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [statsRes, insightsRes, recentRes] = await Promise.all([
          predictionsApi.stats(),
          modelsApi.insights(),
          predictionsApi.list({ limit: 12 }),
        ]);
        setStats(statsRes.data);
        setInsights(insightsRes.data);
        setRecent(recentRes.data.items);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <Spinner label="Loading dashboard…" />;
  if (error) return <Alert tone="error">{error}</Alert>;
  if (!stats || !insights) return null;

  const distData = [
    { name: "Positive", value: stats.positive, color: "#dc2626" },
    { name: "Negative", value: stats.negative, color: "#059669" },
  ];
  const trendData = (recent || []).slice().reverse().map((item, i) => ({
    name: `#${i + 1}`,
    probability: item.probability * 100,
  }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">Dashboard</h1>
          <p className="mt-1 text-sm text-muted">
            Your prediction activity and HeartGuard AI&apos;s Logistic Regression model.
          </p>
        </div>
        <Link
          to="/predict"
          className="flex items-center gap-2 rounded-lg bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800"
        >
          <HeartPulse size={16} />
          New Prediction
        </Link>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard icon={Activity} label="Total predictions" value={stats.total_predictions} tone="teal" />
        <StatCard
          icon={ThumbsUp}
          label="Positive classifications"
          value={stats.positive}
          sub="presence of the target condition"
          tone="red"
        />
        <StatCard
          icon={ThumbsDown}
          label="Negative classifications"
          value={stats.negative}
          sub="absence of the target condition"
          tone="green"
        />
        <StatCard
          icon={Sparkles}
          label="Model in use"
          value={insights.model.name}
          sub={`ROC-AUC ${formatPercent(insights.test_metrics.roc_auc)} · Primary prediction model`}
          tone="blue"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Prediction distribution" subtitle="Your predictions by unified result" icon={PieIcon} />
          <div className="p-4">
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={distData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={3}>
                  {distData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader title="Recent prediction trend" subtitle="Model-estimated probability per prediction" icon={Activity} />
          <div className="p-4">
            {trendData.length === 0 ? (
              <EmptyState icon={Activity} title="No predictions yet" description="Run your first prediction to see the trend." />
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={trendData} margin={{ top: 5, right: 10, bottom: 0, left: -15 }}>
                  <XAxis dataKey="name" />
                  <YAxis domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                  <Tooltip formatter={(v) => `${v.toFixed(1)}%`} />
                  <Line type="monotone" dataKey="probability" name="Probability" stroke="#0d9488" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Latest prediction"
          subtitle={stats.latest ? formatDateTime(stats.latest.created_at) : "No predictions yet"}
          icon={HeartPulse}
          action={
            stats.latest && (
              <Link to="/history" className="flex items-center gap-1 text-xs font-semibold text-primary-800 hover:underline">
                View history <ArrowRight size={13} />
              </Link>
            )
          }
        />
        {stats.latest ? (
          <div className="flex flex-wrap items-center gap-x-6 gap-y-3 px-5 py-4">
            <ConsensusBadge consensus={stats.latest.consensus} />
            <div>
              <p className="text-xs text-muted">Model</p>
              <p className="text-sm font-semibold text-ink">{stats.latest.best_model_name}</p>
            </div>
            <div>
              <p className="text-xs text-muted">Model-estimated probability</p>
              <p className="text-sm font-semibold text-ink">{formatPercent(stats.latest.probability)}</p>
            </div>
            <ShieldCheck size={16} className="text-emerald-600" />
            <span className="text-xs text-muted">Educational ML demonstration — not a medical diagnosis.</span>
          </div>
        ) : (
          <div className="px-5 py-4">
            <p className="text-sm text-muted">
              No predictions yet.{" "}
              <Link to="/predict" className="font-semibold text-primary-800 hover:underline">
                Create your first prediction
              </Link>
              .
            </p>
          </div>
        )}
      </Card>
    </div>
  );
}
