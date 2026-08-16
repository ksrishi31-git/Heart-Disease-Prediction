import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ClipboardList, Eye, EyeOff, Trash2 } from "lucide-react";
import { Alert, Card, ConsensusBadge, EmptyState, Spinner } from "../components/UI.jsx";
import { predictionsApi } from "../services/predictions.js";
import { errorMessage } from "../services/api.js";
import { formatDateTime, formatPercent } from "../utils/format.js";
import { FEATURES } from "../utils/validation.js";

const LABELS = Object.fromEntries(FEATURES.map((f) => [f.name, f.label]));

function FeatureRows({ input }) {
  return (
    <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1.5 sm:grid-cols-3">
      {Object.entries(input).map(([key, value]) => (
        <div key={key} className="flex justify-between gap-2 text-sm">
          <dt className="text-muted">{LABELS[key] || key}</dt>
          <dd className="font-medium text-ink">{value}</dd>
        </div>
      ))}
    </dl>
  );
}

function DetailRow({ item, onDelete }) {
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  const toggle = async () => {
    if (open) { setOpen(false); return; }
    setOpen(true);
    if (!detail) {
      try {
        const { data } = await predictionsApi.get(item.prediction_id);
        setDetail(data);
      } catch (err) {
        setError(errorMessage(err));
      }
    }
  };

  const handleDelete = async () => {
    if (!window.confirm("Delete this prediction record? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await predictionsApi.remove(item.prediction_id);
      onDelete(item.prediction_id);
    } catch (err) {
      setError(errorMessage(err));
      setDeleting(false);
    }
  };

  return (
    <div className="border-b border-slate-100 last:border-0">
      <div className="grid grid-cols-2 items-center gap-3 px-5 py-3.5 text-sm sm:grid-cols-[1.4fr_1fr_1fr_1fr_auto]">
        <span className="text-muted">{formatDateTime(item.created_at)}</span>
        <span><ConsensusBadge consensus={item.consensus} /></span>
        <span className="font-medium text-ink">{item.best_model_name}</span>
        <span className="font-medium text-ink">{formatPercent(item.probability)}</span>
        <div className="col-span-2 flex gap-1 sm:col-span-1 sm:justify-end">
          <button
            onClick={toggle}
            className="flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-semibold text-primary-800 hover:bg-primary-50"
          >
            {open ? <EyeOff size={14} /> : <Eye size={14} />}
            {open ? "Hide" : "Details"}
          </button>
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="flex items-center gap-1 rounded-md px-2 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50 disabled:opacity-50"
          >
            <Trash2 size={14} />
            {deleting ? "…" : "Delete"}
          </button>
        </div>
      </div>

      {open && (
        <div className="bg-slate-50/60 px-5 py-4">
          {error && <Alert tone="error" className="mb-3">{error}</Alert>}
          {detail ? (
            <div className="space-y-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">Prediction</p>
                <p className="text-sm font-semibold text-ink">{detail.classification}</p>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <p className="text-xs text-muted">Model</p>
                  <p className="text-sm font-semibold text-ink">
                    {detail.model?.model_name || detail.best_model_name || "Logistic Regression"}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted">Model-estimated probability</p>
                  <p className="text-sm font-semibold text-ink">{formatPercent(detail.probability)}</p>
                </div>
                <div>
                  <p className="text-xs text-muted">Model version</p>
                  <p className="text-sm font-semibold text-ink">{detail.model_version}</p>
                </div>
              </div>
              <FeatureRows input={detail.input_features} />
            </div>
          ) : (
            <Spinner label="Loading details…" className="py-4" />
          )}
        </div>
      )}
    </div>
  );
}

export default function History() {
  const [items, setItems] = useState([]);
  const [filter, setFilter] = useState("all");
  const [sort, setSort] = useState("desc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await predictionsApi.list({ limit: 100 });
      setItems(data.items);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const visible = items
    .filter((item) => filter === "all" || item.consensus === filter)
    .sort((a, b) => {
      const diff = new Date(a.created_at) - new Date(b.created_at);
      return sort === "desc" ? -diff : diff;
    });

  const handleDelete = (id) => setItems((list) => list.filter((item) => item.prediction_id !== id));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-ink">Prediction History</h1>
          <p className="mt-1 text-sm text-muted">
            Your previous predictions — full details are decrypted server-side only for you.
          </p>
        </div>
        <Link to="/predict" className="rounded-lg bg-primary-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-primary-800">
          New Prediction
        </Link>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-sm text-muted">
          Filter
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-ink"
          >
            <option value="all">All results</option>
            <option value="Positive">Positive</option>
            <option value="Negative">Negative</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-muted">
          Sort
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-ink"
          >
            <option value="desc">Newest first</option>
            <option value="asc">Oldest first</option>
          </select>
        </label>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      <Card>
        {loading ? (
          <Spinner label="Loading predictions…" />
        ) : visible.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title={items.length === 0 ? "No predictions yet" : "Nothing matches the filter"}
            description={items.length === 0 ? "Run your first prediction to start your history." : "Try a different filter."}
          />
        ) : (
          <>
            <div className="hidden grid-cols-[1.4fr_1fr_1fr_1fr_auto] gap-3 border-b border-slate-200 bg-slate-50/60 px-5 py-2.5 text-xs font-semibold uppercase tracking-wide text-muted sm:grid">
              <span>Date</span>
              <span>Prediction</span>
              <span>Model</span>
              <span>Probability</span>
              <span className="text-right">Actions</span>
            </div>
            {visible.map((item) => (
              <DetailRow key={item.prediction_id} item={item} onDelete={handleDelete} />
            ))}
          </>
        )}
      </Card>
    </div>
  );
}
