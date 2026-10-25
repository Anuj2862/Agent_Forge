"use client";

import { useState } from "react";

export type StreamConnectionStatus =
  | "connecting"
  | "streaming"
  | "reconnecting"
  | "completed"
  | "disconnected";

interface LiveExecutionStatusProps {
  executionId: string;
  status?: string;
  stage?: string;
  eventCount: number;
  connectionStatus: StreamConnectionStatus;
  durationSeconds?: number;
  error?: string | null;
  onReconnect?: () => void;
}

export default function LiveExecutionStatus({
  executionId,
  status = "running",
  stage,
  eventCount,
  connectionStatus,
  durationSeconds,
  error,
  onReconnect,
}: LiveExecutionStatusProps) {
  const [copied, setCopied] = useState(false);

  const handleCopyId = () => {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(executionId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const isCompleted = status === "completed";
  const isFailed = status === "failed";
  const isRunning = status === "running";

  const statusLabel = isCompleted
    ? "Completed"
    : isFailed
    ? "Failed"
    : isRunning
    ? "Executing"
    : status;

  const statusColor = isCompleted
    ? "#34d399"
    : isFailed
    ? "#f87171"
    : "#38bdf8";

  return (
    <div
      style={{
        padding: "10px 14px",
        background: "var(--bg-card-subtle)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        display: "flex",
        flexDirection: "column",
        gap: 8,
      }}
    >
      {/* Primary Row: ID + Execution Status + Live Stream Pulse */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
          fontSize: 12,
        }}
      >
        {/* Monospace Execution ID */}
        <div style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
          <span style={{ color: "var(--text-muted)", fontSize: 12 }}>Run:</span>
          <span
            style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: 12,
              color: "var(--text-primary)",
              fontWeight: 500,
              maxWidth: 160,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
            title={executionId}
          >
            {executionId || "pending…"}
          </span>
          {executionId && (
            <button
              onClick={handleCopyId}
              title="Copy execution ID"
              style={{
                background: "transparent",
                border: "none",
                cursor: "pointer",
                padding: "2px 4px",
                color: copied ? "var(--emerald)" : "var(--text-muted)",
                fontSize: 11,
                lineHeight: 1,
              }}
            >
              {copied ? "✓" : "⧉"}
            </button>
          )}
        </div>

        {/* Status Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              fontSize: 11.5,
              fontWeight: 600,
              color: statusColor,
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: statusColor,
                boxShadow: isRunning ? `0 0 6px ${statusColor}` : "none",
              }}
            />
            <span>{statusLabel}</span>
          </div>

          {/* SSE Stream status if active */}
          {connectionStatus === "streaming" && (
            <span
              style={{
                fontSize: 10,
                color: "var(--cyan-network)",
                background: "rgba(8, 145, 178, 0.12)",
                padding: "1px 6px",
                borderRadius: 4,
                border: "1px solid rgba(8, 145, 178, 0.25)",
              }}
            >
              Live SSE
            </span>
          )}
        </div>
      </div>

      {/* Secondary Row: Technical Telemetry stats */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          fontSize: 11.5,
          color: "var(--text-secondary)",
          borderTop: "1px solid var(--border-soft)",
          paddingTop: 6,
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          {stage && (
            <span>
              Stage: <strong style={{ color: "var(--text-primary)", fontWeight: 500 }}>{stage.replace(/_/g, " ")}</strong>
            </span>
          )}
          <span>
            Events:{" "}
            <strong
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                color: "var(--text-primary)",
                fontWeight: 500,
              }}
            >
              {eventCount}
            </strong>
          </span>
          {durationSeconds !== undefined && durationSeconds > 0 && (
            <span>
              Duration:{" "}
              <strong
                style={{
                  fontFamily: "'JetBrains Mono', monospace",
                  color: "var(--text-primary)",
                  fontWeight: 500,
                }}
              >
                {durationSeconds.toFixed(2)}s
              </strong>
            </span>
          )}
        </div>

        {connectionStatus === "reconnecting" && onReconnect && (
          <button
            onClick={onReconnect}
            style={{
              fontSize: 11,
              color: "var(--blue-bright)",
              background: "none",
              border: "none",
              cursor: "pointer",
              textDecoration: "underline",
              padding: 0,
            }}
          >
            Reconnect
          </button>
        )}
      </div>

      {/* Error alert if any */}
      {error && (
        <div
          style={{
            padding: "6px 10px",
            background: "rgba(220, 38, 38, 0.08)",
            border: "1px solid rgba(220, 38, 38, 0.25)",
            borderRadius: 6,
            fontSize: 11.5,
            color: "var(--error-red)",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <span>✕</span>
          <span style={{ lineHeight: 1.4 }}>{error}</span>
        </div>
      )}
    </div>
  );
}
