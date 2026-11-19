import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { dashboardPath, useAuth } from "../context/AuthContext.jsx";
import { errMsg } from "../api.js";
import { Card, ErrorBox, Field, btnPrimary, inputCls } from "../components/ui.jsx";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const user = await login(form.email, form.password);
      navigate(location.state?.from || dashboardPath(user.role), { replace: true });
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <Card>
        <h1 className="mb-1 text-2xl font-bold">Welcome back</h1>
        <p className="mb-5 text-sm text-slate-500 dark:text-slate-400">Log in to manage your bookings.</p>
        <form onSubmit={submit} className="space-y-4">
          <ErrorBox message={error} />
          <Field label="Email"><input type="email" required className={inputCls} value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></Field>
          <Field label="Password"><input type="password" required className={inputCls} value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} /></Field>
          <button disabled={busy} className={`${btnPrimary} w-full`}>{busy ? "Signing in…" : "Log in"}</button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">New here? <Link to="/register" className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline">Create an account</Link></p>
      </Card>
    </div>
  );
}
