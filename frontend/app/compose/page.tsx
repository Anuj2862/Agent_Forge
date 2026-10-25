"use client";

import TaskSubmitForm from "@/components/TaskSubmitForm";

export default function ComposePage() {
  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", flexDirection: "column", gap: 24 }}>
      {/* ── Page Header ─────────────────────────────────────────── */}
      <div className="fade-up">
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "3px 12px",
              borderRadius: 99,
              background: "rgba(37, 99, 235, 0.12)",
              border: "1px solid rgba(56, 189, 248, 0.3)",
            }}
          >
            <span style={{ fontSize: 11, fontWeight: 700, color: "#60A5FA", letterSpacing: "0.06em", textTransform: "uppercase" }}>
              Synthesis Studio
            </span>
          </div>
          <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
            Constraint-Governed Architectural Planner
          </span>
        </div>

        <h1
          style={{
            fontSize: "clamp(1.5rem, 2.5vw, 2.1rem)",
            fontWeight: 800,
            letterSpacing: "-0.025em",
            lineHeight: 1.25,
            color: "var(--text-primary)",
            marginBottom: 6,
          }}
        >
          Compose New Research Task
        </h1>
        <p style={{ fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.55, maxWidth: 780 }}>
          Specify your task description and enforce operational boundaries. The Meta Controller will parse required capabilities,
          query evolutionary memory for proven topology patterns, and synthesize an initial Architecture V1.
        </p>
      </div>

      {/* ── Main Form Container ─────────────────────────────────── */}
      <div className="fade-up delay-1">
        <TaskSubmitForm />
      </div>

      {/* ── Operational Guidance & Constraint Reference ─────────── */}
      <div
        className="card fade-up delay-2"
        style={{
          padding: "20px 24px",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: 20,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ color: "#22D3EE", fontSize: 15 }}>🛡️</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              Hard Constraint Invariance
            </span>
          </div>
          <p style={{ fontSize: 12.5, color: "var(--text-secondary)", lineHeight: 1.55 }}>
            Limits on agent counts (<code className="mono" style={{ color: "#22D3EE" }}>max_agents</code>) and forbidden tool sets (<code className="mono" style={{ color: "#F87171" }}>forbidden_tools</code>) are inviolable. Any mutated candidate architecture that breaches them is immediately rejected at the decision gate.
          </p>
        </div>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ color: "#34D399", fontSize: 15 }}>⚖️</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              Automated Self-Evolution
            </span>
          </div>
          <p style={{ fontSize: 12.5, color: "var(--text-secondary)", lineHeight: 1.55 }}>
            Submitting with the automated pipeline active dispatches Run 1, evaluates factual accuracy, diagnoses deficiencies, synthesizes candidate mutations (e.g. adding a Verification Specialist), and executes Run 2 for empirical comparison.
          </p>
        </div>

        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ color: "#A78BFA", fontSize: 15 }}>🧠</span>
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              Experiential Memory Transfer
            </span>
          </div>
          <p style={{ fontSize: 12.5, color: "var(--text-secondary)", lineHeight: 1.55 }}>
            The framework continuously queries past accepted architecture records from SQLite to seed the initial topology, ensuring previously identified failure modes are not repeated across similar tasks.
          </p>
        </div>
      </div>
    </div>
  );
}
