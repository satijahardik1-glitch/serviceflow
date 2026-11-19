import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { errMsg } from "../api.js";
import { useAuth } from "../context/AuthContext.jsx";
import { ErrorBox, Field, btnPrimary, inputCls } from "./ui.jsx";

const toLocalInput = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16);

export default function BookingForm({ technician, defaultCategoryId, defaultDescription = "", symptoms = [], onBooked }) {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    category_id: defaultCategoryId || technician.categories[0]?.id,
    problem_description: defaultDescription,
    address: "",
    city: user?.city || technician.city,
    scheduled_at: "",
  });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const minDate = toLocalInput(new Date(Date.now() + 60 * 60000));

  const submit = async (e) => {
    e.preventDefault();
    if (!user) return navigate("/login", { state: { from: window.location.pathname + window.location.search } });
    if (user.role !== "customer") return setError("Only customer accounts can book services.");
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post("/bookings", {
        technician_id: technician.id,
        category_id: Number(form.category_id),
        problem_description: form.problem_description,
        symptoms,
        address: form.address,
        city: form.city,
        scheduled_at: new Date(form.scheduled_at).toISOString(),
      });
      onBooked ? onBooked(data) : navigate("/customer");
    } catch (err) {
      setError(errMsg(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4">
      <ErrorBox message={error} />
      <Field label="Service">
        <select className={inputCls} value={form.category_id} onChange={set("category_id")}>
          {technician.categories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
        </select>
      </Field>
      <Field label="Describe the problem" hint="We use this to prepare a diagnosis and price estimate for the technician.">
        <textarea required minLength={5} rows={3} className={inputCls} value={form.problem_description} onChange={set("problem_description")} />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Address"><input required minLength={5} className={inputCls} value={form.address} onChange={set("address")} placeholder="House no., street, locality" /></Field>
        <Field label="City"><input required className={inputCls} value={form.city} onChange={set("city")} /></Field>
      </div>
      <Field label="Preferred date & time">
        <input required type="datetime-local" min={minDate} className={inputCls} value={form.scheduled_at} onChange={set("scheduled_at")} />
      </Field>
      <button type="submit" disabled={busy || !technician.is_available} className={`${btnPrimary} w-full`}>
        {busy ? "Sending request…" : user ? "Request booking" : "Log in to book"}
      </button>
    </form>
  );
}
