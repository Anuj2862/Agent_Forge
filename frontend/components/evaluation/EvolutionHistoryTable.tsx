"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getMemoryHistory, MemoryRecord } from "@/lib/api";

export default function EvolutionHistoryTable() {
  const [records, setRecords] = useState<MemoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMemoryHistory(1, 20)
      .then((d) => { setRecords(d.records); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "48px 0" }}>
        <span className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
      </div>
    );
  }

  if (records.length === 0) {
    return (
      <div
        className="card"
        style={{
          padding: "48px 24px",
          textAlign: "center",
          borderStyle: "dashed",
        }}
      >
        <svg style={{ margin: "0 auto 16px", color: "var(--text-muted)" }} width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 20v-6M6 20V10M18 20V4"/>
        </svg>
        <p style={{ fontSize: 14, color: "var(--text-muted)" }}>No runs yet — submit a task from the dashboard.</p>
      </div>
    );
  }

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" }}>
              {["Task", "Architecture", "Run", "Success", "Recommendation", ""].map((h) => (
                <th
                  key={h}
                  style={{
                    padding: "11px 16px",
                    textAlign: "left",
                    fontSize: 10,
                    fontWeight: 700,
                    letterSpacing: ".09em",
                    textTransform: "uppercase",
                    color: "var(--text-muted)",
                    whiteSpace: "nowrap",
                  }}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {records.map((rec, i) => {
              const rating = rec.success_rating;
              const ratingColor = rating >= 0.8 ? "var(--emerald)" : rating >= 0.6 ? "var(--amber)" : "var(--rose)";
              return (
                <tr
                  key={rec.record_id}
                  style={{
                    borderBottom: i < records.length - 1 ? "1px solid var(--border-soft)" : "none",
                    transition: "background .12s",
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = "var(--bg-secondary)")}
                  onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                >
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 3 }}>
                      {rec.task_type.replace(/_/g, " ")}
                    </div>
                    <div style={{ fontSize: 10, fontFamily: "monospace", color: "var(--text-muted)" }}>
                      {rec.task_spec.task_id.slice(0, 12)}…
                    </div>
                  </td>
                  <td style={{ padding: "14px 16px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                      <span className="badge badge-violet">{rec.topology}</span>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{rec.agent_count} agents</span>
                    </div>
                  </td>
                  <td style={{ padding: "14px 16px", textAlign: "center" }}>
                    <span
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        width: 24,
                        height: 24,
                        borderRadius: "50%",
                        background: rec.run_number > 1 ? "rgba(16,185,129,0.12)" : "var(--bg-secondary)",
                        border: rec.run_number > 1 ? "1px solid rgba(16,185,129,0.25)" : "1px solid var(--border)",
                        fontSize: 11,
                        fontWeight: 800,
                        color: rec.run_number > 1 ? "var(--emerald)" : "var(--text-muted)",
                      }}
                    >
                      {rec.run_number}
                    </span>
                  </td>
                  <td style={{ padding: "14px 16px", textAlign: "center" }}>
                    <span
                      style={{
                        fontSize: 14,
                        fontWeight: 800,
                        fontFamily: "monospace",
                        color: ratingColor,
                      }}
                    >
                      {(rating * 100).toFixed(0)}%
                    </span>
                  </td>
                  <td style={{ padding: "14px 16px", maxWidth: 260 }}>
                    <span
                      style={{
                        fontSize: 12,
                        color: "var(--text-muted)",
                        display: "-webkit-box",
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical",
                        overflow: "hidden",
                      }}
                    >
                      {rec.recommendation_summary || "—"}
                    </span>
                  </td>
                  <td style={{ padding: "14px 16px", textAlign: "right" }}>
                    <Link
                      href={`/run/${rec.task_spec.task_id}`}
                      style={{
                        fontSize: 12,
                        fontWeight: 600,
                        color: "#818cf8",
                        textDecoration: "none",
                        padding: "4px 10px",
                        borderRadius: 6,
                        border: "1px solid rgba(99,102,241,0.2)",
                        transition: "background .12s",
                      }}
                    >
                      View
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
