"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navSections = [
  {
    label: "Workspace Command",
    items: [
      {
        href: "/",
        label: "Overview",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1.5" />
            <rect x="14" y="3" width="7" height="7" rx="1.5" />
            <rect x="14" y="14" width="7" height="7" rx="1.5" />
            <rect x="3" y="14" width="7" height="7" rx="1.5" />
          </svg>
        ),
      },
      {
        href: "/compose",
        label: "Compose Task",
        isNewTask: true,
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        ),
      },
    ],
  },
  {
    label: "Research Lifecycle",
    items: [
      {
        href: "/architecture",
        label: "Architecture Studio",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="5" r="3" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <circle cx="6" cy="19" r="3" />
            <circle cx="18" cy="19" r="3" />
            <line x1="8.5" y1="17.5" x2="10.5" y2="13.5" />
            <line x1="15.5" y1="17.5" x2="13.5" y2="13.5" />
          </svg>
        ),
      },
      {
        href: "/execution",
        label: "Live Execution",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
        ),
      },
      {
        href: "/evaluation",
        label: "Evaluate",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
        ),
      },
      {
        href: "/diagnosis",
        label: "Failure Diagnosis",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        ),
      },
      {
        href: "/evolution",
        label: "Evolve",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2v6h-6" />
            <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
            <path d="M3 22v-6h6" />
            <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
          </svg>
        ),
      },
    ],
  },
  {
    label: "Empirical Memory",
    items: [
      {
        href: "/history",
        label: "Experiments & History",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 20v-6M6 20V10M18 20V4" />
          </svg>
        ),
      },
      {
        href: "/memory",
        label: "Memory & Knowledge",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
            <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
          </svg>
        ),
      },
    ],
  },
  {
    label: "Platform",
    items: [
      {
        href: "/settings",
        label: "Settings",
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.07 4.93a10 10 0 0 1 1.414 14.142M4.929 19.07A10 10 0 0 1 3.515 4.929M19.07 19.07a10 10 0 0 1-14.142 0M4.929 4.929a10 10 0 0 1 14.142 0" />
          </svg>
        ),
      },
    ],
  },
];

export default function SideBar() {
  const pathname = usePathname();

  return (
    <aside
      className="sidebar"
      aria-label="Main Navigation"
      style={{
        background: "var(--bg-sidebar)",
        backdropFilter: "blur(6px)",
        WebkitBackdropFilter: "blur(6px)",
        borderRight: "1px solid var(--border)",
      }}
    >
      {/* Logo & Platform Identity */}
      <div className="sidebar-logo">
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 12 }}>
          <div
            className="sidebar-logo-icon"
            style={{
              position: "relative",
              width: 48,
              height: 48,
              borderRadius: 12,
              overflow: "hidden",
              boxShadow: "0 0 20px rgba(37, 99, 235, 0.45), 0 0 10px rgba(34, 211, 238, 0.35)",
              border: "1px solid rgba(34, 211, 238, 0.4)",
              flexShrink: 0,
              background: "#030712",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Image
              src="/logo.png"
              alt="Agent Forge Logo"
              width={48}
              height={48}
              priority
              style={{ objectFit: "cover", width: "100%", height: "100%" }}
            />
          </div>
          <div className="sidebar-logo-text">
            <div className="sidebar-logo-title" style={{ color: "var(--text-primary)", fontSize: 15.5, fontWeight: 800, letterSpacing: "-0.015em", lineHeight: 1.2 }}>
              Agent Forge
            </div>
            <div
              className="sidebar-logo-sub"
              style={{
                color: "var(--text-muted)",
                fontSize: 9.5,
                fontWeight: 600,
                letterSpacing: "0.07em",
                textTransform: "uppercase",
                marginTop: 2,
              }}
            >
              Build • Experiment • Evolve
            </div>
          </div>
        </Link>
      </div>

      {/* Navigation Sections */}
      <nav className="sidebar-nav">
        {navSections.map((section, si) => (
          <div key={si}>
            {section.label && (
              <div className="sidebar-section-label">{section.label}</div>
            )}
            {section.items.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname.startsWith(item.href + "/");
              const isNewTask = "isNewTask" in item && item.isNewTask;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "sidebar-nav-item",
                    isActive && !isNewTask ? "active" : "",
                    isNewTask ? "new-task" : "",
                  ].filter(Boolean).join(" ")}
                  style={{
                    textDecoration: "none",
                    ...(isActive && !isNewTask
                      ? {
                          background: "rgba(37, 99, 235, 0.15)",
                          borderColor: "rgba(34, 211, 238, 0.35)",
                          color: "var(--text-primary)",
                        }
                      : {}),
                  }}
                  aria-current={isActive ? "page" : undefined}
                >
                  <span style={{ flexShrink: 0, display: "flex", alignItems: "center" }}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Footer status */}
      <div className="sidebar-footer" style={{ background: "var(--bg-sidebar)", borderTop: "1px solid var(--border)" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-primary)" }}>
            SQLite ACID Store
          </span>
          <span style={{ fontSize: 9, color: "var(--text-muted)", letterSpacing: "0.04em" }}>
            Self-Evolution Engine
          </span>
        </div>
      </div>
    </aside>
  );
}
