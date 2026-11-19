import { useCallback, useEffect, useState } from "react";
import api, { errMsg } from "../api.js";
import { Card, Empty, ErrorBox, Field, Spinner, SuccessBox, btnDanger, btnPrimary, btnSecondary, btnSm, fmtMinutes, inputCls, money } from "./ui.jsx";

const BLANK = { symptom: "", keywords: "", diagnosis: "", min_price: "", max_price: "", estimated_minutes: 60, priority: 0, is_default: false };

export default function RulesManager() {
  const [categories, setCategories] = useState([]);
  const [catId, setCatId] = useState(null);
  const [rules, setRules] = useState(null);
  const [form, setForm] = useState(null); // null = closed, otherwise the rule being edited/created
  const [newCat, setNewCat] = useState({ name: "", icon: "🛠️" });
  const [error, setError] = useState("");
  const [ok, setOk] = useState("");

  const loadCats = useCallback((selectId) =>
    api.get("/services/categories").then((r) => {
      setCategories(r.data);
      setCatId((cur) => selectId ?? (r.data.some((c) => c.id === cur) ? cur : r.data[0]?.id ?? null));
    }).catch((e) => setError(errMsg(e))), []);
  useEffect(() => { loadCats(); }, [loadCats]);

  const loadRules = useCallback(() => {
    if (!catId) return;
    setRules(null);
    api.get("/admin/rules", { params: { category_id: catId } }).then((r) => setRules(r.data)).catch((e) => setError(errMsg(e)));
  }, [catId]);
  useEffect(() => { setForm(null); loadRules(); }, [loadRules]);

  const run = async (fn, msg) => {
    setError(""); setOk("");
    try { await fn(); if (msg) setOk(msg); return true; } catch (e) { setError(errMsg(e)); return false; }
  };

  const addCategory = async (e) => {
    e.preventDefault();
    let created;
    if (await run(async () => { created = (await api.post("/admin/categories", newCat)).data; }, "Category created with a fallback rule.")) {
      setNewCat({ name: "", icon: "🛠️" });
      loadCats(created.id);
    }
  };
  const removeCategory = async () => {
    if (!window.confirm("Delete this category and all its rules?")) return;
    if (await run(() => api.delete(`/admin/categories/${catId}`), "Category deleted.")) { setCatId(null); loadCats(); }
  };

  const saveRule = async (e) => {
    e.preventDefault();
    const payload = {
      symptom: form.symptom, keywords: form.keywords, diagnosis: form.diagnosis, is_default: form.is_default,
      min_price: Number(form.min_price), max_price: Number(form.max_price),
      estimated_minutes: Number(form.estimated_minutes), priority: Number(form.priority),
    };
    const done = await run(() => form.id
      ? api.put(`/admin/rules/${form.id}`, payload)
      : api.post("/admin/rules", { ...payload, category_id: catId }), "Rule saved.");
    if (done) { setForm(null); loadRules(); }
  };
  const removeRule = async (r) => {
    if (!window.confirm(`Delete rule "${r.symptom}"?`)) return;
    if (await run(() => api.delete(`/admin/rules/${r.id}`), "Rule deleted.")) loadRules();
  };
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value }));

  return (
    <div className="space-y-4">
      <ErrorBox message={error} />
      <SuccessBox message={ok} />
      <Card>
        <form onSubmit={addCategory} className="flex flex-wrap items-end gap-3">
          <Field label="New service category"><input required minLength={2} className={inputCls} value={newCat.name} onChange={(e) => setNewCat({ ...newCat, name: e.target.value })} placeholder="e.g. Painting" /></Field>
          <Field label="Icon"><input className={`${inputCls} w-20`} maxLength={4} value={newCat.icon} onChange={(e) => setNewCat({ ...newCat, icon: e.target.value })} /></Field>
          <button className={btnPrimary}>Add category</button>
        </form>
      </Card>

      <div className="flex flex-wrap items-center gap-3">
        <select className={`${inputCls} max-w-xs`} value={catId || ""} onChange={(e) => setCatId(Number(e.target.value))}>
          {categories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
        </select>
        <button className={btnPrimary + btnSm} disabled={!catId} onClick={() => setForm({ ...BLANK })}>+ Add rule</button>
        <button className={btnDanger + btnSm} disabled={!catId} onClick={removeCategory}>Delete category</button>
      </div>

      {form && (
        <Card>
          <form onSubmit={saveRule} className="space-y-4">
            <h3 className="font-bold">{form.id ? "Edit rule" : "New rule"}</h3>
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="Symptom label (shown to customers)"><input required minLength={2} className={inputCls} value={form.symptom} onChange={set("symptom")} /></Field>
              <Field label="Diagnosis"><input required minLength={3} className={inputCls} value={form.diagnosis} onChange={set("diagnosis")} /></Field>
            </div>
            <Field label="Keywords" hint="Comma separated. Matched against the customer's description (case-insensitive). Optional only for the fallback rule.">
              <textarea rows={2} className={inputCls} value={form.keywords} onChange={set("keywords")} placeholder="leak, dripping, seepage" />
            </Field>
            <div className="grid gap-4 sm:grid-cols-4">
              <Field label="Min price (₹)"><input required type="number" min="0" className={inputCls} value={form.min_price} onChange={set("min_price")} /></Field>
              <Field label="Max price (₹)"><input required type="number" min="0" className={inputCls} value={form.max_price} onChange={set("max_price")} /></Field>
              <Field label="Minutes"><input required type="number" min="5" className={inputCls} value={form.estimated_minutes} onChange={set("estimated_minutes")} /></Field>
              <Field label="Priority" hint="Wins ties; use high for safety issues"><input type="number" min="0" max="100" className={inputCls} value={form.priority} onChange={set("priority")} /></Field>
            </div>
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.is_default} onChange={set("is_default")} /> Fallback rule (used when nothing else matches)</label>
            <div className="flex gap-2">
              <button className={btnPrimary}>Save rule</button>
              <button type="button" className={btnSecondary} onClick={() => setForm(null)}>Cancel</button>
            </div>
          </form>
        </Card>
      )}

      {!rules ? <Spinner /> : rules.length === 0 ? <Empty>No rules yet.</Empty> : (
        <div className="space-y-2">
          {rules.map((r) => (
            <div key={r.id} className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 text-sm">
              <div className="space-y-1">
                <div className="flex items-center gap-2"><b>{r.symptom}</b>{r.is_default && <span className="rounded-full bg-slate-200 dark:bg-slate-700 px-2 py-0.5 text-xs">fallback</span>}{r.priority > 0 && <span className="text-xs text-slate-500 dark:text-slate-400">priority {r.priority}</span>}</div>
                <div>{r.diagnosis}</div>
                <div className="text-slate-500 dark:text-slate-400">{money(r.min_price)} – {money(r.max_price)} · {fmtMinutes(r.estimated_minutes)}</div>
                {r.keywords && <div className="text-xs text-slate-400 dark:text-slate-500">{r.keywords.split(",").join(" · ")}</div>}
              </div>
              <div className="flex gap-2">
                <button className={btnSecondary + btnSm} onClick={() => setForm({ ...r })}>Edit</button>
                {!r.is_default && <button className={btnDanger + btnSm} onClick={() => removeRule(r)}>Delete</button>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
