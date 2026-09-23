"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navSections = [
  {
    items: [
      {
        href: "/",
        label: "New Task",
        isNewTask: true,
        icon: (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
        ),
      },
    ],
  },
  {
    label: "Workspace",
    items: [
      {
        href: "/architecture",
        label: "Architecture",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
          </svg>
        ),
      },
      {
        href: "/execution",
        label: "Execution",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
        ),
      },
      {
        href: "/evaluation",
        label: "Evaluation",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        ),
      },
      {
        href: "/diagnosis",
        label: "Diagnosis",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
        ),
      },
      {
        href: "/evolution",
        label: "Evolution",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/>
          </svg>
        ),
      },
    ],
  },
  {
    label: "Data",
    items: [
      {
        href: "/memory",
        label: "Memory",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
          </svg>
        ),
      },
      {
        href: "/history",
        label: "History",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 20v-6M6 20V10M18 20V4"/>
          </svg>
        ),
      },
    ],
  },
  {
    label: "System",
    items: [
      {
        href: "/settings",
        label: "Settings",
        icon: (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 1.414 14.142M4.929 19.07A10 10 0 0 1 3.515 4.929M19.07 19.07a10 10 0 0 1-14.142 0M4.929 4.929a10 10 0 0 1 14.142 0"/>
          </svg>
        ),
      },
    ],
  },
];

export default function SideBar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10 }}>
          <div className="sidebar-logo-icon">AF</div>
          <div className="sidebar-logo-text">
            <div className="sidebar-logo-title">Agent Forge</div>
            <div className="sidebar-logo-sub">Architect · Execute · Evolve</div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {navSections.map((section, si) => (
          <div key={si}>
            {section.label && (
              <div className="sidebar-section-label">{section.label}</div>
            )}
            {section.items.map((item) => {
              const isActive = pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href));
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
                  style={{ textDecoration: "none" }}
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
      <div className="sidebar-footer">
        <div className="sidebar-status">
          <div className="status-dot live" />
          <div className="sidebar-status-text">
            <div className="sidebar-status-label">System Online</div>
            <div className="sidebar-status-sub">All Services Operational</div>
          </div>
        </div>
      </div>
    </aside>
  );
}
