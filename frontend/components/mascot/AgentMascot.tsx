"use client";

import React, { useState } from "react";
import Image from "next/image";
import {
  AgentRole,
  ExecutionState,
  getRoleMetadata,
  getStatusMetadata,
  resolveAgentRole,
} from "@/lib/mascots";
import { useTheme } from "@/lib/theme";

export interface AgentMascotProps {
  role?: AgentRole | string;
  agent?: { agent_id?: string; name?: string; role?: string; objective?: string };
  status?: ExecutionState | string;
  size?: number;
  active?: boolean;
  showStatusBadge?: boolean;
  className?: string;
  style?: React.CSSProperties;
  title?: string;
}

export default function AgentMascot({
  role,
  agent,
  status,
  size = 46,
  active = false,
  showStatusBadge = false,
  className = "",
  style = {},
  title,
}: AgentMascotProps) {
  const [hasError, setHasError] = useState(false);
  const theme = useTheme();
  const isLight = theme === "light";

  // Resolve role intelligently from props or agent object
  const resolvedRole = (() => {
    if (agent) {
      const fromAgent = resolveAgentRole(agent);
      if (fromAgent !== "executor") return fromAgent;
    }
    if (role) {
      const fromRole = resolveAgentRole(role);
      if (fromRole !== "executor") return fromRole;
    }
    if (agent) return resolveAgentRole(agent);
    if (role) return resolveAgentRole(role);
    return "executor";
  })();
  const roleMeta = getRoleMetadata(resolvedRole, isLight);
  const statusMeta = status ? getStatusMetadata(status, isLight) : null;

  // Active / running glow
  const isRunning = statusMeta?.state === "running" || active;

  return (
    <div
      className={`agent-mascot-container ${className}`}
      title={title || `${roleMeta.name} (${roleMeta.tagline})${statusMeta ? ` — ${statusMeta.label}` : ""}`}
      style={{
        position: "relative",
        width: size,
        height: size,
        flexShrink: 0,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        borderRadius: Math.max(8, Math.round(size * 0.22)),
        background: isLight ? "#F8FAFC" : "#050B16",
        border: `1.5px solid ${
          isRunning
            ? statusMeta?.color || roleMeta.color
            : isLight
            ? roleMeta.borderLight
            : roleMeta.border
        }`,
        boxShadow: isRunning
          ? `0 0 16px ${roleMeta.color}88, inset 0 0 8px ${roleMeta.color}33`
          : isLight
          ? "0 2px 8px rgba(15, 23, 42, 0.06)"
          : "0 2px 10px rgba(0, 0, 0, 0.4)",
        transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
        overflow: "visible",
        ...style,
      }}
    >
      {/* Inner Character Image with fallback */}
      {!hasError ? (
        <div
          style={{
            position: "relative",
            width: size - 4,
            height: size - 4,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden",
            borderRadius: Math.max(6, Math.round(size * 0.18)),
          }}
        >
          <Image
            src={roleMeta.webpSrc}
            alt={`${roleMeta.name} Mascot`}
            width={size}
            height={size}
            onError={() => setHasError(true)}
            priority={size >= 44}
            style={{
              objectFit: "contain",
              width: "100%",
              height: "100%",
              pointerEvents: "none",
              userSelect: "none",
            }}
          />
        </div>
      ) : (
        /* Accessible High-Contrast SVG Fallback */
        <div
          style={{
            width: "100%",
            height: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: roleMeta.color,
          }}
          aria-label={roleMeta.name}
        >
          <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="10" rx="2" />
            <circle cx="12" cy="5" r="2" />
            <path d="M12 7v4" />
            <line x1="8" y1="16" x2="8.01" y2="16" />
            <line x1="16" y1="16" x2="16.01" y2="16" />
          </svg>
        </div>
      )}

      {/* Execution State Indicator Badge */}
      {showStatusBadge && statusMeta && (
        <div
          style={{
            position: "absolute",
            bottom: -3,
            right: -3,
            width: Math.max(12, Math.round(size * 0.28)),
            height: Math.max(12, Math.round(size * 0.28)),
            borderRadius: "50%",
            background: statusMeta.dotColor,
            border: `2px solid ${isLight ? "#FFFFFF" : "#050B16"}`,
            boxShadow: statusMeta.glow,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 3,
          }}
        >
          {statusMeta.state === "completed" && (
            <svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="3.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
          {statusMeta.state === "failed" && (
            <svg width="7" height="7" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" strokeWidth="3.5">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          )}
        </div>
      )}
    </div>
  );
}
