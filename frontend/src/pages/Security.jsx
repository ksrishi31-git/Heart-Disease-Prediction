import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { KeyRound, LogOut, MonitorSmartphone, ShieldCheck, Trash2, UserRound } from "lucide-react";
import { Alert, Card, CardHeader, EmptyState, Spinner } from "../components/UI.jsx";
import { Field, SubmitButton, TextInput } from "../components/FormControls.jsx";
import { useAuth } from "../hooks/useAuth.jsx";
import { authApi } from "../services/auth.js";
import { errorMessage } from "../services/api.js";
import { validatePassword } from "../utils/validation.js";
import { formatDateTime } from "../utils/format.js";

export default function Security() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState(null);
  const [passwordForm, setPasswordForm] = useState({ old: "", next: "", confirm: "" });
  const [passwordErrors, setPasswordErrors] = useState({});
  const [passwordMessage, setPasswordMessage] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const loadSessions = useCallback(async () => {
    try {
      const { data } = await authApi.listSessions();
      setSessions(data);
    } catch {
      setSessions([]);
    }
  }, []);

  useEffect(() => { loadSessions(); }, [loadSessions]);

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    const errors = {};
    const passwordErrorMsg = validatePassword(passwordForm.next, passwordForm.confirm);
    if (!passwordForm.old) errors.old = "Current password is required.";
    if (passwordErrorMsg) errors.next = passwordErrorMsg;
    setPasswordErrors(errors);
    if (Object.keys(errors).length > 0) return;

    setSaving(true);
    setPasswordMessage("");
    setPasswordError("");
    try {
      const { data } = await authApi.changePassword({
        old_password: passwordForm.old,
        new_password: passwordForm.next,
      });
      setPasswordMessage(data.message);
      setPasswordForm({ old: "", next: "", confirm: "" });
      await loadSessions();
    } catch (error) {
      setPasswordError(errorMessage(error));
    } finally {
      setSaving(false);
    }
  };

  const handleRevokeSession = async (id) => {
    try {
      await authApi.revokeSession(id);
      await loadSessions();
    } catch (error) {
      setPasswordError(errorMessage(error));
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm(
      "Delete your account permanently? All your prediction records will be deleted. This cannot be undone.",
    )) return;
    setDeleting(true);
    try {
      await authApi.deleteAccount();
      await logout();
      navigate("/");
    } catch (error) {
      setPasswordError(errorMessage(error));
      setDeleting(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">Security & Profile</h1>
        <p className="mt-1 text-sm text-muted">
          Manage your account, password and active sessions.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Profile" subtitle="Your account information" icon={UserRound} />
          <div className="space-y-3 p-5">
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-700 text-lg font-bold text-white">
                {(user?.name || "?").charAt(0).toUpperCase()}
              </span>
              <div>
                <p className="font-semibold text-ink">{user?.name}</p>
                <p className="text-sm text-muted">{user?.email}</p>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 pt-2 text-sm">
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-muted">Member since</p>
                <p className="font-medium text-ink">{formatDateTime(user?.created_at)}</p>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <p className="text-xs text-muted">Account status</p>
                <p className="font-medium text-emerald-600">Active</p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex w-full items-center justify-center gap-2 rounded-lg border border-slate-200 px-4 py-2.5 text-sm font-semibold text-muted transition-colors hover:border-rose-200 hover:bg-rose-50 hover:text-rose-600"
            >
              <LogOut size={16} />
              Log out
            </button>
          </div>
        </Card>

        <Card>
          <CardHeader title="Change password" subtitle="Argon2id hashed · revokes other sessions" icon={KeyRound} />
          <div className="p-5">
            {passwordMessage && <Alert tone="success" className="mb-4">{passwordMessage}</Alert>}
            {passwordError && <Alert tone="error" className="mb-4">{passwordError}</Alert>}
            <form onSubmit={handlePasswordChange} className="space-y-4" noValidate>
              <Field label="Current password" error={passwordErrors.old} htmlFor="old">
                <TextInput id="old" type="password" autoComplete="current-password" value={passwordForm.old} error={passwordErrors.old} onChange={(e) => setPasswordForm((f) => ({ ...f, old: e.target.value }))} />
              </Field>
              <Field
                label="New password"
                error={passwordErrors.next}
                helper="At least 8 characters with uppercase, lowercase and a digit."
                htmlFor="next"
              >
                <TextInput id="next" type="password" autoComplete="new-password" value={passwordForm.next} error={passwordErrors.next} onChange={(e) => setPasswordForm((f) => ({ ...f, next: e.target.value }))} />
              </Field>
              <Field label="Confirm new password" htmlFor="confirm">
                <TextInput id="confirm" type="password" autoComplete="new-password" value={passwordForm.confirm} onChange={(e) => setPasswordForm((f) => ({ ...f, confirm: e.target.value }))} />
              </Field>
              <SubmitButton loading={saving}>Update password</SubmitButton>
            </form>
          </div>
        </Card>

        <Card>
          <CardHeader title="Active sessions" subtitle="Devices with a valid refresh token" icon={MonitorSmartphone} />
          <div className="p-5">
            {sessions === null ? (
              <Spinner label="Loading sessions…" className="py-4" />
            ) : sessions.length === 0 ? (
              <EmptyState icon={MonitorSmartphone} title="No sessions" description="Log in from a new device to create a session." />
            ) : (
              <ul className="space-y-2">
                {sessions.map((session) => (
                  <li key={session.id} className="flex items-center justify-between gap-3 rounded-lg border border-slate-200 px-3 py-2.5 text-sm">
                    <div className="min-w-0">
                      <p className="font-medium text-ink">Session #{session.id}</p>
                      <p className="truncate text-xs text-muted">
                        Created {formatDateTime(session.created_at)} · expires {formatDateTime(session.expires_at)}
                        {session.revoked ? " · revoked" : " · active"}
                      </p>
                    </div>
                    {!session.revoked && (
                      <button
                        onClick={() => handleRevokeSession(session.id)}
                        className="shrink-0 rounded-md px-2.5 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50"
                      >
                        Revoke
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>

        <Card className="border-rose-200">
          <CardHeader title="Privacy & data deletion" subtitle="Right to deletion" icon={ShieldCheck} />
          <div className="p-5">
            <p className="text-sm leading-relaxed text-muted">
              Deleting your account permanently removes your profile and all stored
              (encrypted) prediction records, in line with the data-minimisation and
              retention principles described in the documentation.
            </p>
            <button
              onClick={handleDeleteAccount}
              disabled={deleting}
              className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg border border-rose-300 bg-white px-4 py-2.5 text-sm font-semibold text-rose-600 transition-colors hover:bg-rose-50 disabled:opacity-60"
            >
              <Trash2 size={16} />
              {deleting ? "Deleting account…" : "Delete my account"}
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
}
