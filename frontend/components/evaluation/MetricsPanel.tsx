"use client";

import { EvaluationMetrics } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface Props { metrics: EvaluationMetrics; }

function scoreColor(v: number) {
  if (v >= 0.8) return "var(--emerald)";
  if (v >= 0.6) return "var(--amber)";
  return "var(--rose)";
}

const CustomTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 8, padding: "8px 12px", fontSize: 12 }}>
      <span style={{ color: "var(--text-secondary)" }}>{payload[0].name}: </span>
      <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>{payload[0].value}%</span>
    </div>
  );
};

export default function MetricsPanel({ metrics }: Props) {
  const accuracyVal = typeof (metrics as any).accuracy === "number"
    ? Math.round((metrics as any).accuracy * 100)
    : Math.round(metrics.task_success * 100);

  const verificationStatus = (metrics as any).verification_confidence || (
    metrics.agent_count >= 3 ? "Corroborated" : "Unverified"
  );

  const isVerified = verificationStatus.toLowerCase().includes("corroborat") || verificationStatus.toLowerCase().includes("high");

  const bars = [
    { name: "Task Success", value: Math.round(metrics.task_success * 100) },
    { name: "Output Quality", value: Math.round(metrics.quality * 100) },
    { name: "Factual Accuracy", value: accuracyVal },
    { name: "Completeness", value: Math.round(metrics.completeness * 100) },
  ];

  const stats = [
    { label: "Exec Time",   value: `${metrics.execution_time_seconds.toFixed(1)}s` },
    { label: "Agents",      value: `${metrics.agent_count}` },
    { label: "Tool Calls",  value: `${metrics.tool_call_count}` },
  ];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {/* Verification Status Pill */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 12px",
          borderRadius: 8,
          background: isVerified ? "rgba(16, 185, 129, 0.08)" : "rgba(245, 158, 11, 0.08)",
          border: `1px solid ${isVerified ? "rgba(16, 185, 129, 0.25)" : "rgba(245, 158, 11, 0.25)"}`,
        }}
      >
        <span style={{ fontSize: 11, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".06em" }}>
          Verification Status
        </span>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            color: isVerified ? "#34d399" : "#fbbf24",
            display: "flex",
            alignItems: "center",
            gap: 5,
          }}
        >
          {isVerified ? "✓ Corroborated" : "⚠ Unverified Claims"}
        </span>
      </div>
      {/* Score bars */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {bars.map(({ name, value }) => {
          const color = scoreColor(value / 100);
          return (
            <div key={name}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>{name}</span>
                <span style={{ fontSize: 12, fontWeight: 700, fontFamily: "monospace", color }}>{value}%</span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${value}%`, background: color }}
                />
              </div>
            </div>
          );
        })}
      </div>

      <hr className="divider" />

      {/* Stats row */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
        {stats.map(({ label, value }) => (
          <div
            key={label}
            style={{
              background: "var(--bg-secondary)",
              border: "1px solid var(--border-soft)",
              borderRadius: 8,
              padding: "12px 14px",
              textAlign: "center",
            }}
          >
            <div style={{ fontSize: 20, fontWeight: 800, fontFamily: "monospace", color: "var(--text-primary)", marginBottom: 4 }}>{value}</div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", letterSpacing: ".07em" }}>{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
