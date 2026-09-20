"use client";

import { ReflectionResult } from "@/lib/api";

interface Props { reflection: ReflectionResult; }

export default function ReflectionPanel({ reflection }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Summary */}
      <p
        style={{
          fontSize: 13,
          color: "var(--text-secondary)",
          lineHeight: 1.7,
          padding: "12px 16px",
          background: "var(--bg-secondary)",
          border: "1px solid var(--border-soft)",
          borderRadius: 8,
          fontStyle: "italic",
        }}
      >
        {reflection.reflection_summary}
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Issues */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: ".08em" }}>Issues</span>
            <span className="badge badge-rose">{reflection.identified_issues.length}</span>
          </div>

          {reflection.identified_issues.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", padding: "14px 0" }}>None detected ✓</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {reflection.identified_issues.map((issue, i) => (
                <div
                  key={i}
                  style={{
                    background: "rgba(244,63,94,0.05)",
                    border: "1px solid rgba(244,63,94,0.15)",
                    borderRadius: 8,
                    padding: "10px 12px",
                  }}
                >
                  <div style={{ fontSize: 10, fontWeight: 700, color: "#fb7185", textTransform: "uppercase", letterSpacing: ".07em", marginBottom: 4 }}>
                    {issue.category.replace(/_/g, " ")}
                  </div>
                  <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.55 }}>{issue.description}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recommendations */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: ".08em" }}>Recommendations</span>
            <span className="badge badge-cyan">{reflection.recommendations.length}</span>
          </div>

          {reflection.recommendations.length === 0 ? (
            <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", padding: "14px 0" }}>None needed</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {reflection.recommendations.map((rec, i) => (
                <div
                  key={i}
                  style={{
                    background: "rgba(6,182,212,0.05)",
                    border: "1px solid rgba(6,182,212,0.15)",
                    borderLeft: "3px solid rgba(6,182,212,0.6)",
                    borderRadius: "0 8px 8px 0",
                    padding: "10px 12px",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 4 }}>
                    <span style={{ fontSize: 10, fontWeight: 700, color: "#38bdf8", textTransform: "uppercase", letterSpacing: ".07em" }}>{rec.action}</span>
                    {rec.priority === "high" && (
                      <span className="badge badge-rose" style={{ fontSize: 9, padding: "1px 6px" }}>High</span>
                    )}
                  </div>
                  <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.55 }}>
                    {rec.details.rationale || Object.values(rec.details)[0]}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
