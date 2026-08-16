import { AlertTriangle, CheckCircle2, Info, Loader2 } from "lucide-react";

export function Card({ className = "", children, ...rest }) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`} {...rest}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, icon: Icon, action }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-slate-100 px-5 py-4">
      <div className="flex items-start gap-3">
        {Icon && (
          <span className="mt-0.5 rounded-lg bg-primary-50 p-2 text-primary-700">
            <Icon size={18} />
          </span>
        )}
        <div>
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
          {subtitle && <p className="mt-0.5 text-xs text-muted">{subtitle}</p>}
        </div>
      </div>
      {action}
    </div>
  );
}

export function Badge({ tone = "slate", children, className = "" }) {
  const tones = {
    slate: "bg-slate-100 text-slate-700",
    green: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
    red: "bg-rose-50 text-rose-700 ring-1 ring-rose-200",
    amber: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
    teal: "bg-primary-50 text-primary-800 ring-1 ring-primary-200",
  };
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]} ${className}`}>
      {children}
    </span>
  );
}

export function ConsensusBadge({ consensus }) {
  if (consensus === "Positive") return <Badge tone="red">Positive</Badge>;
  return <Badge tone="green">Negative</Badge>;
}

export function Spinner({ label = "Loading…", className = "" }) {
  return (
    <div className={`flex items-center justify-center gap-2 py-8 text-sm text-muted ${className}`}>
      <Loader2 size={18} className="animate-spin text-primary-700" />
      {label}
    </div>
  );
}

export function Alert({ tone = "info", children, className = "" }) {
  const tones = {
    info: "border-sky-200 bg-sky-50 text-sky-900",
    warning: "border-amber-200 bg-amber-50 text-amber-900",
    error: "border-rose-200 bg-rose-50 text-rose-900",
    success: "border-emerald-200 bg-emerald-50 text-emerald-900",
  };
  const icons = {
    info: <Info size={16} className="mt-0.5 shrink-0" />,
    warning: <AlertTriangle size={16} className="mt-0.5 shrink-0" />,
    error: <AlertTriangle size={16} className="mt-0.5 shrink-0" />,
    success: <CheckCircle2 size={16} className="mt-0.5 shrink-0" />,
  };
  return (
    <div className={`flex gap-2.5 rounded-lg border p-3 text-sm leading-relaxed ${tones[tone]} ${className}`}>
      {icons[tone]}
      <div>{children}</div>
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12 text-center">
      {Icon && <Icon size={32} className="text-slate-300" />}
      <p className="text-sm font-medium text-ink">{title}</p>
      {description && <p className="max-w-sm text-xs text-muted">{description}</p>}
    </div>
  );
}
