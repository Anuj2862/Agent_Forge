"use client";

import { useState, useMemo } from "react";
import { AgentLog, ExecutionEvent } from "@/lib/api";

interface ExecutionTimelineProps {
  events?: ExecutionEvent[];
  logs?: AgentLog[];
  isStreaming?: boolean;
  emptyMessage?: string;
}

export default function ExecutionTimeline({
  events = [],
  logs = [],
  isStreaming = false,
  emptyMessage = "Awaiting execution events…",
}: ExecutionTimelineProps) {
  const [filterType, setFilterType] = useState<"all" | "agents" | "tools" | "stages" | "errors">("all");
  const [expandedEvents, setExpandedEvents] = useState<Record<string, boolean>>({});

  const toggleExpand = (id: string) => {
    setExpandedEvents((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Convert legacy AgentLog[] into normalized items if no events provided
  const normalizedItems = useMemo(() => {
    if (events && events.length > 0) {
      // Deduplicate by event_id and sort by sequence_number
      const map = new Map<string, ExecutionEvent>();
      for (const ev of events) {
        map.set(ev.event_id, ev);
      }
      const uniqueEvents = Array.from(map.values());
      uniqueEvents.sort((a, b) => a.sequence_number - b.sequence_number);
      return uniqueEvents;
    }

    // Fallback from legacy AgentLog[]
    if (logs && logs.length > 0) {
      return logs.map((log, idx) => ({
        event_id: `legacy_${log.agent_id}_${idx}`,
        execution_id: "legacy",
        task_id: "legacy",
        sequence_number: idx + 1,
        event_type: log.status === "failed" ? "agent.failed" : "agent.completed",
        timestamp: new Date().toISOString(),
        status: log.status === "failed" ? "failed" : "completed",
        agent_id: log.agent_id,
        stage: "agent_execution",
        message: `Agent '${log.agent_name || log.agent_id}' (${log.role}) finished execution`,
        data: {
          role: log.role,
          execution_time_seconds: log.execution_time_seconds ?? log.execution_time,
          tool_calls: log.tool_calls,
          output_preview: log.output_preview,
        },
        error: log.status === "failed" ? "Agent execution failed" : undefined,
      })) as ExecutionEvent[];
    }

    return [];
  }, [events, logs]);

  // Filter items based on active category filter
  const filteredItems = useMemo(() => {
    if (filterType === "all") return normalizedItems;
    if (filterType === "agents") {
      return normalizedItems.filter((e) => e.event_type.startsWith("agent."));
    }
    if (filterType === "tools") {
      return normalizedItems.filter((e) => e.event_type.startsWith("tool."));
    }
    if (filterType === "stages") {
      return normalizedItems.filter(
        (e) =>
          e.event_type.includes("stage_") ||
          e.event_type.startsWith("execution.") ||
          e.event_type.startsWith("evolution.") ||
          e.event_type.startsWith("evaluation.")
      );
    }
    if (filterType === "errors") {
      return normalizedItems.filter(
        (e) =>
          e.status === "failed" ||
          e.event_type.includes("failed") ||
          e.event_type.includes("warning") ||
          e.event_type.includes("rejected") ||
          Boolean(e.error)
      );
    }
    return normalizedItems;
  }, [normalizedItems, filterType]);

  if (normalizedItems.length === 0) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "36px 16px",
          textAlign: "center",
          gap: 10,
          color: "var(--text-muted)",
        }}
      >
        {isStreaming ? (
          <>
            <span className="spinner" style={{ width: 24, height: 24, borderWidth: 2 }} />
            <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>Streaming live telemetry from execution engine…</p>
          </>
        ) : (
          <>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <p style={{ fontSize: 13, color: "var(--text-secondary)" }}>{emptyMessage}</p>
          </>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {/* Restrained Filter Row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 4,
          paddingBottom: 6,
          borderBottom: "1px solid var(--border)",
          overflowX: "auto",
        }}
      >
        {(
          [
            { key: "all", label: `All (${normalizedItems.length})` },
            { key: "agents", label: "Agents" },
            { key: "tools", label: "Tools" },
            { key: "stages", label: "Stages" },
            { key: "errors", label: "Errors" },
          ] as const
        ).map((f) => {
          const isActive = filterType === f.key;
          return (
            <button
              key={f.key}
              onClick={() => setFilterType(f.key)}
              style={{
                fontSize: 11.5,
                fontWeight: isActive ? 600 : 400,
                color: isActive ? "var(--blue-primary)" : "var(--text-muted)",
                background: isActive ? "rgba(37, 99, 235, 0.12)" : "transparent",
                border: isActive ? "1px solid var(--border-active)" : "1px solid transparent",
                borderRadius: 5,
                padding: "2px 8px",
                cursor: "pointer",
                whiteSpace: "nowrap",
                transition: "all 0.15s ease",
              }}
            >
              {f.label}
            </button>
          );
        })}
      </div>

      {/* Investigation Feed List (Thin Separators, No Nested Cards) */}
      <div style={{ display: "flex", flexDirection: "column" }}>
        {filteredItems.map((event, idx) => {
          const isLast = idx === filteredItems.length - 1;
          const isExpanded = Boolean(expandedEvents[event.event_id]);
          const hasPayload =
            (event.data && Object.keys(event.data).length > 0) || Boolean(event.error);

          // Category dot color
          let dotColor = "var(--text-muted)";
          if (event.event_type.startsWith("agent.")) {
            dotColor = "var(--blue-bright)";
          } else if (event.event_type.startsWith("tool.")) {
            dotColor = "var(--amber)";
          } else if (event.event_type.startsWith("evaluation.")) {
            dotColor = "var(--emerald)";
          } else if (event.event_type.startsWith("evolution.")) {
            dotColor = event.event_type.includes("rejected") ? "var(--error-red)" : "var(--emerald)";
          } else if (event.event_type.includes("failed") || event.error) {
            dotColor = "var(--error-red)";
          }

          const isLiveItem = isStreaming && isLast;

          return (
            <div
              key={event.event_id}
              style={{
                padding: "8px 6px",
                borderBottom: isLast ? "none" : "1px solid var(--border-soft)",
                display: "flex",
                flexDirection: "column",
                gap: 4,
                transition: "background 0.12s ease",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = "var(--bg-card-subtle)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = "transparent";
              }}
            >
              {/* Event Header Line: Sequence + Dot + Title + Timestamp */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 8,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
                  {/* Sequence number in mono */}
                  <span
                    style={{
                      fontFamily: "'JetBrains Mono', monospace",
                      fontSize: 10.5,
                      color: "var(--text-muted)",
                      minWidth: 22,
                    }}
                  >
                    #{String(event.sequence_number).padStart(2, "0")}
                  </span>

                  {/* Dot */}
                  <span
                    style={{
                      width: 6,
                      height: 6,
                      borderRadius: "50%",
                      background: dotColor,
                      flexShrink: 0,
                      boxShadow: isLiveItem ? `0 0 6px ${dotColor}` : "none",
                    }}
                  />

                  {/* Event Type / Title */}
                  <span
                    style={{
                      fontSize: 12,
                      fontWeight: 600,
                      color: "var(--text-primary)",
                      whiteSpace: "nowrap",
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                    }}
                  >
                    {event.event_type}
                  </span>

                  {/* Agent ID tag if present */}
                  {event.agent_id && (
                    <span
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 10.5,
                        color: "var(--blue-primary)",
                        background: "rgba(37, 99, 235, 0.10)",
                        border: "1px solid var(--border)",
                        padding: "1px 5px",
                        borderRadius: 3,
                        flexShrink: 0,
                      }}
                    >
                      {event.agent_id}
                    </span>
                  )}
                </div>

                {/* Timestamp in mono */}
                <span
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 10.5,
                    color: "var(--text-muted)",
                    flexShrink: 0,
                  }}
                >
                  {event.timestamp ? event.timestamp.slice(11, 19) : ""}
                </span>
              </div>

              {/* Event Message */}
              <div
                style={{
                  fontSize: 12,
                  color: "var(--text-secondary)",
                  lineHeight: 1.45,
                  paddingLeft: 28,
                }}
              >
                {event.message}
              </div>

              {/* Expandable Technical Details */}
              {hasPayload && (
                <div style={{ paddingLeft: 28, marginTop: 2 }}>
                  <button
                    onClick={() => toggleExpand(event.event_id)}
                    style={{
                      background: "none",
                      border: "none",
                      padding: 0,
                      fontSize: 11,
                      color: "var(--blue-primary)",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    <span>{isExpanded ? "▾ Hide payload" : "▸ View payload"}</span>
                  </button>

                  {isExpanded && (
                    <div
                      style={{
                        marginTop: 6,
                        background: "var(--bg-input)",
                        border: "1px solid var(--border)",
                        borderRadius: 6,
                        padding: "8px 10px",
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 11,
                        color: "var(--text-primary)",
                        overflowX: "auto",
                        maxHeight: 200,
                        overflowY: "auto",
                      }}
                    >
                      {event.error && (
                        <div style={{ color: "var(--error-red)", marginBottom: 6, fontWeight: 500 }}>
                          Error: {event.error}
                        </div>
                      )}
                      <pre style={{ margin: 0, whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                        {JSON.stringify(event.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
