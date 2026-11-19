import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "/api" });

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem("sf_token");
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const isAuthCall = err.config?.url?.startsWith("/auth/login") || err.config?.url?.startsWith("/auth/register");
    if (err.response?.status === 401 && !isAuthCall && localStorage.getItem("sf_token")) {
      localStorage.removeItem("sf_token");
      localStorage.removeItem("sf_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export const errMsg = (e) => {
  const d = e?.response?.data?.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((x) => x.msg?.replace(/^Value error, /, "")).join("; ");
  if (e?.code === "ERR_NETWORK") return "Cannot reach the server. Is the backend running?";
  return e?.message || "Something went wrong";
};

export default api;
