"use client";

import { EvaluationMetrics } from "@/lib/api";

interface Props {
  metrics: EvaluationMetrics & { verification_status?: string };
}

function scoreColor(v: number) {
  if (v >= 0.8) return "var(--emerald)";
  if (v >= 0.6) return "var(--amber)";
  return "var(--rose)";
}

export default function MetricsPanel({ metrics }: Props) {
  const accuracyVal =
    typeof metrics.accuracy === "number"
      ? Math.round(metrics.accuracy * 100)
      : Math.round(metrics.task_success * 100);

  const verificationStatus =
    metrics.verification_confidence ||
    metrics.verification_status ||
    (accuracyVal >= 80 ? "Corroborated" : "Unverified Claims");

  const isVerified =
    verificationStatus.toLowerCase().includes("corroborat") ||
    verificationStatus.toLowerCase().includes("high") ||
    verificationStatus.toLowerCase().includes("verified");

  const bars = [
    { name: "Task Success Fulfillment", value: Math.round(metrics.task_success * 100) },
    { name: "Output Coherence & Quality", value: Math.round(metrics.quality * 100) },
    { name: "Factual Accuracy", value: accuracyVal },
    { name: "Requirement Completeness", value: Math.round(metrics.completeness * 100) },
  ];

  const stats = [
    { label: "Execution Latency", value: `${metrics.execution_time_seconds.toFixed(2)}s` },
    { label: "Active Agent Team", value: `${metrics.agent_count} Nodes` },
    { label: "Tool Invocations", value: `${metrics.tool_call_count} Calls` },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Verification Status Pill */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "10px 14px",
          borderRadius: 8,
          background: isVerified ? "rgba(16, 185, 129, 0.08)" : "rgba(245, 158, 11, 0.08)",
          border: `1px solid ${isVerified ? "rgba(16, 185, 129, 0.25)" : "rgba(245, 158, 11, 0.25)"}`,
        }}
      >
        <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".06em" }}>
          Factual Verification Audit
        </span>
        <span
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: isVerified ? "#34d399" : "#fbbf24",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          {isVerified ? "✓ Claims Corroborated" : "⚠ Unverified Factual Claims"}
        </span>
      </div>

      {/* Score Bars */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {bars.map(({ name, value }) => {
          const color = scoreColor(value / 100);
          return (
            <div key={name}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 5 }}>
                <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{name}</span>
                <span style={{ fontSize: 12, fontWeight: 700, fontFamily: "var(--font-mono, monospace)", color }}>
                  {value}%
                </span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${Math.min(100, Math.max(0, value))}%`, background: color }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <hr className="divider" />

      {/* Metrics Stat Row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
        {stats.map(({ label, value }) => (
          <div
            key={label}
            style={{
              background: "var(--bg-card-subtle)",
              border: "1px solid var(--border-soft)",
              borderRadius: 8,
              padding: "12px 14px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 18, fontWeight: 800, fontFamily: "var(--font-mono, monospace)", color: "var(--text-primary)", marginBottom: 2 }}>
              {value}
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 700, textTransform: "uppercase", letterSpacing: ".06em" }}>
              {label}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
