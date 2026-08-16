import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Alert } from "../components/UI.jsx";
import { Field, SubmitButton, TextInput } from "../components/FormControls.jsx";
import AuthLayout from "../layouts/AuthLayout.jsx";
import { useAuth } from "../hooks/useAuth.jsx";
import { errorMessage } from "../services/api.js";
import { validateEmail, validatePassword } from "../utils/validation.js";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirmPassword: "" });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    const nextErrors = {};
    if (form.name.trim().length < 2) nextErrors.name = "Name must be at least 2 characters long.";
    const emailError = validateEmail(form.email);
    if (emailError) nextErrors.email = emailError;
    const passwordError = validatePassword(form.password, form.confirmPassword);
    if (passwordError) nextErrors.password = passwordError;
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setLoading(true);
    setServerError("");
    try {
      await register({
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
        confirm_password: form.confirmPassword,
      });
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setServerError(errorMessage(error));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthLayout title="Create your account" subtitle="Secure sign-up for the HeartGuard AI demo.">
      {serverError && <Alert tone="error" className="mb-4">{serverError}</Alert>}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <Field label="Name" htmlFor="name" error={errors.name}>
          <TextInput
            id="name"
            autoComplete="name"
            placeholder="Your full name"
            value={form.name}
            error={errors.name}
            onChange={set("name")}
          />
        </Field>
        <Field label="Email" htmlFor="email" error={errors.email}>
          <TextInput
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            value={form.email}
            error={errors.email}
            onChange={set("email")}
          />
        </Field>
        <Field
          label="Password"
          htmlFor="password"
          error={errors.password}
          helper="At least 8 characters with an uppercase letter, a lowercase letter and a digit."
        >
          <TextInput
            id="password"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            value={form.password}
            error={errors.password}
            onChange={set("password")}
          />
        </Field>
        <Field label="Confirm password" htmlFor="confirmPassword" error={errors.password}>
          <TextInput
            id="confirmPassword"
            type="password"
            autoComplete="new-password"
            placeholder="••••••••"
            value={form.confirmPassword}
            onChange={set("confirmPassword")}
          />
        </Field>
        <SubmitButton loading={loading} className="w-full">
          {loading ? "Creating account…" : "Create account"}
        </SubmitButton>
      </form>
      <p className="mt-5 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-semibold text-primary-800 hover:underline">
          Log in
        </Link>
      </p>
    </AuthLayout>
  );
}
