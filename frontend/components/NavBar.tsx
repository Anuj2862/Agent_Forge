"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Dashboard" },
  { href: "/history", label: "Evolution History" },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <nav
      style={{
        background: "rgba(7,11,20,0.85)",
        backdropFilter: "blur(18px)",
        WebkitBackdropFilter: "blur(18px)",
        borderBottom: "1px solid rgba(30,45,69,0.8)",
        height: 60,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "0 28px",
        position: "sticky",
        top: 0,
        zIndex: 200,
      }}
    >
      {/* Logo */}
      <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10 }}>
        <div
          style={{
            width: 34,
            height: 34,
            borderRadius: 9,
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 13,
            fontWeight: 800,
            color: "#fff",
            letterSpacing: "-0.5px",
            flexShrink: 0,
          }}
        >
          AF
        </div>
        <span
          style={{
            fontSize: 16,
            fontWeight: 700,
            background: "linear-gradient(135deg, #818cf8, #c4b5fd)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
          }}
        >
          Agent Forge
        </span>
      </Link>

      {/* Nav Links */}
      <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
        {links.map(({ href, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              style={{
                padding: "6px 14px",
                borderRadius: 8,
                fontSize: 13,
                fontWeight: 500,
                textDecoration: "none",
                color: active ? "#e2e8f0" : "#64748b",
                background: active ? "rgba(99,102,241,0.12)" : "transparent",
                border: active ? "1px solid rgba(99,102,241,0.25)" : "1px solid transparent",
                transition: "all .15s",
              }}
            >
              {label}
            </Link>
          );
        })}
      </div>

      {/* Status indicator */}
      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
        <div className="status-dot live" />
        <span style={{ fontSize: 12, color: "#475569", fontWeight: 500 }}>Live</span>
      </div>
    </nav>
  );
}
