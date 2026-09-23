"use client";

import { usePathname } from "next/navigation";

const PAGE_META: Record<string, { title: string; subtitle: string }> = {
  "/": {
    title: "Autonomous Multi-Agent Architecture Laboratory",
    subtitle: "Design. Execute. Diagnose. Evolve. Remember.",
  },
  "/history": {
    title: "Evolution Memory History",
    subtitle: "Persistent record of all executed architectures and their evaluation outcomes.",
  },
  "/architecture": {
    title: "Architecture Viewer",
    subtitle: "Inspect and explore generated multi-agent architectures.",
  },
  "/execution": {
    title: "Execution Engine",
    subtitle: "Live logs and state from the LangGraph execution pipeline.",
  },
  "/evaluation": {
    title: "Evaluation Dashboard",
    subtitle: "Quality scores, factual accuracy, and task success metrics.",
  },
  "/diagnosis": {
    title: "Diagnosis & Reflection",
    subtitle: "Root-cause analysis and architectural improvement suggestions.",
  },
  "/evolution": {
    title: "Evolution Tracker",
    subtitle: "Track how architectures improve across successive runs.",
  },
  "/memory": {
    title: "Memory Store",
    subtitle: "Retrieve past architectures to inform future synthesis.",
  },
  "/settings": {
    title: "Settings",
    subtitle: "Configure your Agent Forge environment and preferences.",
  },
};

export default function TopHeader() {
  const pathname = usePathname();

  // Match /run/[id] pages
  const meta =
    PAGE_META[pathname] ??
    (pathname.startsWith("/run/")
      ? { title: "Run Dashboard", subtitle: "Live architecture execution, evaluation, and evolution." }
      : { title: "Agent Forge", subtitle: "Autonomous Multi-Agent Architecture Laboratory" });

  return (
    <header className="top-header">
      {/* Left: titles */}
      <div className="top-header-titles">
        <div className="top-header-title">{meta.title}</div>
        <div className="top-header-subtitle">{meta.subtitle}</div>
      </div>

      {/* Right: quote + user */}
      <div className="top-header-right">
        {/* AI quote chip */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "5px 12px",
            borderRadius: 8,
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.06)",
            maxWidth: 240,
          }}
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
          </svg>
          <span style={{ fontSize: 10, color: "var(--text-muted)", lineHeight: 1.4, fontStyle: "italic" }}>
            &ldquo;Better Agent Architectures Through Continuous Learning.&rdquo;
          </span>
        </div>

        {/* User chip */}
        <div className="top-header-user">
          <div className="top-header-avatar">AG</div>
          <span className="top-header-username">Anuj Gardi</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ color: "var(--text-muted)" }}>
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>

        {/* Settings icon */}
        <button
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: "rgba(255,255,255,0.04)",
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            color: "var(--text-muted)",
            transition: "all 0.15s",
            flexShrink: 0,
          }}
          onMouseOver={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.08)";
            (e.currentTarget as HTMLElement).style.color = "var(--text-secondary)";
          }}
          onMouseOut={(e) => {
            (e.currentTarget as HTMLElement).style.background = "rgba(255,255,255,0.04)";
            (e.currentTarget as HTMLElement).style.color = "var(--text-muted)";
          }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 1.414 14.142M4.929 19.07A10 10 0 0 1 3.515 4.929M19.07 19.07a10 10 0 0 1-14.142 0M4.929 4.929a10 10 0 0 1 14.142 0"/>
          </svg>
        </button>
      </div>
    </header>
  );
}
