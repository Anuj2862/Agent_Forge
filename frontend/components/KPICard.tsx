"use client";

import React from "react";

interface KPICardProps {
  label: string;
  value: string | number;
  subtext?: string;
  delta?: {
    value: string;
    type?: "positive" | "negative" | "neutral";
  };
  icon?: React.ReactNode;
  accentColor?: string;
  className?: string;
}

export default function KPICard({
  label,
  value,
  subtext,
  delta,
  icon,
  accentColor = "var(--cyan-network)",
  className = "",
}: KPICardProps) {
  return (
    <div
      className={`kpi-card ${className}`}
      style={{
        padding: "16px 18px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Luminous accent line at the top */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 1.5,
          background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
          opacity: 0.85,
        }}
      />

      {/* Label and Icon Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            letterSpacing: "0.08em",
            textTransform: "uppercase",
            color: "var(--text-muted)",
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          {label}
        </span>
        {icon && (
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: 6,
              background: "var(--bg-card-subtle)",
              border: "1px solid var(--border-soft)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: accentColor,
              flexShrink: 0,
            }}
          >
            {icon}
          </div>
        )}
      </div>

      {/* Main KPI Value Row */}
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          justifyContent: "space-between",
          gap: 10,
          marginTop: 2,
        }}
      >
        <span
          style={{
            fontSize: 26,
            fontWeight: 700,
            color: "var(--text-primary)",
            letterSpacing: "-0.02em",
            fontFamily: "'JetBrains Mono', monospace",
          }}
        >
          {value}
        </span>

        {delta && (
          <span
            className={`kpi-delta ${delta.type || "neutral"}`}
            style={{
              fontSize: 11,
              fontWeight: 700,
              padding: "2px 7px",
              borderRadius: 6,
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {delta.value}
          </span>
        )}
      </div>

      {/* Subtext description if available */}
      {subtext && (
        <span
          style={{
            fontSize: 11.5,
            color: "var(--text-secondary)",
            marginTop: 2,
            lineHeight: 1.4,
          }}
        >
          {subtext}
        </span>
      )}
    </div>
  );
}
