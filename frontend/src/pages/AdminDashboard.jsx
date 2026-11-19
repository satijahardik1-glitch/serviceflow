import { useCallback, useEffect, useState } from "react";
import api, { errMsg } from "../api.js";
import Pager from "../components/Pager.jsx";
import RulesManager from "../components/RulesManager.jsx";
import Tabs from "../components/Tabs.jsx";
import { Empty, ErrorBox, Spinner, Stars, StatusBadge, btnDanger, btnPrimary, btnSecondary, btnSm, fmtDateTime, inputCls, money } from "../components/ui.jsx";

function Metric({ label, value, tone = "" }) {
  return <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4"><div className={`text-2xl font-bold ${tone}`}>{value}</div><div className="text-sm text-slate-500 dark:text-slate-400">{label}</div></div>;
}

function VerificationQueue({ techs, onReview }) {
  const [notes, setNotes] = useState({});
  if (!techs.length) return <Empty>No technicians in this list.</Empty>;
  return (
    <div className="space-y-3">
      {techs.map((t) => (
        <div key={t.id} className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-1 text-sm">
              <div className="flex items-center gap-2"><b className="text-base">{t.name}</b><StatusBadge status={t.verification_status} /></div>
              <div className="text-slate-600 dark:text-slate-300">{t.email} · {t.phone || "no phone"} · {t.city}</div>
              <div className="text-slate-600 dark:text-slate-300">{t.categories.map((c) => c.name).join(", ")} · {t.experience_years} yrs · {money(t.base_rate)}</div>
              <div><span className="text-slate-500 dark:text-slate-400">ID:</span> {t.id_document_type ? `${t.id_document_type} – ${t.id_document_number}` : <i className="text-rose-600 dark:text-rose-400">not submitted</i>}</div>
              {t.verification_note && <div className="text-slate-500 dark:text-slate-400">Note: {t.verification_note}</div>}
            </div>
            <div className="w-full space-y-2 sm:w-64">
              <input className={inputCls} placeholder="Note (required to reject)" value={notes[t.id] || ""} onChange={(e) => setNotes({ ...notes, [t.id]: e.target.value })} />
              <div className="flex gap-2">
                <button className={btnPrimary + btnSm} disabled={t.verification_status === "verified"} onClick={() => onReview(t.id, "verified", notes[t.id])}>Approve</button>
                <button className={btnDanger + btnSm} disabled={t.verification_status === "rejected"} onClick={() => onReview(t.id, "rejected", notes[t.id])}>Reject</button>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

const Table = ({ head, children }) => (
  <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900">
    <table className="min-w-full text-left text-sm">
      <thead className="bg-slate-50 dark:bg-slate-800/50 text-xs uppercase text-slate-500 dark:text-slate-400"><tr>{head.map((h) => <th key={h} className="px-4 py-3">{h}</th>)}</tr></thead>
      <tbody className="divide-y divide-slate-100 dark:divide-slate-800">{children}</tbody>
    </table>
  </div>
);

export default function AdminDashboard() {
  const [tab, setTab] = useState("verification");
  const [metrics, setMetrics] = useState(null);
  const [techs, setTechs] = useState(null);
  const PAGE = 25;
  const [users, setUsers] = useState(null);
  const [userPage, setUserPage] = useState({ offset: 0, total: 0 });
  const [bookings, setBookings] = useState(null);
  const [bookingPage, setBookingPage] = useState({ offset: 0, total: 0 });
  const [bookingFilter, setBookingFilter] = useState("");
  const [error, setError] = useState("");

  const loadAll = useCallback(() => {
    const fail = (e) => setError(errMsg(e));
    api.get("/admin/metrics").then((r) => setMetrics(r.data)).catch(fail);
    api.get("/admin/technicians", { params: { limit: 200 } }).then((r) => setTechs(r.data)).catch(fail);
  }, []);
  const loadUsers = useCallback((offset = 0) =>
    api.get("/admin/users", { params: { limit: PAGE, offset } })
      .then((r) => { setUsers(r.data); setUserPage({ offset, total: Number(r.headers["x-total-count"]) }); })
      .catch((e) => setError(errMsg(e))), []);
  const loadBookings = useCallback((offset = 0) => {
    setBookings(null);
    return api.get("/admin/bookings", { params: { limit: PAGE, offset, status: bookingFilter || undefined } })
      .then((r) => { setBookings(r.data); setBookingPage({ offset, total: Number(r.headers["x-total-count"]) }); })
      .catch((e) => setError(errMsg(e)));
  }, [bookingFilter]);
  useEffect(() => { loadAll(); loadUsers(0); }, [loadAll, loadUsers]);
  useEffect(() => { loadBookings(0); }, [loadBookings]);

  const review = async (id, status, note) => {
    setError("");
    try { await api.patch(`/admin/technicians/${id}/verification`, { status, note: note || null }); loadAll(); } catch (e) { setError(errMsg(e)); }
  };
  const toggleUser = async (u) => {
    setError("");
    try { await api.patch(`/admin/users/${u.id}/status`, { is_active: !u.is_active }); loadAll(); loadUsers(userPage.offset); } catch (e) { setError(errMsg(e)); }
  };

  const pending = techs?.filter((t) => t.verification_status === "pending") || [];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Admin panel</h1>
      <ErrorBox message={error} />
      {metrics && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Metric label="Customers" value={metrics.customers} />
          <Metric label="Technicians" value={metrics.technicians} />
          <Metric label="Pending verification" value={metrics.technicians_pending} tone={metrics.technicians_pending ? "text-amber-600 dark:text-amber-400" : ""} />
          <Metric label="Verified technicians" value={metrics.technicians_verified} tone="text-emerald-600 dark:text-emerald-400" />
          <Metric label="Total bookings" value={metrics.total_bookings} />
          <Metric label="Completed" value={metrics.bookings_by_status.completed || 0} />
          <Metric label="Est. completed job value" value={money(metrics.completed_value_estimate)} />
          <Metric label="Avg. technician rating" value={metrics.average_platform_rating ? `${metrics.average_platform_rating} ★` : "–"} />
        </div>
      )}
      <Tabs active={tab} onChange={setTab} tabs={[["verification", "Verification requests", pending.length], ["technicians", "All technicians"], ["users", "Users"], ["bookings", "Bookings"], ["rules", "Service rules"]]} />

      {tab === "verification" && (!techs ? <Spinner /> : <VerificationQueue techs={pending} onReview={review} />)}
      {tab === "technicians" && (!techs ? <Spinner /> : <VerificationQueue techs={techs} onReview={review} />)}

      {tab === "users" && (!users ? <Spinner /> : (
        <Table head={["Name", "Email", "Role", "City", "Joined", "Status", ""]}>
          {users.map((u) => (
            <tr key={u.id}>
              <td className="px-4 py-3 font-medium">{u.name}</td><td className="px-4 py-3">{u.email}</td>
              <td className="px-4 py-3 capitalize">{u.role}</td><td className="px-4 py-3">{u.city || "–"}</td>
              <td className="px-4 py-3">{fmtDateTime(u.created_at)}</td>
              <td className="px-4 py-3">{u.is_active ? <span className="text-emerald-600 dark:text-emerald-400">Active</span> : <span className="text-rose-600 dark:text-rose-400">Deactivated</span>}</td>
              <td className="px-4 py-3 text-right">{u.role !== "admin" && <button className={btnSecondary + btnSm} onClick={() => toggleUser(u)}>{u.is_active ? "Deactivate" : "Activate"}</button>}</td>
            </tr>
          ))}
        </Table>
      ))}
      {tab === "users" && users && <Pager offset={userPage.offset} limit={PAGE} total={userPage.total} onChange={loadUsers} />}

      {tab === "bookings" && (
        <div className="space-y-3">
          <select className={`${inputCls} max-w-xs`} value={bookingFilter} onChange={(e) => setBookingFilter(e.target.value)}>
            <option value="">All statuses</option>
            {["pending", "accepted", "in_progress", "completed", "rejected", "cancelled"].map((s) => <option key={s} value={s}>{s.replace("_", " ")}</option>)}
          </select>
          {!bookings ? <Spinner /> : bookings.length === 0 ? <Empty>No bookings found.</Empty> : (
            <Table head={["#", "Service", "Customer", "Technician", "Scheduled", "Estimate", "Status", "Review"]}>
              {bookings.map((b) => (
                <tr key={b.id}>
                  <td className="px-4 py-3">{b.id}</td><td className="px-4 py-3">{b.category_name}</td>
                  <td className="px-4 py-3">{b.customer_name}</td><td className="px-4 py-3">{b.technician_name}</td>
                  <td className="px-4 py-3">{fmtDateTime(b.scheduled_at)}</td>
                  <td className="px-4 py-3 whitespace-nowrap">{money(b.estimated_min_price)}–{money(b.estimated_max_price)}</td>
                  <td className="px-4 py-3"><StatusBadge status={b.status} /></td>
                  <td className="px-4 py-3">{b.review ? <Stars value={b.review.rating} /> : "–"}</td>
                </tr>
              ))}
            </Table>
          )}
          <Pager offset={bookingPage.offset} limit={PAGE} total={bookingPage.total} onChange={loadBookings} />
        </div>
      )}

      {tab === "rules" && <RulesManager />}
    </div>
  );
}
