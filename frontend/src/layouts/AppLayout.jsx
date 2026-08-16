import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  Activity,
  BarChart3,
  ClipboardList,
  HeartPulse,
  History,
  LogOut,
  Menu,
  ShieldCheck,
  X,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth.jsx";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: Activity },
  { to: "/predict", label: "Predict", icon: HeartPulse },
  { to: "/history", label: "History", icon: History },
  { to: "/model-insights", label: "Model Insights", icon: BarChart3 },
  { to: "/security", label: "Security", icon: ShieldCheck },
];

function Logo() {
  return (
    <NavLink to="/dashboard" className="flex items-center gap-2">
      <span className="rounded-lg bg-primary-700 p-1.5 text-white">
        <HeartPulse size={20} />
      </span>
      <span className="text-base font-bold tracking-tight text-ink">
        HeartGuard <span className="text-primary-700">AI</span>
      </span>
    </NavLink>
  );
}

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const navClass = ({ isActive }) =>
    `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
      isActive
        ? "bg-primary-50 text-primary-800"
        : "text-muted hover:bg-slate-100 hover:text-ink"
    }`;

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo />
          <nav className="hidden items-center gap-1 lg:flex">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink key={to} to={to} className={navClass}>
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-muted sm:block">
              {user?.name}
            </span>
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-muted transition-colors hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
            >
              <LogOut size={15} />
              <span className="hidden sm:inline">Logout</span>
            </button>
            <button
              className="rounded-lg p-2 text-muted hover:bg-slate-100 lg:hidden"
              onClick={() => setMenuOpen((v) => !v)}
              aria-label="Toggle navigation menu"
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
        {menuOpen && (
          <nav className="border-t border-slate-100 bg-white px-4 py-2 lg:hidden">
            {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium ${
                    isActive ? "bg-primary-50 text-primary-800" : "text-muted"
                  }`
                }
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </nav>
        )}
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6 sm:px-6 sm:py-8">
        <Outlet />
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-4 py-4 text-center text-xs text-muted sm:px-6">
          <p className="flex items-center justify-center gap-1.5">
            <ClipboardList size={13} />
            HeartGuard AI is an educational machine-learning demonstration. Its
            predictions are <strong>not medical diagnoses</strong> — consult a
            qualified healthcare professional for medical advice.
          </p>
        </div>
      </footer>
    </div>
  );
}
