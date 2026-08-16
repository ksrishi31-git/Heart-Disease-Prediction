import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const MODEL_COLORS = {
  logistic_regression: "#0d9488",
};

export const MODEL_COLORS_BY_KEY = MODEL_COLORS;

export function ConfusionMatrix({ matrix, title = "Confusion Matrix" }) {
  const [tn, fp] = matrix[0];
  const [fn, tp] = matrix[1];
  const cells = [
    { label: "True Negative", value: tn, row: 0, col: 0 },
    { label: "False Positive", value: fp, row: 0, col: 1 },
    { label: "False Negative", value: fn, row: 1, col: 0 },
    { label: "True Positive", value: tp, row: 1, col: 1 },
  ];
  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>
      <div className="grid grid-cols-2 gap-1.5 text-center">
        <div className="rounded-md bg-emerald-50 p-2.5">
          <p className="text-lg font-bold text-emerald-700">{tn}</p>
          <p className="text-[11px] text-emerald-700/70">TN — no disease</p>
        </div>
        <div className="rounded-md bg-amber-50 p-2.5">
          <p className="text-lg font-bold text-amber-700">{fp}</p>
          <p className="text-[11px] text-amber-700/70">FP — false alarm</p>
        </div>
        <div className="rounded-md bg-rose-50 p-2.5">
          <p className="text-lg font-bold text-rose-700">{fn}</p>
          <p className="text-[11px] text-rose-700/70">FN — missed</p>
        </div>
        <div className="rounded-md bg-teal-50 p-2.5">
          <p className="text-lg font-bold text-teal-700">{tp}</p>
          <p className="text-[11px] text-teal-700/70">TP — detected</p>
        </div>
      </div>
      <p className="mt-2 text-[11px] text-muted">
        Test set: 61 rows. Predicted vs actual heart disease.
      </p>
    </div>
  );
}

export function RocCurve({ fpr, tpr, color = "#0d9488", title }) {
  const data = fpr.map((x, i) => ({ fpr: x, tpr: tpr[i] }));
  return (
    <div>
      {title && <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>}
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 10, bottom: 5, left: -15 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="fpr" type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
          <YAxis type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
          <Tooltip formatter={(value) => Number(value).toFixed(3)} />
          <Line type="monotone" dataKey="tpr" stroke={color} strokeWidth={2} dot={false} name="TPR" />
          <Line
            type="monotone"
            data={[{ fpr: 0, tpr: 0 }, { fpr: 1, tpr: 1 }]}
            dataKey="tpr"
            stroke="#cbd5e1"
            strokeDasharray="4 4"
            strokeWidth={1}
            dot={false}
            name="Random"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export function MetricBars({ data, metric, label }) {
  const rows = data.map((d) => ({ name: d.shortName, value: d[metric], key: d.key }));
  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={rows} margin={{ top: 5, right: 10, bottom: 5, left: -15 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="name" />
        <YAxis domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
        <Tooltip formatter={(value) => `${(value * 100).toFixed(1)}%`} />
        <Bar dataKey="value" name={label} radius={[4, 4, 0, 0]}>
          {rows.map((row) => (
            <Cell key={row.key} fill={MODEL_COLORS[row.key] || "#0d9488"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
