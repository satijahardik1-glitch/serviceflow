import { useEffect } from "react";
import { Link, Route, Routes, useLocation } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import AdminDashboard from "./pages/AdminDashboard.jsx";
import BookService from "./pages/BookService.jsx";
import CustomerDashboard from "./pages/CustomerDashboard.jsx";
import Landing from "./pages/Landing.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import TechnicianDashboard from "./pages/TechnicianDashboard.jsx";
import TechnicianProfile from "./pages/TechnicianProfile.jsx";
import Technicians from "./pages/Technicians.jsx";

// Start every page at the top and give each route a meaningful browser-tab title
const TITLES = { "/": "", "/login": "Log in", "/register": "Sign up", "/book": "Book a service", "/technicians": "Find technicians",
  "/customer": "My dashboard", "/technician": "Technician dashboard", "/admin": "Admin panel" };
function RouteEffects() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
    const t = TITLES[pathname] ?? (pathname.startsWith("/technicians/") ? "Technician profile" : "Page not found");
    document.title = t ? `${t} · ServiceFlow` : "ServiceFlow – Trusted Technician Marketplace";
  }, [pathname]);
  return null;
}

const NotFound = () => (
  <div className="py-24 text-center">
    <h1 className="text-3xl font-bold">Page not found</h1>
    <Link to="/" className="mt-4 inline-block text-indigo-600 dark:text-indigo-400 hover:underline">Back to home</Link>
  </div>
);

export default function App() {
  return (
    <div className="min-h-screen">
      <RouteEffects />
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/book" element={<BookService />} />
          <Route path="/technicians" element={<Technicians />} />
          <Route path="/technicians/:id" element={<TechnicianProfile />} />
          <Route path="/customer" element={<ProtectedRoute roles={["customer"]}><CustomerDashboard /></ProtectedRoute>} />
          <Route path="/technician" element={<ProtectedRoute roles={["technician"]}><TechnicianDashboard /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute roles={["admin"]}><AdminDashboard /></ProtectedRoute>} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <footer className="border-t border-slate-200 dark:border-slate-800 py-6 text-center text-sm text-slate-500 dark:text-slate-400">© {new Date().getFullYear()} ServiceFlow – Trusted Technician Marketplace</footer>
    </div>
  );
}
