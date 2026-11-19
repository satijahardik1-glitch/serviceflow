import { btnSecondary, btnSm } from "./ui.jsx";

export default function Pager({ offset, limit, total, onChange }) {
  if (!total || total <= limit) return null;
  const from = offset + 1;
  const to = Math.min(offset + limit, total);
  return (
    <div className="flex items-center justify-between text-sm text-slate-600 dark:text-slate-300">
      <span>{from}–{to} of {total}</span>
      <div className="flex gap-2">
        <button className={btnSecondary + btnSm} disabled={offset === 0} onClick={() => onChange(Math.max(0, offset - limit))}>← Previous</button>
        <button className={btnSecondary + btnSm} disabled={to >= total} onClick={() => onChange(offset + limit)}>Next →</button>
      </div>
    </div>
  );
}
