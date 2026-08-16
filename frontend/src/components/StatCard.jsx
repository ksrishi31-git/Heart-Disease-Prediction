export default function StatCard({ icon: Icon, label, value, sub, tone = "teal" }) {
  const tones = {
    teal: "bg-primary-50 text-primary-700",
    red: "bg-rose-50 text-rose-600",
    green: "bg-emerald-50 text-emerald-600",
    blue: "bg-sky-50 text-sky-700",
    amber: "bg-amber-50 text-amber-600",
    slate: "bg-slate-100 text-slate-600",
  };
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <span className={`rounded-lg p-2.5 ${tones[tone]}`}>
          <Icon size={20} />
        </span>
        <div className="min-w-0">
          <p className="truncate text-xs font-medium uppercase tracking-wide text-muted">{label}</p>
          <p className="truncate text-xl font-bold text-ink">{value}</p>
          {sub && <p className="truncate text-xs text-muted">{sub}</p>}
        </div>
      </div>
    </div>
  );
}
