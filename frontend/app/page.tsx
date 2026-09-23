import TaskSubmitForm from "@/components/TaskSubmitForm";

const PIPELINE_STEPS = [
  { num: 1, label: "Task\nInput",          status: "done" },
  { num: 2, label: "Architecture\nSynthesis", status: "active" },
  { num: 3, label: "Agent\nExecution",     status: "pending" },
  { num: 4, label: "Evaluation",           status: "pending" },
  { num: 5, label: "Diagnosis",            status: "pending" },
  { num: 6, label: "Evolution",            status: "pending" },
  { num: 7, label: "Memory",               status: "pending" },
];

const CAPABILITIES = [
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        <path d="M2 12h20"/>
      </svg>
    ),
    color: "#818cf8",
    bg: "rgba(99,102,241,0.09)",
    border: "rgba(99,102,241,0.18)",
    title: "Dynamic Synthesis",
    desc: "Meta Controller converts natural language into structured subtasks and synthesizes specialized agents on the fly.",
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>
      </svg>
    ),
    color: "#38bdf8",
    bg: "rgba(6,182,212,0.09)",
    border: "rgba(6,182,212,0.18)",
    title: "Graph Execution",
    desc: "Executes the dynamically generated architecture via LangGraph — handling state, tool calls, and parallel workflows.",
  },
  {
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
    ),
    color: "#34d399",
    bg: "rgba(16,185,129,0.09)",
    border: "rgba(16,185,129,0.18)",
    title: "Evolution Memory",
    desc: "Evaluates outputs, diagnoses architectural gaps, and persists experience to improve future synthesis automatically.",
  },
];

export default function Home() {
  return (
    <div style={{ maxWidth: 1100, margin: "0 auto" }}>

      {/* ── Page intro ────────────────────────────────────────── */}
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 6,
              padding: "3px 12px",
              borderRadius: 99,
              background: "rgba(16,185,129,0.1)",
              border: "1px solid rgba(16,185,129,0.2)",
            }}
          >
            <div className="status-dot live" style={{ width: 6, height: 6 }} />
            <span style={{ fontSize: 10, fontWeight: 700, color: "#34d399", letterSpacing: "0.1em", textTransform: "uppercase" }}>
              Autonomous Engine Ready
            </span>
          </div>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Member 4 · Evolution Memory &amp; API Layer
          </span>
        </div>
        <h1
          style={{
            fontSize: "clamp(1.6rem, 3.5vw, 2.4rem)",
            fontWeight: 900,
            letterSpacing: "-0.035em",
            lineHeight: 1.1,
            marginBottom: 8,
          }}
        >
          Describe your task and let{" "}
          <span className="shimmer-text">Agent Forge</span>
          {" "}design the architecture.
        </h1>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.7, maxWidth: 620 }}>
          Enter a natural language task and let Agent Forge design, execute, diagnose, and evolve the best multi-agent architecture.
        </p>
      </div>

      {/* ── Task Input Form ───────────────────────────────────── */}
      <div className="fade-up delay-1" style={{ marginBottom: 24 }}>
        <TaskSubmitForm />
      </div>

      {/* ── Pipeline Stepper ──────────────────────────────────── */}
      <div className="fade-up delay-2" style={{ marginBottom: 36 }}>
        <div
          className="card"
          style={{ padding: "16px 24px" }}
        >
          <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--text-muted)", marginBottom: 14 }}>
            Execution Pipeline
          </div>
          <div className="stepper">
            {PIPELINE_STEPS.map((step, i) => (
              <div key={step.num} className="step-item">
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                  <div className={`step-bubble ${step.status}`}>
                    {step.status === "done" ? (
                      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                    ) : step.num}
                  </div>
                  <div className={`step-label ${step.status}`} style={{ maxWidth: 70, textAlign: "center", lineHeight: 1.3 }}>
                    {step.label.split("\n").map((l, li) => (
                      <span key={li} style={{ display: "block" }}>{l}</span>
                    ))}
                  </div>
                </div>
                {i < PIPELINE_STEPS.length - 1 && (
                  <div className={`step-connector ${i === 0 ? "done" : "pending"}`} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── How it works ──────────────────────────────────────── */}
      <div className="fade-up delay-3">
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
          <hr className="divider" style={{ flex: 1 }} />
          <span className="section-label">How it works</span>
          <hr className="divider" style={{ flex: 1 }} />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 14 }}>
          {CAPABILITIES.map((cap, i) => (
            <div
              key={i}
              className="card"
              style={{ padding: "20px 22px" }}
            >
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 9,
                  background: cap.bg,
                  border: `1px solid ${cap.border}`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: cap.color,
                  marginBottom: 14,
                  flexShrink: 0,
                }}
              >
                {cap.icon}
              </div>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 7, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
                {cap.title}
              </h3>
              <p style={{ fontSize: 12.5, color: "var(--text-secondary)", lineHeight: 1.65 }}>
                {cap.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
