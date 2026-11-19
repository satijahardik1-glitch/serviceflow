import { useCallback, useEffect, useState } from "react";
import api, { errMsg } from "../api.js";
import TechnicianCard from "../components/TechnicianCard.jsx";
import { Empty, ErrorBox, Field, Spinner, inputCls } from "../components/ui.jsx";

export default function Technicians() {
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ category_id: "", city: "", available_only: false });
  const [techs, setTechs] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { api.get("/services/categories").then((r) => setCategories(r.data)).catch(() => {}); }, []);

  const search = useCallback(() => {
    setTechs(null); setError("");
    api.get("/technicians/match", {
      params: { category_id: filters.category_id || undefined, city: filters.city || undefined, available_only: filters.available_only || undefined },
    }).then((r) => setTechs(r.data)).catch((e) => setError(errMsg(e)));
  }, [filters]);

  useEffect(() => { const t = setTimeout(search, 300); return () => clearTimeout(t); }, [search]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Find a verified technician</h1>
        <p className="text-slate-500 dark:text-slate-400">Ranked by skill match, availability, location and customer ratings.</p>
      </div>
      <div className="grid gap-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4 sm:grid-cols-3">
        <Field label="Service">
          <select className={inputCls} value={filters.category_id} onChange={(e) => setFilters({ ...filters, category_id: e.target.value })}>
            <option value="">All services</option>
            {categories.map((c) => <option key={c.id} value={c.id}>{c.icon} {c.name}</option>)}
          </select>
        </Field>
        <Field label="City"><input className={inputCls} placeholder="e.g. Jalandhar" value={filters.city} onChange={(e) => setFilters({ ...filters, city: e.target.value })} /></Field>
        <label className="flex items-end gap-2 pb-2 text-sm">
          <input type="checkbox" className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500" checked={filters.available_only} onChange={(e) => setFilters({ ...filters, available_only: e.target.checked })} /> Available now only
        </label>
      </div>
      <ErrorBox message={error} />
      {!techs && !error && <Spinner label="Finding technicians…" />}
      {techs && (techs.length === 0 ? <Empty>No technicians match your filters.</Empty> :
        <div className="space-y-3">{techs.map((t) => <TechnicianCard key={t.id} tech={t} />)}</div>)}
    </div>
  );
}
