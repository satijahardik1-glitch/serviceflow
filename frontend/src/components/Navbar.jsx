import { useEffect, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { dashboardPath, useAuth } from "../context/AuthContext.jsx";
import ThemeToggle from "./ThemeToggle.jsx";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [location.pathname]); // close the mobile menu after navigating

  const link = ({ isActive }) =>
    `text-sm font-medium ${isActive ? "text-indigo-600 dark:text-indigo-400" : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"}`;
  const doLogout = () => { logout(); navigate("/"); };

  const links = (
    <>
      <NavLink to="/technicians" className={link}>Find technicians</NavLink>
      {(!user || user.role === "customer") && <NavLink to="/book" className={link}>Book a service</NavLink>}
      {user ? (
        <>
          <NavLink to={dashboardPath(user.role)} className={link}>Dashboard</NavLink>
          <span className="text-sm text-slate-500 dark:text-slate-400">Hi, {user.name.split(" ")[0]}</span>
          <button onClick={doLogout} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800">Log out</button>
        </>
      ) : (
        <>
          <NavLink to="/login" className={link}>Log in</NavLink>
          <Link to="/register" className="rounded-lg bg-indigo-600 px-3 py-1.5 text-center text-sm font-semibold text-white hover:bg-indigo-700">Sign up</Link>
        </>
      )}
    </>
  );

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur dark:border-slate-800 dark:bg-slate-900/90">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-xl font-extrabold text-indigo-600 dark:text-indigo-400">Service<span className="text-slate-900 dark:text-white">Flow</span></Link>

        {/* Desktop */}
        <nav className="hidden items-center gap-5 md:flex">
          {links}
          <ThemeToggle />
        </nav>

        {/* Mobile */}
        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          <button type="button" aria-label="Menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-300 text-lg hover:bg-slate-100 dark:border-slate-600 dark:hover:bg-slate-800">
            <span aria-hidden="true">{open ? "✕" : "☰"}</span>
          </button>
        </div>
      </div>
      {open && <nav className="flex flex-col gap-4 border-t border-slate-200 px-4 py-4 dark:border-slate-800 md:hidden">{links}</nav>}
    </header>
  );
}
