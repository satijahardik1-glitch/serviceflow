import { createContext, useCallback, useContext, useEffect, useState } from "react";
import api from "../api.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export const dashboardPath = (role) => ({ customer: "/customer", technician: "/technician", admin: "/admin" }[role] || "/");

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try { return JSON.parse(localStorage.getItem("sf_user")); } catch { return null; }
  });
  const [ready, setReady] = useState(!localStorage.getItem("sf_token"));

  const persist = useCallback((data) => {
    localStorage.setItem("sf_token", data.access_token);
    localStorage.setItem("sf_user", JSON.stringify(data.user));
    setUser(data.user);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("sf_token");
    localStorage.removeItem("sf_user");
    setUser(null);
  }, []);

  useEffect(() => {
    if (!localStorage.getItem("sf_token")) return;
    api.get("/auth/me")
      .then((r) => { setUser(r.data); localStorage.setItem("sf_user", JSON.stringify(r.data)); })
      .catch(() => {})
      .finally(() => setReady(true));
  }, []);

  const login = async (email, password) => persist((await api.post("/auth/login", { email, password })).data);
  const register = async (payload) => persist((await api.post("/auth/register", payload)).data);

  return <AuthContext.Provider value={{ user, ready, login, register, logout }}>{children}</AuthContext.Provider>;
}
