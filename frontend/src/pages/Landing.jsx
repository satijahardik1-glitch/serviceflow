import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../api.js";
import { Spinner, btnPrimary, btnSecondary } from "../components/ui.jsx";

const STEPS = [
  ["1", "Describe the problem", "Pick a service and symptoms - our diagnosis engine shows the likely cause, time and a transparent price range."],
  ["2", "Choose a verified pro", "We rank ID-verified technicians by skill, availability, distance and customer ratings."],
  ["3", "Book & track", "Send a request, follow its status in real time and rate the job when it's done."],
];

const WHY = [
  ["🛡️", "Background verified", "Every technician submits an ID that an admin reviews before they can appear in search."],
  ["💰", "Upfront pricing", "See a price range and time estimate before you book - no surprises on the day."],
  ["⭐", "Real reviews", "Only customers with a completed job can leave a rating, so scores stay honest."],
  ["🎯", "Smart matching", "Technicians are scored on skill, availability, city and past ratings for the best fit."],
];

export default function Landing() {
  const [categories, setCategories] = useState(null);
  useEffect(() => { api.get("/services/categories").then((r) => setCategories(r.data)).catch(() => setCategories([])); }, []);

  return (
    <div className="space-y-16">
      <section className="rounded-3xl bg-gradient-to-br from-indigo-600 to-violet-700 px-8 py-16 text-center text-white shadow-lg dark:from-indigo-700 dark:to-violet-900 dark:shadow-indigo-950/50">
        <h1 className="mx-auto max-w-3xl text-4xl font-extrabold leading-tight sm:text-5xl">Trusted technicians for every home repair</h1>
        <p className="mx-auto mt-4 max-w-2xl text-lg text-indigo-100">
          Electricians, plumbers, AC and carpentry experts - background-verified, rated by real customers and priced upfront.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link to="/book" className={`${btnPrimary} !bg-white !text-indigo-700 hover:!bg-indigo-50`}>Get a free estimate</Link>
          <Link to="/register" className={`${btnSecondary} !border-white/40 !bg-transparent !text-white hover:!bg-white/10`}>Join as a technician</Link>
        </div>
      </section>

      <section>
        <h2 className="mb-6 text-2xl font-bold">Popular services</h2>
        {!categories ? <Spinner label="Loading services…" /> : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {categories.map((c) => (
              <Link key={c.id} to={`/book?category=${c.id}`} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-700 dark:bg-slate-900 dark:hover:border-indigo-500/50">
                <div className="text-3xl">{c.icon}</div>
                <h3 className="mt-3 font-bold">{c.name}</h3>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{c.description}</p>
              </Link>
            ))}
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-6 text-2xl font-bold">How it works</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {STEPS.map(([n, title, text]) => (
            <div key={n} className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 font-bold text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">{n}</span>
              <h3 className="mt-3 font-bold">{title}</h3>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-6 text-2xl font-bold">Why ServiceFlow</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {WHY.map(([icon, title, text]) => (
            <div key={title} className="rounded-xl bg-slate-100 p-5 dark:bg-slate-800/60">
              <div className="text-2xl" aria-hidden="true">{icon}</div>
              <h3 className="mt-2 font-bold">{title}</h3>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{text}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-3xl border border-slate-200 bg-white px-8 py-12 text-center dark:border-slate-700 dark:bg-slate-900">
        <h2 className="text-2xl font-bold">Ready to get it fixed?</h2>
        <p className="mx-auto mt-2 max-w-xl text-slate-600 dark:text-slate-300">Get a diagnosis and price range in under a minute - no account needed to explore.</p>
        <Link to="/book" className={`${btnPrimary} mt-6`}>Book a service</Link>
      </section>
    </div>
  );
}
