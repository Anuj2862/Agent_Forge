import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Agent Forge — Autonomous Multi-Agent Evolution Platform",
  description:
    "Submit tasks and watch Agent Forge dynamically synthesize multi-agent architectures, execute them, evaluate results, reflect, and evolve — improving with every run.",
};

function NavBar() {
  return (
    <nav
      style={{
        background: "rgba(10, 14, 26, 0.9)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid #1e2d45",
        padding: "12px 24px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <Link href="/" style={{ textDecoration: "none" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 16,
              fontWeight: 800,
              color: "white",
            }}
          >
            AF
          </div>
          <span
            className="gradient-text"
            style={{ fontSize: 18, fontWeight: 700 }}
          >
            Agent Forge
          </span>
        </div>
      </Link>

      <div style={{ display: "flex", gap: "4px" }}>
        {[
          { href: "/", label: "Dashboard" },
          { href: "/history", label: "Evolution History" },
        ].map(({ href, label }) => (
          <Link
            key={href}
            href={href}
            style={{
              color: "#94a3b8",
              textDecoration: "none",
              padding: "6px 14px",
              borderRadius: 6,
              fontSize: 14,
              fontWeight: 500,
              transition: "color 0.2s, background 0.2s",
            }}
            onMouseEnter={(e) => {
              (e.target as HTMLAnchorElement).style.color = "#e2e8f0";
              (e.target as HTMLAnchorElement).style.background = "#1e2d45";
            }}
            onMouseLeave={(e) => {
              (e.target as HTMLAnchorElement).style.color = "#94a3b8";
              (e.target as HTMLAnchorElement).style.background = "transparent";
            }}
          >
            {label}
          </Link>
        ))}
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: "50%",
            background: "#10b981",
            boxShadow: "0 0 6px #10b981",
          }}
        />
        <span style={{ fontSize: 12, color: "#64748b" }}>API Live</span>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.className}>
      <body>
        <NavBar />
        <main>{children}</main>
      </body>
    </html>
  );
}
