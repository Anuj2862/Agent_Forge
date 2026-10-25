"use client";

import { ReflectionResult, ReflectionIssue, ArchitecturalRecommendation } from "@/lib/api";

interface Props {
  reflection: ReflectionResult;
}

export default function ReflectionPanel({ reflection }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      {/* Reflection Summary */}
      <div
        style={{
          fontSize: 13,
          color: "var(--text-secondary)",
          lineHeight: 1.6,
          padding: "14px 18px",
          background: "var(--bg-card-subtle)",
          border: "1px solid var(--border-soft)",
          borderRadius: 8,
          fontStyle: "italic",
        }}
      >
        &ldquo;{reflection.reflection_summary}&rdquo;
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Identified Issues */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: ".08em" }}>
              Diagnosed Vulnerabilities
            </span>
            <span className="badge badge-rose">{reflection.identified_issues.length} Issues</span>
          </div>

          {reflection.identified_issues.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--emerald)", background: "rgba(16, 185, 129, 0.06)", padding: "12px", borderRadius: 8, textAlign: "center", border: "1px solid rgba(16, 185, 129, 0.2)" }}>
              ✓ No critical vulnerabilities detected in execution trace
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {reflection.identified_issues.map((issue: ReflectionIssue, i: number) => {
                const severity = (issue.severity || "medium").toLowerCase();
                const isHigh = severity === "high" || severity === "critical";

                return (
                  <div
                    key={i}
                    style={{
                      background: "rgba(244, 63, 94, 0.05)",
                      border: `1px solid ${isHigh ? "rgba(244, 63, 94, 0.3)" : "rgba(244, 63, 94, 0.15)"}`,
                      borderRadius: 8,
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, color: "#fb7185", textTransform: "uppercase", letterSpacing: ".06em" }}>
                        {issue.category ? issue.category.replace(/_/g, " ") : "Architectural Gap"}
                      </span>
                      <span className={isHigh ? "badge badge-rose" : "badge badge-amber"} style={{ fontSize: 9 }}>
                        {issue.severity || "Medium"}
                      </span>
                    </div>

                    <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: issue.affected_component ? 6 : 0 }}>
                      {issue.description}
                    </p>

                    {issue.affected_component && (
                      <div style={{ fontSize: 10, color: "var(--text-muted)", fontFamily: "var(--font-mono, monospace)" }}>
                        Affected Node: {issue.affected_component}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Structural Recommendations */}
        <div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: ".08em" }}>
              Structural Graph Recommendations
            </span>
            <span className="badge badge-cyan">{reflection.recommendations.length} Actions</span>
          </div>

          {reflection.recommendations.length === 0 ? (
            <div style={{ fontSize: 12, color: "var(--text-muted)", background: "var(--bg-card-subtle)", padding: "12px", borderRadius: 8, textAlign: "center", border: "1px solid var(--border-soft)" }}>
              No structural graph modifications required
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {reflection.recommendations.map((rec: ArchitecturalRecommendation, i: number) => {
                const priority = (rec.priority || "medium").toLowerCase();
                const isHigh = priority === "high";

                return (
                  <div
                    key={i}
                    style={{
                      background: "rgba(2, 132, 199, 0.05)",
                      border: "1px solid rgba(2, 132, 199, 0.2)",
                      borderLeft: "3px solid #0284c7",
                      borderRadius: "0 8px 8px 0",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 11, fontWeight: 700, color: "#38bdf8", textTransform: "uppercase", letterSpacing: ".06em" }}>
                        {rec.action}
                      </span>
                      {isHigh && (
                        <span className="badge badge-rose" style={{ fontSize: 9 }}>High Priority</span>
                      )}
                    </div>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                      {rec.details?.rationale ? String(rec.details.rationale) : rec.reason || ""}
                    </p>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
