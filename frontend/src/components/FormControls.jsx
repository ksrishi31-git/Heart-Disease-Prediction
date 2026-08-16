export function Field({ label, helper, error, children, htmlFor }) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {helper && !error && <p className="text-xs text-muted">{helper}</p>}
      {error && <p className="text-xs font-medium text-rose-600" role="alert">{error}</p>}
    </div>
  );
}

const controlClasses =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-ink placeholder:text-slate-400 focus:border-primary-600 focus:outline-none focus:ring-1 focus:ring-primary-600 disabled:opacity-60";

export function TextInput({ error, className = "", ...rest }) {
  return <input className={`${controlClasses} ${error ? "border-rose-400" : ""} ${className}`} {...rest} />;
}

export function SelectInput({ options = [], error, placeholder = "Select…", className = "", ...rest }) {
  return (
    <select className={`${controlClasses} ${error ? "border-rose-400" : ""} ${className}`} {...rest}>
      <option value="" disabled>
        {placeholder}
      </option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

export function RadioGroup({ options = [], name, value, onChange, inline = true, disabled = false, groupLabel = "" }) {
  return (
    <div role="radiogroup" aria-label={groupLabel} className={`flex gap-4 ${inline ? "flex-wrap" : "flex-col"}`}>
      {options.map((option) => {
        const checked = String(value) === String(option.value);
        return (
          <label
            key={option.value}
            className={`flex cursor-pointer items-center gap-2 rounded-lg border px-3 py-2 text-sm transition-colors ${
              checked
                ? "border-primary-600 bg-primary-50 text-primary-800"
                : "border-slate-300 bg-white text-ink hover:border-slate-400"
            } ${disabled ? "cursor-not-allowed opacity-60" : ""}`}
          >
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={checked}
              onChange={() => onChange(option.value)}
              disabled={disabled}
              aria-label={`${groupLabel}: ${option.label}`}
              className="h-4 w-4 accent-[var(--color-primary-700)]"
            />
            {option.label}
          </label>
        );
      })}
    </div>
  );
}

export function SubmitButton({ children, loading, disabled, className = "" }) {
  return (
    <button
      type="submit"
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center gap-2 rounded-lg bg-primary-700 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-800 disabled:cursor-not-allowed disabled:opacity-60 ${className}`}
    >
      {loading && (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
      )}
      {children}
    </button>
  );
}
