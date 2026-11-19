import { createContext, useCallback, useContext, useEffect, useState } from "react";

const ThemeContext = createContext(null);
export const useTheme = () => useContext(ThemeContext);

const KEY = "sf_theme";
const systemPrefersDark = () => window.matchMedia("(prefers-color-scheme: dark)").matches;
const stored = () => { try { return localStorage.getItem(KEY); } catch { return null; } };

export function ThemeProvider({ children }) {
  // The inline script in index.html already set the class; mirror it into state.
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);

  // Until the user makes an explicit choice, follow the operating-system setting live.
  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = (e) => { if (!stored()) setDark(e.matches); };
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  const toggle = useCallback(() => {
    setDark((d) => {
      try { localStorage.setItem(KEY, d ? "light" : "dark"); } catch { /* private mode: ignore */ }
      return !d;
    });
  }, []);

  return <ThemeContext.Provider value={{ dark, toggle, systemPrefersDark }}>{children}</ThemeContext.Provider>;
}
