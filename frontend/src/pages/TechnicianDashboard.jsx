import { useCallback, useEffect, useState } from "react";
import api, { errMsg } from "../api.js";
import BookingCard from "../components/BookingCard.jsx";
import Tabs from "../components/Tabs.jsx";
import { Card, Empty, ErrorBox, Field, Spinner, Stars, StatusBadge, SuccessBox, btnPrimary, btnSecondary, inputCls } from "../components/ui.jsx";

const BANNERS = {
  pending: ["bg-amber-50 dark:bg-amber-500/10 border-amber-200 dark:border-amber-500/30 text-amber-800 dark:text-amber-300", "Your profile is awaiting admin verification. Submit your ID details below - you'll appear in search once verified."],
  verified: ["bg-emerald-50 dark:bg-emerald-500/10 border-emerald-200 dark:border-emerald-500/30 text-emerald-800 dark:text-emerald-300", "You're verified. Customers can now find and book you."],
  rejected: ["bg-rose-50 dark:bg-rose-500/10 border-rose-200 dark:border-rose-500/30 text-rose-800 dark:text-rose-300", "Your verification was rejected. Update your ID details to resubmit for review."],
};

export default function TechnicianDashboard() {
  const [tab, setTab] = useState("requests");
  const [profile, setProfile] = useState(null);
  const [bookings, setBookings] = useState(null);
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState(null);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState("");
  const [busy, setBusy] = useState(false);

  const applyProfile = (p) => {
    setProfile(p);
    setForm({
      bio: p.bio || "", city: p.city, phone: p.phone || "", base_rate: p.base_rate, experience_years: p.experience_years,
      category_ids: p.categories.map((c) => c.id), id_document_type: p.id_document_type || "Aadhaar", id_document_number: "",
    });
  };

  const load = useCallback(() => {
    api.get("/technicians/me").then((r) => applyProfile(r.data)).catch((e) => setError(errMsg(e)));
    api.get("/bookings/mine").then((r) => setBookings(r.data)).catch((e) => setError(errMsg(e)));
  }, []);
  useEffect(() => { load(); api.get("/services/categories").then((r) => setCategories(r.data)).catch(() => {}); }, [load]);

  const toggleAvailability = async () => {
    try { applyProfile((await api.patch("/technicians/me/availability", { is_available: !profile.is_available })).data); } catch (e) { setError(errMsg(e)); }
  };

  const saveProfile = async (e) => {
    e.preventDefault();
    setBusy(true); setError(""); setSaved("");
    try {
      const payload = { ...form, base_rate: Number(form.base_rate) || 0, experience_years: Number(form.experience_years) || 0 };
      if (!payload.id_document_number.trim()) delete payload.id_document_number; // blank = keep the stored (encrypted) number
      applyProfile((await api.put("/technicians/me", payload)).data);
      setSaved("Profile saved.");
    } catch (err) { setError(errMsg(err)); } finally { setBusy(false); }
  };

  if (!profile || !form) return error ? <ErrorBox message={error} /> : <Spinner />;
  const [bannerCls, bannerText] = BANNERS[profile.verification_status];
  const pendingCount = bookings?.filter((b) => b.status === "pending").length || 0;
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const toggleCat = (id) => setForm((f) => ({ ...f, category_ids: f.category_ids.includes(id) ? f.category_ids.filter((x) => x !== id) : [...f.category_ids, id] }));

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">Technician dashboard</h1>
          <div className="mt-1 flex items-center gap-2"><StatusBadge status={profile.verification_status} /><Stars value={profile.avg_rating} count={profile.review_count} /></div>
        </div>
        <button onClick={toggleAvailability} className={profile.is_available ? btnPrimary : btnSecondary}>
          {profile.is_available ? "● Available - tap to go offline" : "○ Offline - tap to go available"}
        </button>
      </div>
      <div className={`rounded-lg border px-4 py-3 text-sm ${bannerCls}`}>
        {bannerText}{profile.verification_note && <div className="mt-1 font-medium">Admin note: {profile.verification_note}</div>}
      </div>
      <ErrorBox message={error} />
      <Tabs active={tab} onChange={setTab} tabs={[["requests", "Booking requests", pendingCount], ["profile", "Profile & verification"]]} />

      {tab === "requests" && (!bookings ? <Spinner /> : bookings.length === 0 ? <Empty>No booking requests yet.</Empty> :
        <div className="space-y-4">{bookings.map((b) => <BookingCard key={b.id} booking={b} role="technician" onChanged={load} />)}</div>)}

      {tab === "profile" && (
        <Card>
          <form onSubmit={saveProfile} className="space-y-4">
            <SuccessBox message={saved} />
            <div className="grid gap-4 sm:grid-cols-2">
              <Field label="City"><input required className={inputCls} value={form.city} onChange={set("city")} /></Field>
              <Field label="Phone"><input className={inputCls} value={form.phone} onChange={set("phone")} /></Field>
              <Field label="Visit charge (₹)"><input type="number" min="0" className={inputCls} value={form.base_rate} onChange={set("base_rate")} /></Field>
              <Field label="Years of experience"><input type="number" min="0" className={inputCls} value={form.experience_years} onChange={set("experience_years")} /></Field>
            </div>
            <Field label="Services you offer">
              <div className="flex flex-wrap gap-2">
                {categories.map((c) => (
                  <button type="button" key={c.id} onClick={() => toggleCat(c.id)}
                    className={`rounded-full border px-3 py-1 text-sm ${form.category_ids.includes(c.id) ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-300" : "border-slate-300 dark:border-slate-600"}`}>{c.icon} {c.name}</button>
                ))}
              </div>
            </Field>
            <Field label="Bio"><textarea rows={3} className={inputCls} value={form.bio} onChange={set("bio")} /></Field>
            <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 p-4">
              <h3 className="mb-3 font-semibold">Identity verification</h3>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="ID type">
                  <select className={inputCls} value={form.id_document_type} onChange={set("id_document_type")}>
                    {["Aadhaar", "PAN", "Driving Licence", "Voter ID", "Passport"].map((t) => <option key={t}>{t}</option>)}
                  </select>
                </Field>
                <Field label="ID number" hint={profile.id_document_number ? `Stored securely (${profile.id_document_number}). Leave blank to keep it.` : "Stored encrypted; only admins can view it."}>
                  <input className={inputCls} autoComplete="off" value={form.id_document_number} onChange={set("id_document_number")} placeholder={profile.id_document_number || ""} />
                </Field>
              </div>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">Changing ID details sends your profile back for admin review. Your full ID number is encrypted and visible only to admins.</p>
            </div>
            <button disabled={busy || form.category_ids.length === 0} className={btnPrimary}>{busy ? "Saving…" : "Save profile"}</button>
          </form>
        </Card>
      )}
    </div>
  );
}
