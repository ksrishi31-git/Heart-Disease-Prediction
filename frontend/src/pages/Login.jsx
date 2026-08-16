import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Alert } from "../components/UI.jsx";
import { Field, SubmitButton, TextInput } from "../components/FormControls.jsx";
import AuthLayout from "../layouts/AuthLayout.jsx";
import { useAuth } from "../hooks/useAuth.jsx";
import { errorMessage } from "../services/api.js";
import { validateEmail } from "../utils/validation.js";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const nextErrors = {};
    const emailError = validateEmail(email);
    if (emailError) nextErrors.email = emailError;
    if (!password) nextErrors.password = "Password is required.";
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setLoading(true);
    setServerError("");
    try {
      await login(email, password);
      navigate(location.state?.from || "/dashboard", { replace: true });
    } catch (error) {
      setServerError(errorMessage(error, "Incorrect email or password."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue to your dashboard.">
      {serverError && <Alert tone="error" className="mb-4">{serverError}</Alert>}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Field label="Email" htmlFor="email" error={errors.email}>
          <TextInput
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={email}
            error={errors.email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </Field>
        <Field label="Password" htmlFor="password" error={errors.password}>
          <TextInput
            id="password"
            type="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            error={errors.password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </Field>
        <SubmitButton loading={loading} className="w-full">
          {loading ? "Logging in…" : "Log in"}
        </SubmitButton>
      </form>
      <p className="mt-5 text-center text-sm text-muted">
        Don't have an account?{" "}
        <Link to="/register" className="font-semibold text-primary-800 hover:underline">
          Register
        </Link>
      </p>
    </AuthLayout>
  );
}
