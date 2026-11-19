import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import api, { errMsg } from "../api.js";
import { dashboardPath, useAuth } from "../context/AuthContext.jsx";
import { Card, ErrorBox, Field, btnPrimary, inputCls } from "../components/ui.jsx";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({
    role: "customer", name: "", email: "", password: "", phone: "", city: "",
    category_ids: [], base_rate: "", experience_years: "", bio: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get("/services/categories").then((r) => setCategories(r.data)).catch(() => {}); }, []);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const toggleCat = (id) => setForm((f) => ({
    ...f, category_ids: f.category_ids.includes(id) ? f.category_ids.filter((x) => x !== id) : [...f.category_ids, id],
  }));
  const isTech = form.role === "technician";

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (isTech && form.category_ids.length === 0) return setError("Select at least one service you offer.");
    setBusy(true);
    try {
      const payload = {
        role: form.role, name: form.name, email: form.email, password: form.password,
        phone: form.phone || null, city: form.city || null,
      };
      if (isTech) Object.assign(payload, {
        category_ids: form.category_ids, bio: form.bio || null,
        base_rate: Number(form.base_rate) || 0, experience_years: Number(form.experience_years) || 0,
      });
      const user = await register(payload);
      navigate(dashboardPath(user.role), { replace: true });
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl">
      <Card>
        <h1 className="mb-4 text-2xl font-bold">Create your account</h1>
        <div className="mb-5 grid grid-cols-2 gap-2 rounded-lg bg-slate-100 dark:bg-slate-800 p-1">
          {[["customer", "I need a technician"], ["technician", "I'm a technician"]].map(([r, label]) => (
            <button key={r} type="button" onClick={() => setForm({ ...form, role: r })}
              className={`rounded-md py-2 text-sm font-semibold ${form.role === r ? "bg-white dark:bg-slate-700 shadow text-indigo-700 dark:text-white" : "text-slate-600 dark:text-slate-300"}`}>{label}</button>
          ))}
        </div>
        <form onSubmit={submit} className="space-y-4">
          <ErrorBox message={error} />
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Full name"><input required minLength={2} className={inputCls} value={form.name} onChange={set("name")} /></Field>
            <Field label="Phone"><input className={inputCls} value={form.phone} onChange={set("phone")} /></Field>
          </div>
          <Field label="Email"><input type="email" required className={inputCls} value={form.email} onChange={set("email")} /></Field>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Password" hint="8+ characters with a letter and a number"><input type="password" required minLength={8} className={inputCls} value={form.password} onChange={set("password")} /></Field>
            <Field label="City"><input required={isTech} className={inputCls} value={form.city} onChange={set("city")} /></Field>
          </div>
          {isTech && (
            <>
              <Field label="Services you offer">
                <div className="flex flex-wrap gap-2">
                  {categories.map((c) => (
                    <button type="button" key={c.id} onClick={() => toggleCat(c.id)}
                      className={`rounded-full border px-3 py-1 text-sm ${form.category_ids.includes(c.id) ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300" : "border-slate-300 dark:border-slate-600"}`}>
                      {c.icon} {c.name}
                    </button>
                  ))}
                </div>
              </Field>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Visit charge (₹)"><input type="number" min="0" className={inputCls} value={form.base_rate} onChange={set("base_rate")} /></Field>
                <Field label="Years of experience"><input type="number" min="0" max="60" className={inputCls} value={form.experience_years} onChange={set("experience_years")} /></Field>
              </div>
              <Field label="Short bio"><textarea rows={3} className={inputCls} value={form.bio} onChange={set("bio")} /></Field>
              <p className="rounded-lg bg-amber-50 dark:bg-amber-500/10 p-3 text-xs text-amber-800 dark:text-amber-300">After signing up, submit your ID details from your dashboard. You'll appear in search results once an admin verifies you.</p>
            </>
          )}
          <button disabled={busy} className={`${btnPrimary} w-full`}>{busy ? "Creating account…" : "Sign up"}</button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500 dark:text-slate-400">Already registered? <Link to="/login" className="font-medium text-indigo-600 dark:text-indigo-400 hover:underline">Log in</Link></p>
      </Card>
    </div>
  );
}
