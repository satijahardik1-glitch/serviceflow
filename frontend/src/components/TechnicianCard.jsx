import { Link } from "react-router-dom";
import { Stars, VerifiedBadge, btnPrimary, btnSecondary, money } from "./ui.jsx";

export default function TechnicianCard({ tech, onSelect, onRemove }) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-5 shadow-sm sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-2">
        <div className="flex flex-wrap items-center gap-2">
          <Link to={`/technicians/${tech.id}`} className="text-lg font-bold hover:text-indigo-600">{tech.name}</Link>
          {tech.verification_status === "verified" && <VerifiedBadge />}
          {!tech.is_available && <span className="rounded-full bg-slate-200 dark:bg-slate-700 px-2 py-0.5 text-xs font-semibold text-slate-600 dark:text-slate-300">Unavailable</span>}
          {tech.score !== undefined && <span className="rounded-full bg-indigo-100 dark:bg-indigo-500/20 px-2 py-0.5 text-xs font-semibold text-indigo-700 dark:text-indigo-300">Match {tech.score}/100</span>}
        </div>
        <Stars value={tech.avg_rating} count={tech.review_count} />
        <p className="text-sm text-slate-600 dark:text-slate-300">
          📍 {tech.city} · {tech.experience_years} yrs experience · from <b>{money(tech.base_rate)}</b> visit
        </p>
        <div className="flex flex-wrap gap-1.5">
          {tech.categories.map((c) => (
            <span key={c.id} className="rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-0.5 text-xs text-slate-700 dark:text-slate-200">{c.icon} {c.name}</span>
          ))}
        </div>
        {tech.reasons && <p className="text-xs text-slate-500 dark:text-slate-400">{tech.reasons.join(" · ")}</p>}
      </div>
      <div className="flex shrink-0 gap-2 sm:flex-col">
        {onSelect && <button className={btnPrimary} disabled={!tech.is_available} onClick={() => onSelect(tech)}>Select</button>}
        <Link to={`/technicians/${tech.id}`} className={btnSecondary}>View profile</Link>
        {onRemove && <button className={btnSecondary} onClick={() => onRemove(tech)}>Remove</button>}
      </div>
    </div>
  );
}
