import { useState } from "react";
import api, { errMsg } from "../api.js";
import { ErrorBox, Stars, StatusBadge, btnDanger, btnPrimary, btnSecondary, btnSm, fmtDateTime, fmtMinutes, inputCls, money } from "./ui.jsx";

const TECH_ACTIONS = {
  pending: [["accepted", "Accept", btnPrimary], ["rejected", "Reject", btnDanger]],
  accepted: [["in_progress", "Start job", btnPrimary], ["cancelled", "Cancel", btnSecondary]],
  in_progress: [["completed", "Mark completed", btnPrimary], ["cancelled", "Cancel", btnSecondary]],
};
const CUSTOMER_ACTIONS = { pending: [["cancelled", "Cancel request", btnSecondary]], accepted: [["cancelled", "Cancel booking", btnSecondary]] };

export default function BookingCard({ booking: b, role, onChanged }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [review, setReview] = useState({ rating: 5, comment: "" });

  const actions = (role === "technician" ? TECH_ACTIONS : CUSTOMER_ACTIONS)[b.status] || [];

  const run = async (fn) => {
    setBusy(true);
    setError("");
    try { await fn(); onChanged(); setReviewing(false); } catch (e) { setError(errMsg(e)); } finally { setBusy(false); }
  };
  const changeStatus = (status) => run(() => api.patch(`/bookings/${b.id}/status`, { status }));
  const submitReview = (e) => { e.preventDefault(); run(() => api.post(`/bookings/${b.id}/review`, review)); };

  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="font-bold">{b.category_name} · #{b.id}</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            {role === "technician" ? `Customer: ${b.customer_name}` : `Technician: ${b.technician_name}`} · {fmtDateTime(b.scheduled_at)}
          </p>
        </div>
        <StatusBadge status={b.status} />
      </div>
      <p className="mt-3 text-sm">{b.problem_description}</p>
      <div className="mt-3 grid gap-2 rounded-lg bg-slate-50 dark:bg-slate-800/50 p-3 text-sm sm:grid-cols-3">
        <div><span className="block text-xs text-slate-500 dark:text-slate-400">Likely diagnosis</span>{b.diagnosis}</div>
        <div><span className="block text-xs text-slate-500 dark:text-slate-400">Estimated price</span>{money(b.estimated_min_price)} – {money(b.estimated_max_price)}</div>
        <div><span className="block text-xs text-slate-500 dark:text-slate-400">Estimated time</span>{fmtMinutes(b.estimated_minutes)}</div>
      </div>
      <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">📍 {b.address}, {b.city}{role === "technician" && b.customer_phone ? ` · 📞 ${b.customer_phone}` : ""}</p>

      {b.review && (
        <div className="mt-3 rounded-lg border border-amber-200 dark:border-amber-500/30 bg-amber-50 dark:bg-amber-500/10 p-3 text-sm">
          <Stars value={b.review.rating} />
          {b.review.comment && <p className="mt-1 text-slate-700 dark:text-slate-200">“{b.review.comment}”</p>}
        </div>
      )}
      <div className="mt-3 space-y-3">
        <ErrorBox message={error} />
        <div className="flex flex-wrap gap-2">
          {actions.map(([status, label, cls]) => (
            <button key={status} disabled={busy} className={cls + btnSm} onClick={() => changeStatus(status)}>{label}</button>
          ))}
          {role === "customer" && b.status === "completed" && !b.review && !reviewing && (
            <button className={btnPrimary + btnSm} onClick={() => setReviewing(true)}>Rate & review</button>
          )}
        </div>
        {reviewing && (
          <form onSubmit={submitReview} className="space-y-3 rounded-lg border border-slate-200 dark:border-slate-700 p-3">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Rating</span>
              {[1, 2, 3, 4, 5].map((n) => (
                <button type="button" key={n} onClick={() => setReview((r) => ({ ...r, rating: n }))}
                  className={`text-2xl ${n <= review.rating ? "text-amber-400" : "text-slate-300 dark:text-slate-600"}`} aria-label={`${n} stars`}>★</button>
              ))}
            </div>
            <textarea rows={2} className={inputCls} placeholder="Share your experience (optional)" value={review.comment}
              onChange={(e) => setReview((r) => ({ ...r, comment: e.target.value }))} />
            <div className="flex gap-2">
              <button disabled={busy} className={btnPrimary + btnSm}>Submit review</button>
              <button type="button" className={btnSecondary + btnSm} onClick={() => setReviewing(false)}>Cancel</button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
