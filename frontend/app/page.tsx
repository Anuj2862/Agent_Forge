import TaskSubmitForm from "@/components/TaskSubmitForm";

const features = [
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        <path d="M2 12h20"/>
      </svg>
    ),
    color: "#818cf8",
    bg: "rgba(99,102,241,0.08)",
    border: "rgba(99,102,241,0.18)",
    title: "Dynamic Synthesis",
    desc: "Meta Controller converts natural language into structured subtasks and synthesizes specialized agents on the fly.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
      </svg>
    ),
    color: "#38bdf8",
    bg: "rgba(6,182,212,0.08)",
    border: "rgba(6,182,212,0.18)",
    title: "Graph Execution",
    desc: "Executes the dynamically generated architecture via LangGraph — handling state, tool calls, and parallel workflows.",
  },
  {
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    color: "#34d399",
    bg: "rgba(16,185,129,0.08)",
    border: "rgba(16,185,129,0.18)",
    title: "Evolution Memory",
    desc: "Evaluates outputs, diagnoses architectural gaps, and persists experience to improve future synthesis automatically.",
  },
];

export default function Home() {
  return (
    <div style={{ maxWidth: 860, margin: "0 auto", padding: "64px 24px 80px" }}>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <div className="fade-up" style={{ textAlign: "center", marginBottom: 56 }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 7,
            background: "rgba(99,102,241,0.1)",
            border: "1px solid rgba(99,102,241,0.22)",
            borderRadius: 99,
            padding: "4px 14px",
            marginBottom: 28,
          }}
        >
          <div className="status-dot live" style={{ width: 6, height: 6 }} />
          <span style={{ fontSize: 11, fontWeight: 600, color: "#818cf8", letterSpacing: ".08em", textTransform: "uppercase" }}>
            Member 4 · Evolution Memory & API
          </span>
        </div>

        <h1
          style={{
            fontSize: "clamp(2rem, 5vw, 3.25rem)",
            fontWeight: 900,
            lineHeight: 1.1,
            letterSpacing: "-0.03em",
            marginBottom: 20,
          }}
        >
          Autonomous{" "}
          <span className="gradient-text">Multi-Agent</span>
          <br />
          Architecture Forge
        </h1>

        <p
          style={{
            fontSize: 16,
            color: "var(--text-secondary)",
            lineHeight: 1.7,
            maxWidth: 560,
            margin: "0 auto",
          }}
        >
          Describe a task. Agent Forge synthesizes a specialized team of AI agents,
          executes them, evaluates the results, and evolves the architecture over time.
        </p>
      </div>

      {/* ── Submit Form ─────────────────────────────────────────── */}
      <div className="fade-up delay-1" style={{ marginBottom: 56 }}>
        <TaskSubmitForm />
      </div>

      {/* ── Divider ─────────────────────────────────────────────── */}
      <div className="fade-up delay-2" style={{ marginBottom: 40 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <hr className="divider" style={{ flex: 1 }} />
          <span className="section-label">How it works</span>
          <hr className="divider" style={{ flex: 1 }} />
        </div>
      </div>

      {/* ── Feature Cards ───────────────────────────────────────── */}
      <div
        className="fade-up delay-3"
        style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 16 }}
      >
        {features.map((f, i) => (
          <div
            key={i}
            className="card"
            style={{ padding: "22px 22px 24px" }}
          >
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 10,
                background: f.bg,
                border: `1px solid ${f.border}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: f.color,
                marginBottom: 16,
              }}
            >
              {f.icon}
            </div>
            <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 8, color: "var(--text-primary)" }}>
              {f.title}
            </h3>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.65 }}>{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
