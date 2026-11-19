export const inputCls =
  "w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 dark:text-slate-100 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";
export const btnPrimary =
  "inline-flex items-center justify-center rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50";
export const btnSecondary =
  "inline-flex items-center justify-center rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-700 dark:text-slate-200 transition hover:bg-slate-50 dark:hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50";
export const btnDanger =
  "inline-flex items-center justify-center rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700 disabled:cursor-not-allowed disabled:opacity-50";
export const btnSm = " !px-3 !py-1.5 !text-xs";

export const money = (n) => "₹" + Number(n || 0).toLocaleString("en-IN");
export const fmtDateTime = (iso) =>
  new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
export const fmtMinutes = (m) => (m >= 60 ? `${Math.floor(m / 60)}h${m % 60 ? ` ${m % 60}m` : ""}` : `${m} min`);

export function Spinner({ label = "Loading…" }) {
  return (
    <div className="flex items-center justify-center gap-3 py-12 text-slate-500 dark:text-slate-400">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
      <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorBox({ message }) {
  if (!message) return null;
  return <div role="alert" className="rounded-lg border border-rose-200 dark:border-rose-500/30 bg-rose-50 dark:bg-rose-500/10 px-4 py-3 text-sm text-rose-700 dark:text-rose-300">{message}</div>;
}

export function SuccessBox({ message }) {
  if (!message) return null;
  return <div className="rounded-lg border border-emerald-200 dark:border-emerald-500/30 bg-emerald-50 dark:bg-emerald-500/10 px-4 py-3 text-sm text-emerald-700 dark:text-emerald-300">{message}</div>;
}

export function Empty({ children }) {
  return <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-900/50 py-10 text-center text-sm text-slate-500 dark:text-slate-400">{children}</div>;
}

export function Card({ className = "", children }) {
  return <div className={`rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-5 shadow-sm ${className}`}>{children}</div>;
}

export function Field({ label, hint, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-200">{label}</span>
      {children}
      {hint && <span className="mt-1 block text-xs text-slate-500 dark:text-slate-400">{hint}</span>}
    </label>
  );
}

const STATUS_STYLES = {
  pending: "bg-amber-100 dark:bg-amber-500/20 text-amber-800 dark:text-amber-300",
  accepted: "bg-sky-100 dark:bg-sky-500/20 text-sky-800 dark:text-sky-300",
  in_progress: "bg-indigo-100 dark:bg-indigo-500/20 text-indigo-800 dark:text-indigo-300",
  completed: "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300",
  rejected: "bg-rose-100 dark:bg-rose-500/20 text-rose-800 dark:text-rose-300",
  cancelled: "bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200",
  verified: "bg-emerald-100 dark:bg-emerald-500/20 text-emerald-800 dark:text-emerald-300",
};
export function StatusBadge({ status }) {
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${STATUS_STYLES[status] || "bg-slate-100 dark:bg-slate-800"}`}>
      {status.replace("_", " ")}
    </span>
  );
}

export function VerifiedBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 dark:bg-emerald-500/20 px-2 py-0.5 text-xs font-semibold text-emerald-800 dark:text-emerald-300">
      ✔ Verified
    </span>
  );
}

export function Stars({ value, count }) {
  const full = Math.round(value || 0);
  return (
    <span className="inline-flex items-center gap-1 text-sm">
      <span className="text-amber-400" role="img" aria-label={`${Number(value || 0).toFixed(1)} out of 5 stars`}>{"★".repeat(full)}<span className="text-slate-300 dark:text-slate-600">{"★".repeat(5 - full)}</span></span>
      {count !== undefined && (
        <span className="text-slate-500 dark:text-slate-400">{count ? `${Number(value).toFixed(1)} (${count})` : "No reviews yet"}</span>
      )}
    </span>
  );
}
