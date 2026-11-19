import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import api, { errMsg } from "../api.js";
import BookingForm from "../components/BookingForm.jsx";
import TechnicianCard from "../components/TechnicianCard.jsx";
import { Card, Empty, ErrorBox, Field, Spinner, btnPrimary, btnSecondary, fmtMinutes, inputCls, money } from "../components/ui.jsx";

export default function BookService() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [categories, setCategories] = useState([]);
  const [catId, setCatId] = useState(params.get("category") ? Number(params.get("category")) : null);
  const [symptomOptions, setSymptomOptions] = useState([]);
  const [symptoms, setSymptoms] = useState([]);
  const [description, setDescription] = useState("");
  const [estimate, setEstimate] = useState(null);
  const [city, setCity] = useState("");
  const [techs, setTechs] = useState(null);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api.get("/services/categories").then((r) => setCategories(r.data)).catch((e) => setError(errMsg(e))); }, []);

  useEffect(() => {
    setSymptoms([]); setEstimate(null); setTechs(null); setSelected(null);
    if (!catId) return;
    api.get("/services/symptoms", { params: { category_id: catId } }).then((r) => setSymptomOptions(r.data)).catch((e) => setError(errMsg(e)));
  }, [catId]);

  const toggle = (s) => setSymptoms((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));

  const getEstimate = async (e) => {
    e.preventDefault();
    setLoading(true); setError(""); setTechs(null); setSelected(null);
    try {
      setEstimate((await api.post("/services/diagnose", { category_id: catId, description, symptoms })).data);
    } catch (err) { setError(errMsg(err)); } finally { setLoading(false); }
  };

  const findTechs = async () => {
    setLoading(true); setError("");
    try {
      setTechs((await api.get("/technicians/match", { params: { category_id: catId, city: city || undefined } })).data);
    } catch (err) { setError(errMsg(err)); } finally { setLoading(false); }
  };

  const category = categories.find((c) => c.id === catId);
  const bookingDescription = description.trim() || symptoms.join(", ");

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Book a service</h1>
        <p className="text-slate-500 dark:text-slate-400">Get an instant diagnosis and price range, then pick a verified technician.</p>
      </div>
      <ErrorBox message={error} />

      <Card>
        <h2 className="mb-3 font-bold">1. What do you need help with?</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {categories.map((c) => (
            <button key={c.id} onClick={() => setCatId(c.id)}
              className={`rounded-xl border p-4 text-center transition ${catId === c.id ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-500/10" : "border-slate-200 dark:border-slate-700 hover:border-slate-400 dark:hover:border-slate-500"}`}>
              <div className="text-2xl">{c.icon}</div>
              <div className="mt-1 text-sm font-semibold">{c.name}</div>
            </button>
          ))}
        </div>
      </Card>

      {catId && (
        <Card>
          <h2 className="mb-3 font-bold">2. Describe the problem</h2>
          <form onSubmit={getEstimate} className="space-y-4">
            <div className="flex flex-wrap gap-2">
              {symptomOptions.map((s) => (
                <button type="button" key={s} onClick={() => toggle(s)}
                  className={`rounded-full border px-3 py-1 text-sm ${symptoms.includes(s) ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300" : "border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500"}`}>{s}</button>
              ))}
            </div>
            <Field label="Tell us more (optional if you selected a symptom)">
              <textarea rows={3} className={inputCls} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. The kitchen socket sparks whenever I plug in the kettle" />
            </Field>
            <button disabled={loading || (!description.trim() && symptoms.length === 0)} className={btnPrimary}>{loading && !estimate ? "Analysing…" : "Get diagnosis & estimate"}</button>
          </form>
        </Card>
      )}

      {estimate && (
        <Card className="!border-indigo-200 !bg-indigo-50/40 dark:!border-indigo-500/30 dark:!bg-indigo-500/10">
          <h2 className="mb-3 font-bold">Your estimate · {estimate.category_name}</h2>
          <p className="text-lg font-semibold">{estimate.diagnosis}</p>
          <div className="mt-3 grid gap-3 sm:grid-cols-3">
            <div className="rounded-lg bg-white dark:bg-slate-900 p-3 shadow-sm"><span className="block text-xs text-slate-500 dark:text-slate-400">Price range</span><b>{money(estimate.min_price)} – {money(estimate.max_price)}</b></div>
            <div className="rounded-lg bg-white dark:bg-slate-900 p-3"><span className="block text-xs text-slate-500 dark:text-slate-400">Estimated time</span><b>{fmtMinutes(estimate.estimated_minutes)}</b></div>
            <div className="rounded-lg bg-white dark:bg-slate-900 p-3"><span className="block text-xs text-slate-500 dark:text-slate-400">Confidence</span><b>{Math.round(estimate.confidence * 100)}%</b></div>
          </div>
          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            {estimate.is_fallback
              ? "We couldn't match specific symptoms, so this is a general inspection estimate. Add more detail for a sharper result."
              : `Matched on: ${estimate.matched_keywords.join(", ")}.`} Final price is confirmed by the technician on site.
          </p>
          <div className="mt-4 flex flex-wrap items-end gap-3">
            <Field label="Your city (to find nearby technicians)"><input className={inputCls} value={city} onChange={(e) => setCity(e.target.value)} placeholder="e.g. Jalandhar" /></Field>
            <button className={btnPrimary} onClick={findTechs} disabled={loading}>Find technicians</button>
          </div>
        </Card>
      )}

      {loading && estimate && !techs && <Spinner label="Matching technicians…" />}
      {techs && !selected && (
        <div className="space-y-3">
          <h2 className="font-bold">3. Choose a technician ({techs.length} matched)</h2>
          {techs.length === 0 ? <Empty>No verified {category?.name} technicians found yet.</Empty> :
            techs.map((t) => <TechnicianCard key={t.id} tech={t} onSelect={setSelected} />)}
        </div>
      )}
      {selected && (
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-bold">4. Book {selected.name}</h2>
            <button className={btnSecondary} onClick={() => setSelected(null)}>Change technician</button>
          </div>
          <BookingForm technician={selected} defaultCategoryId={catId} defaultDescription={bookingDescription} symptoms={symptoms}
            onBooked={() => navigate("/customer")} />
        </Card>
      )}
    </div>
  );
}
