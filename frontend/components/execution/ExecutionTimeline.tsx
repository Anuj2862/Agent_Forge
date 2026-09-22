"use client";

import { AgentLog } from "@/lib/api";

interface Props { logs: AgentLog[]; }

export default function ExecutionTimeline({ logs }: Props) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      {logs.map((log, idx) => {
        const success = log.status === "success";
        const accent = success ? "var(--emerald)" : "var(--amber)";
        const isLast = idx === logs.length - 1;

        return (
          <div
            key={`${log.agent_id}-${idx}`}
            style={{
              position: "relative",
              paddingLeft: 24,
              paddingBottom: isLast ? 0 : 18,
            }}
          >
            {/* Vertical line */}
            {!isLast && (
              <div
                style={{
                  position: "absolute",
                  left: 7,
                  top: 20,
                  bottom: 0,
                  width: 1,
                  background: "linear-gradient(to bottom, var(--border), transparent)",
                }}
              />
            )}

            {/* Dot */}
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 8,
                width: 14,
                height: 14,
                borderRadius: "50%",
                background: `${accent}22`,
                border: `2px solid ${accent}`,
                boxShadow: `0 0 6px ${accent}44`,
              }}
            />

            {/* Card */}
            <div
              style={{
                background: "var(--bg-secondary)",
                border: "1px solid var(--border-soft)",
                borderRadius: 10,
                padding: "12px 14px",
              }}
            >
              {/* Agent header */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6, gap: 8 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, minWidth: 0 }}>
                  <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {log.agent_name}
                  </span>
                  <span
                    style={{
                      fontSize: 9,
                      fontWeight: 700,
                      letterSpacing: ".08em",
                      textTransform: "uppercase",
                      padding: "2px 8px",
                      borderRadius: 99,
                      background: `${accent}14`,
                      border: `1px solid ${accent}33`,
                      color: accent,
                      flexShrink: 0,
                    }}
                  >
                    {log.status}
                  </span>
                </div>
                <span style={{ fontSize: 11, fontFamily: "monospace", color: "var(--text-muted)", flexShrink: 0 }}>
                  {log.execution_time_seconds}s
                </span>
              </div>

              {/* Role */}
              <p style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>{log.role}</p>

              {/* Output preview */}
              <p
                style={{
                  fontSize: 12,
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                  display: "-webkit-box",
                  WebkitLineClamp: 4,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
              >
                {log.output_preview}
              </p>

              {/* Tool calls */}
              {log.tool_calls && log.tool_calls.length > 0 && (
                <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 10 }}>
                  {log.tool_calls.map((tc: any, ti: number) => (
                    <span
                      key={ti}
                      style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 4,
                        fontSize: 10,
                        padding: "2px 8px",
                        background: "rgba(99,102,241,0.08)",
                        border: "1px solid rgba(99,102,241,0.18)",
                        borderRadius: 6,
                        color: "#818cf8",
                      }}
                    >
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
                      {tc.tool}
                      <span style={{ color: "#475569" }}>{tc.latency_ms}ms</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
