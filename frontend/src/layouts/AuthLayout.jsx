import { HeartPulse } from "lucide-react";
import { Link } from "react-router-dom";

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <Link to="/" className="inline-flex items-center gap-2">
            <span className="rounded-xl bg-primary-700 p-2.5 text-white">
              <HeartPulse size={24} />
            </span>
            <span className="text-xl font-bold tracking-tight text-ink">
              HeartGuard <span className="text-primary-700">AI</span>
            </span>
          </Link>
          <h1 className="mt-5 text-2xl font-bold text-ink">{title}</h1>
          {subtitle && <p className="mt-1.5 text-sm text-muted">{subtitle}</p>}
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
          {children}
        </div>
      </div>
    </div>
  );
}
