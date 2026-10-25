"use client";

import { useSyncExternalStore } from "react";

export type Theme = "dark" | "light";

export const THEME_STORAGE_KEY = "agentforge_theme";

export function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY);
    if (saved === "light" || saved === "dark") return saved;
  } catch {
    // ignore
  }
  return "dark";
}

export const getStoredTheme = getInitialTheme;

export function applyTheme(theme: Theme): void {
  if (typeof document === "undefined") return;
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);
  if (theme === "light") {
    root.classList.add("light");
    root.classList.remove("dark");
  } else {
    root.classList.add("dark");
    root.classList.remove("light");
  }

  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // ignore
  }

  // Notify components like canvas backgrounds
  window.dispatchEvent(new CustomEvent("themechange", { detail: theme }));
}

export function toggleTheme(): Theme {
  if (typeof document === "undefined") return "dark";
  const current = document.documentElement.getAttribute("data-theme") === "light" ? "light" : "dark";
  const next: Theme = current === "light" ? "dark" : "light";
  applyTheme(next);
  return next;
}

export function subscribeTheme(callback: () => void): () => void {
  if (typeof window === "undefined") return () => {};
  window.addEventListener("themechange", callback);
  window.addEventListener("storage", callback);
  return () => {
    window.removeEventListener("themechange", callback);
    window.removeEventListener("storage", callback);
  };
}

export function getThemeSnapshot(): Theme {
  return getInitialTheme();
}

export function getServerSnapshot(): Theme {
  return "dark";
}

export function useTheme(): Theme {
  return useSyncExternalStore(subscribeTheme, getThemeSnapshot, getServerSnapshot);
}
