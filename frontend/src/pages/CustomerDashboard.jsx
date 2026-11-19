import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errMsg } from "../api.js";
import BookingCard from "../components/BookingCard.jsx";
import Tabs from "../components/Tabs.jsx";
import TechnicianCard from "../components/TechnicianCard.jsx";
import { Empty, ErrorBox, Spinner, btnPrimary } from "../components/ui.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function CustomerDashboard() {
  const { user } = useAuth();
  const [tab, setTab] = useState("bookings");
  const [bookings, setBookings] = useState(null);
  const [saved, setSaved] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    api.get("/bookings/mine").then((r) => setBookings(r.data)).catch((e) => setError(errMsg(e)));
    api.get("/technicians/saved").then((r) => setSaved(r.data)).catch((e) => setError(errMsg(e)));
  }, []);
  useEffect(() => { load(); }, [load]);

  const remove = async (t) => {
    try { await api.delete(`/technicians/${t.id}/save`); setSaved((s) => s.filter((x) => x.id !== t.id)); } catch (e) { setError(errMsg(e)); }
  };

  const active = bookings?.filter((b) => ["pending", "accepted", "in_progress"].includes(b.status)).length ?? 0;
  const stat = (label, value) => (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 p-4"><div className="text-2xl font-bold">{value}</div><div className="text-sm text-slate-500 dark:text-slate-400">{label}</div></div>
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><h1 className="text-3xl font-bold">My dashboard</h1><p className="text-slate-500 dark:text-slate-400">Welcome, {user.name}</p></div>
        <Link to="/book" className={btnPrimary}>+ New booking</Link>
      </div>
      <ErrorBox message={error} />
      <div className="grid gap-4 sm:grid-cols-3">
        {stat("Total bookings", bookings?.length ?? "–")}
        {stat("Active", bookings ? active : "–")}
        {stat("Trusted technicians", saved?.length ?? "–")}
      </div>
      <Tabs active={tab} onChange={setTab} tabs={[["bookings", "My bookings"], ["trusted", "Trusted technicians"]]} />
      {tab === "bookings" && (!bookings ? <Spinner /> : bookings.length === 0 ?
        <Empty>No bookings yet. <Link to="/book" className="text-indigo-600 dark:text-indigo-400 underline">Book your first service</Link>.</Empty> :
        <div className="space-y-4">{bookings.map((b) => <BookingCard key={b.id} booking={b} role="customer" onChanged={load} />)}</div>)}
      {tab === "trusted" && (!saved ? <Spinner /> : saved.length === 0 ?
        <Empty>Save technicians from their profile to rebook them quickly.</Empty> :
        <div className="space-y-3">{saved.map((t) => <TechnicianCard key={t.id} tech={t} onRemove={remove} />)}</div>)}
    </div>
  );
}
