import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api, { errMsg } from "../api.js";
import BookingForm from "../components/BookingForm.jsx";
import { useAuth } from "../context/AuthContext.jsx";
import { Card, Empty, ErrorBox, Spinner, Stars, StatusBadge, SuccessBox, VerifiedBadge, btnSecondary, fmtDateTime, money } from "../components/ui.jsx";

export default function TechnicianProfile() {
  const { id } = useParams();
  const { user } = useAuth();
  const [tech, setTech] = useState(null);
  const [error, setError] = useState("");
  const [booked, setBooked] = useState(false);

  const load = () => api.get(`/technicians/${id}`).then((r) => setTech(r.data)).catch((e) => setError(errMsg(e)));
  useEffect(() => { load(); }, [id]);

  const toggleSave = async () => {
    try {
      tech.is_saved ? await api.delete(`/technicians/${id}/save`) : await api.post(`/technicians/${id}/save`);
      setTech({ ...tech, is_saved: !tech.is_saved });
    } catch (e) { setError(errMsg(e)); }
  };

  if (error && !tech) return <ErrorBox message={error} />;
  if (!tech) return <Spinner />;
  const canBook = (!user || user.role === "customer") && tech.verification_status === "verified";

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-2">
        <ErrorBox message={error} />
        <Card>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2">
                <h1 className="text-2xl font-bold">{tech.name}</h1>
                {tech.verification_status === "verified" ? <VerifiedBadge /> : <StatusBadge status={tech.verification_status} />}
              </div>
              <Stars value={tech.avg_rating} count={tech.review_count} />
              <p className="text-sm text-slate-600 dark:text-slate-300">📍 {tech.city} · {tech.experience_years} yrs experience · visit charge {money(tech.base_rate)}</p>
            </div>
            {user?.role === "customer" && (
              <button className={btnSecondary} onClick={toggleSave}>{tech.is_saved ? "★ Saved to trusted list" : "☆ Save as trusted"}</button>
            )}
          </div>
          <p className="mt-4 text-slate-700 dark:text-slate-200">{tech.bio || "This technician hasn't added a bio yet."}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {tech.categories.map((c) => <span key={c.id} className="rounded-md bg-slate-100 dark:bg-slate-800 px-2 py-1 text-sm">{c.icon} {c.name}</span>)}
          </div>
          <p className="mt-4 text-sm">{tech.is_available ? <span className="text-emerald-600 dark:text-emerald-400">● Available for bookings</span> : <span className="text-slate-500 dark:text-slate-400">● Currently unavailable</span>}</p>
        </Card>

        <Card>
          <h2 className="mb-4 text-lg font-bold">Customer reviews</h2>
          {tech.reviews.length === 0 ? <Empty>No reviews yet.</Empty> : (
            <ul className="divide-y divide-slate-100 dark:divide-slate-800">
              {tech.reviews.map((r) => (
                <li key={r.id} className="py-3">
                  <div className="flex items-center justify-between"><Stars value={r.rating} /><span className="text-xs text-slate-400 dark:text-slate-500">{fmtDateTime(r.created_at)}</span></div>
                  {r.comment && <p className="mt-1 text-sm text-slate-700 dark:text-slate-200">{r.comment}</p>}
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">— {r.customer_name}</p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      {canBook && (
        <Card className="h-fit lg:sticky lg:top-20">
          <h2 className="mb-4 text-lg font-bold">Book {tech.name.split(" ")[0]}</h2>
          {booked ? <SuccessBox message="Request sent! Track it from your dashboard." /> :
            <BookingForm technician={tech} onBooked={() => setBooked(true)} />}
        </Card>
      )}
    </div>
  );
}
