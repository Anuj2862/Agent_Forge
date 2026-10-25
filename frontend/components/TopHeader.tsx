"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { toggleTheme, useTheme } from "@/lib/theme";

const WORKFLOW_STAGES = [
  { href: "/compose", label: "Compose", num: "1" },
  { href: "/architecture", label: "Architecture", num: "2" },
  { href: "/execution", label: "Execute", num: "3" },
  { href: "/evaluation", label: "Evaluate", num: "4" },
  { href: "/evolution", label: "Evolve", num: "5" },
];

export default function TopHeader() {
  const pathname = usePathname();
  const theme = useTheme();

  const isRunRoute = pathname.startsWith("/run/");
  const currentTaskId = isRunRoute ? pathname.replace("/run/", "").split("?")[0] : null;

  return (
    <header
      className="top-header"
      role="banner"
      style={{
        background: "var(--bg-header)",
        backdropFilter: "blur(8px)",
        WebkitBackdropFilter: "blur(8px)",
        borderBottom: "1px solid var(--border)",
      }}
    >
      {/* Left: Breadcrumbs & Research Context */}
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <nav aria-label="Breadcrumb" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
          <Link
            href="/"
            style={{
              color: "var(--text-secondary)",
              textDecoration: "none",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: 6,
              transition: "color 0.15s",
            }}
            onMouseOver={(e) => (e.currentTarget.style.color = "var(--text-primary)")}
            onMouseOut={(e) => (e.currentTarget.style.color = "var(--text-secondary)")}
          >
            <span style={{ color: "var(--blue-primary)" }}>◈</span>
            Workspace
          </Link>

          {isRunRoute && currentTaskId && (
            <>
              <span style={{ color: "var(--border-strong)" }}>/</span>
              <span
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  fontSize: 12,
                  color: "var(--blue-primary)",
                  background: "rgba(37, 99, 235, 0.1)",
                  padding: "2px 8px",
                  borderRadius: 6,
                  border: "1px solid var(--border)",
                }}
              >
                {currentTaskId}
              </span>
            </>
          )}
        </nav>

        {/* Workflow Lifecycle Steps */}
        <div
          className="hidden md:flex"
          style={{
            alignItems: "center",
            gap: 4,
            marginLeft: 12,
            padding: "3px 8px",
            background: "var(--bg-card-subtle)",
            border: "1px solid var(--border)",
            borderRadius: 8,
          }}
        >
          {WORKFLOW_STAGES.map((st, idx) => {
            const isCurrent =
              pathname === st.href ||
              (st.href === "/execution" && isRunRoute);
            return (
              <div key={st.href} style={{ display: "flex", alignItems: "center" }}>
                <Link
                  href={st.href}
                  style={{
                    fontSize: 11,
                    fontWeight: isCurrent ? 700 : 500,
                    color: isCurrent ? "var(--blue-primary)" : "var(--text-muted)",
                    textDecoration: "none",
                    padding: "2px 8px",
                    borderRadius: 5,
                    background: isCurrent ? "rgba(37, 99, 235, 0.12)" : "transparent",
                    transition: "all 0.15s",
                  }}
                >
                  <span style={{ opacity: 0.6, marginRight: 3, fontFamily: "'JetBrains Mono', monospace" }}>
                    {st.num}.
                  </span>
                  {st.label}
                </Link>
                {idx < WORKFLOW_STAGES.length - 1 && (
                  <span style={{ color: "var(--border-strong)", fontSize: 10, margin: "0 2px" }}>
                    →
                  </span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Right: Theme Toggle & Primary Action */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {/* Light / Dark Mode Toggle */}
        <button
          id="theme-toggle-btn"
          data-testid="theme-toggle-btn"
          onClick={() => {
            toggleTheme();
          }}
          aria-label={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
          title={theme === "light" ? "Switch to Dark Mode" : "Switch to Light Mode"}
          style={{
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "var(--bg-card-subtle)",
            border: "1px solid var(--border)",
            color: "var(--text-secondary)",
            cursor: "pointer",
            transition: "all 0.15s ease",
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.color = "var(--text-primary)";
            e.currentTarget.style.borderColor = "var(--border-strong)";
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.color = "var(--text-secondary)";
            e.currentTarget.style.borderColor = "var(--border)";
          }}
        >
          {theme === "light" ? (
            /* Moon icon when in light mode to switch to dark */
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            /* Sun icon when in dark mode to switch to light */
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          )}
        </button>

        {/* Quick Launch Button */}
        <Link
          href="/compose"
          className="btn btn-primary btn-sm"
          style={{ fontSize: 12, padding: "5px 12px" }}
        >
          + Compose Task
        </Link>
      </div>
    </header>
  );
}
