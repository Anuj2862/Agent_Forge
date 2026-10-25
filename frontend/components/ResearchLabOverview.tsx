"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getHealth, listTasks, HealthResponse } from "@/lib/api";

const CORE_INVARIANTS = [
  {
    id: "constraint_invariance",
    title: "Constraint Invariance",
    tag: "Hard Invariant",
    color: "#6366f1",
    summary: "Operational constraints (max agents, forbidden tools, latency) are verified at synthesis and strictly enforced during mutation.",
    detail: "Candidates exceeding agent budgets or using forbidden tools are rejected immediately by EvolutionDecisionPolicy.",
  },
  {
    id: "failure_diagnosis",
    title: "Failure-Driven Reflection",
    tag: "Diagnostic Engine",
    color: "#8b5cf6",
    summary: "Evaluates factual consistency and completeness to identify exact architectural failure modes.",
    detail: "Maps unverified claims and hallucinations directly to structural graph mutations rather than vague prompt edits.",
  },
  {
    id: "verification_synthesis",
    title: "Verification Mutation",
    tag: "Adaptive Graph",
    color: "#0ea5e9",
    summary: "Evolves graph topology by synthesizing dedicated verification specialists or upgrading terminal nodes.",
    detail: "Enforces cycle prevention in DAG execution while routing upstream claims through independent fact-checkers.",
  },
  {
    id: "deterministic_policy",
    title: "Deterministic Decision Gate",
    tag: "Gated Selection",
    color: "#10b981",
    summary: "Compares empirical V1 vs V2 metric shifts against strict quality and regression thresholds.",
    detail: "Issues explicit ACCEPTED, REJECTED, or INCONCLUSIVE verdicts with permanent reason codes and delta audit trails.",
  },
];

export default function ResearchLabOverview() {
  const [activeInvariant, setActiveInvariant] = useState(CORE_INVARIANTS[0]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [experimentCount, setExperimentCount] = useState<number | null>(null);

  useEffect(() => {
    async function loadStats() {
      try {
        const [h, t] = await Promise.all([
          getHealth().catch(() => null),
          listTasks().catch(() => ({ total: 0 })),
        ]);
        if (h) setHealth(h);
        if (t) setExperimentCount(t.total);
      } catch {
        // Handled gracefully
      }
    }
    loadStats();
  }, []);

  return (
    <div className="card" style={{ padding: "0", overflow: "hidden" }}>
      {/* Top Banner */}
      <div
        style={{
          padding: "16px 20px",
          background: "var(--bg-card-subtle)",
          borderBottom: "1px solid var(--border-soft)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: 6,
              background: "rgba(99, 102, 241, 0.15)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#818cf8",
              fontSize: 12,
            }}
          >
            ⚛
          </div>
          <div>
            <span style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              Research Engine Foundation
            </span>
            <span style={{ fontSize: 11, color: "var(--text-muted)", marginLeft: 8 }}>
              Thesis Invariants &amp; Active Runtime
            </span>
          </div>
        </div>

        {/* Live Metrics Pill */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "4px 12px",
              borderRadius: 99,
              background: "rgba(255, 255, 255, 0.04)",
              border: "1px solid var(--border)",
              fontSize: 11,
              fontFamily: "var(--font-mono, monospace)",
              color: "var(--text-secondary)",
            }}
          >
            <span>
              FastAPI {health?.version ? `v${health.version}` : "v0.2.0"} · SQLite DB: {experimentCount !== null ? `${experimentCount} Experiments` : "Connected"}
            </span>
          </div>

          <Link href="/history" className="btn btn-secondary btn-sm" style={{ fontSize: 11 }}>
            View History →
          </Link>
        </div>
      </div>

      {/* Grid of 4 Core Thesis Invariants */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: "1px",
          background: "var(--border-soft)",
        }}
      >
        {CORE_INVARIANTS.map((inv) => {
          const isSelected = activeInvariant.id === inv.id;
          return (
            <button
              key={inv.id}
              onClick={() => setActiveInvariant(inv)}
              style={{
                background: isSelected ? "var(--bg-card-hover)" : "var(--bg-card)",
                padding: "18px 20px",
                border: "none",
                textAlign: "left",
                cursor: "pointer",
                transition: "all 0.15s ease",
                position: "relative",
              }}
            >
              {isSelected && (
                <div
                  style={{
                    position: "absolute",
                    top: 0,
                    left: 0,
                    right: 0,
                    height: 2,
                    background: inv.color,
                  }}
                />
              )}

              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    letterSpacing: "0.08em",
                    color: inv.color,
                  }}
                >
                  {inv.tag}
                </span>
                {isSelected && (
                  <span style={{ fontSize: 10, fontWeight: 700, color: inv.color, padding: "1px 6px", borderRadius: 4, background: "rgba(255, 255, 255, 0.06)" }}>
                    Active
                  </span>
                )}
              </div>

              <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
                {inv.title}
              </div>

              <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.45 }}>
                {inv.summary}
              </p>
            </button>
          );
        })}
      </div>

      {/* Detail Footer for Active Invariant */}
      <div
        style={{
          padding: "14px 20px",
          background: "var(--bg-card-subtle)",
          borderTop: "1px solid var(--border-soft)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontSize: 12 }}>
          <span style={{ fontWeight: 700, color: activeInvariant.color }}>
            {activeInvariant.title} Specification:
          </span>
          <span style={{ color: "var(--text-secondary)" }}>
            {activeInvariant.detail}
          </span>
        </div>

        <Link href="/architecture" style={{ fontSize: 11, color: "var(--indigo)", textDecoration: "none", fontWeight: 600 }}>
          Inspect Topology Rules →
        </Link>
      </div>
    </div>
  );
}
