"use client";

import { EvolutionDecision } from "@/lib/api";

interface DecisionVerdictCardProps {
  decision: EvolutionDecision | null | undefined;
  hasRuns?: boolean;
}

const REASON_EXPLANATIONS: Record<string, { label: string; desc: string }> = {
  QUALITY_IMPROVEMENT: {
    label: "Quality Improvement",
    desc: "The mutated architecture demonstrated a statistically meaningful improvement in output quality or factual accuracy.",
  },
  VERIFICATION_ADDED: {
    label: "Verification Added",
    desc: "A dedicated factual verification stage was successfully integrated to corroborate claims without violating agent limits.",
  },
  MAX_AGENTS_EXCEEDED: {
    label: "Max Agents Exceeded",
    desc: "The candidate architecture violated the hard maximum agent budget constraint specified in the task contract.",
  },
  FORBIDDEN_TOOL_USED: {
    label: "Forbidden Tool Violation",
    desc: "The candidate architecture dispatched or registered an explicit forbidden tool, failing security policy.",
  },
  QUALITY_REGRESSION: {
    label: "Quality Regression",
    desc: "Candidate architecture degraded the composite quality or task success rate below the baseline threshold.",
  },
  ACCURACY_REGRESSION: {
    label: "Accuracy Regression",
    desc: "Factual corroboration accuracy dropped compared to the baseline run.",
  },
  INSUFFICIENT_IMPROVEMENT: {
    label: "Insufficient Delta",
    desc: "The empirical metric delta was negligible and does not justify the added graph complexity or latency.",
  },
  MISSING_EVALUATION_DATA: {
    label: "Awaiting Dual Run Evidence",
    desc: "Deterministic decision requires complete execution and evaluation results for both Baseline V1 and Candidate V2.",
  },
};

export default function DecisionVerdictCard({ decision, hasRuns = true }: DecisionVerdictCardProps) {
  if (!decision) {
    return (
      <div
        className="card"
        style={{
          padding: "20px 24px",
          borderStyle: "dashed",
          background: "rgba(255, 255, 255, 0.02)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
          <span style={{ fontSize: 16 }}>⚖️</span>
          <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em" }}>
            Deterministic Evolution Decision Engine
          </span>
        </div>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
          {hasRuns
            ? "Run #2 execution and evaluation must be completed before the deterministic evolution policy can compute acceptance."
            : "No comparative execution traces available yet. Execute Architecture V1 and mutated V2 to trigger the policy."}
        </p>
      </div>
    );
  }

  const status = (decision.status || "INCONCLUSIVE").toUpperCase() as "ACCEPTED" | "REJECTED" | "INCONCLUSIVE";
  const isAccepted = status === "ACCEPTED";
  const isRejected = status === "REJECTED";
  const isInconclusive = status === "INCONCLUSIVE";

  const scoreDeltaPct = (decision.score_delta * 100).toFixed(1);
  const deltaSign = decision.score_delta > 0 ? "+" : "";

  return (
    <div
      className={`decision-banner ${isAccepted ? "accepted" : isRejected ? "rejected" : "inconclusive"} fade-up`}
    >
      {/* Top Banner Row */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 14, marginBottom: 16 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span
              className={`verdict-tag ${isAccepted ? "accepted" : isRejected ? "rejected" : "inconclusive"}`}
            >
              {isAccepted && "✓ "}
              {isRejected && "✕ "}
              {isInconclusive && "⚠ "}
              VERDICT: {status}
            </span>

            <span style={{ fontSize: 11, fontFamily: "var(--font-mono, monospace)", color: "var(--text-muted)" }}>
              Policy v{decision.policy_version || "1.0.0"} · ID: {decision.decision_id || "eval_decision"}
            </span>
          </div>

          <h3 style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)" }}>
            {isAccepted && "Architecture Candidate V2 Accepted into Production Line"}
            {isRejected && "Architecture Candidate V2 Rejected by Policy"}
            {isInconclusive && "Architecture Evaluation Inconclusive — Requires Further Evidence"}
          </h3>
        </div>

        {/* Score Delta Pill */}
        <div
          style={{
            background: "rgba(0, 0, 0, 0.3)",
            padding: "8px 14px",
            borderRadius: 8,
            border: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: 12,
          }}
        >
          <div>
            <div style={{ fontSize: 10, textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>
              Composite Delta (Δ)
            </div>
            <div
              style={{
                fontSize: 16,
                fontWeight: 800,
                fontFamily: "var(--font-mono, monospace)",
                color: isAccepted ? "#34d399" : isRejected ? "#fb7185" : "#fbbf24",
              }}
            >
              {deltaSign}{scoreDeltaPct}%
            </div>
          </div>

          <div style={{ borderLeft: "1px solid var(--border)", paddingLeft: 12 }}>
            <div style={{ fontSize: 10, textTransform: "uppercase", color: "var(--text-muted)", fontWeight: 700 }}>
              Baseline → V2
            </div>
            <div style={{ fontSize: 12, fontFamily: "var(--font-mono, monospace)", color: "var(--text-secondary)" }}>
              {(decision.v1_overall_score * 100).toFixed(0)}% → {(decision.v2_overall_score * 100).toFixed(0)}%
            </div>
          </div>
        </div>
      </div>

      {/* Rationale text */}
      <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 16 }}>
        {decision.rationale}
      </p>

      {/* Hard Constraints Checklist & Validation Errors */}
      <div
        style={{
          background: "rgba(0, 0, 0, 0.25)",
          border: "1px solid var(--border-soft)",
          borderRadius: 8,
          padding: "12px 16px",
          marginBottom: 16,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                width: 8,
                height: 8,
                borderRadius: "50%",
                background: decision.hard_constraints_satisfied ? "#10b981" : "#f43f5e",
              }}
            />
            <span style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)" }}>
              Operational Constraints Verification:
            </span>
            <span
              className={decision.hard_constraints_satisfied ? "badge badge-emerald" : "badge badge-rose"}
            >
              {decision.hard_constraints_satisfied ? "All Constraints Satisfied" : "Constraint Violation Detected"}
            </span>
          </div>

          {decision.decision_timestamp && (
            <span style={{ fontSize: 11, color: "var(--text-muted)", fontFamily: "var(--font-mono, monospace)" }}>
              Recorded: {new Date(decision.decision_timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}
            </span>
          )}
        </div>

        {decision.validation_errors && decision.validation_errors.length > 0 && (
          <div style={{ marginTop: 10, paddingTop: 10, borderTop: "1px solid var(--border-soft)" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#fb7185", marginBottom: 4 }}>
              Violations Enforced:
            </div>
            <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "#fca5a5", lineHeight: 1.5 }}>
              {decision.validation_errors.map((err, idx) => (
                <li key={idx}>{err}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Reason Codes Breakdown */}
      {decision.reason_codes && decision.reason_codes.length > 0 && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 8 }}>
            Formal Reason Codes:
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {decision.reason_codes.map((code) => {
              const meta = REASON_EXPLANATIONS[code] || { label: code, desc: code };
              return (
                <div
                  key={code}
                  style={{
                    background: "rgba(255, 255, 255, 0.04)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    padding: "6px 10px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    maxWidth: 320,
                  }}
                >
                  <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-primary)", fontFamily: "var(--font-mono, monospace)" }}>
                    {meta.label}
                  </span>
                  <span style={{ fontSize: 10, color: "var(--text-muted)", lineHeight: 1.3 }}>
                    {meta.desc}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
