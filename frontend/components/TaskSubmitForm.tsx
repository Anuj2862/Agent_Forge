"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitTask, runExecution } from "@/lib/api";

const CANONICAL_DEMOS = [
  {
    tag: "DEMO 1: Research + Verification (Canonical)",
    text: "Research the impact of electric vehicle adoption in India and produce a concise evidence-backed summary.",
  },
  {
    tag: "DEMO 2: Data Analysis",
    text: "Analyze quarterly financial revenue trends across AI semiconductor companies, calculate growth metrics, and synthesize a verified projection report.",
  },
  {
    tag: "DEMO 3: Problem Solving",
    text: "Analyze memory leak patterns in asynchronous Python microservices, investigate root causes, verify solutions, and produce actionable recommendations.",
  },
];

export default function TaskSubmitForm() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) return;

    setLoading(true);
    setStage("Decomposing task & extracting capabilities…");

    try {
      const { task_id, architecture_spec } = await submitTask(trimmed);
      setStage(
        `Synthesized ${architecture_spec.agents.length}-agent ${architecture_spec.topology} architecture — building LangGraph…`
      );
      const execution = await runExecution(task_id, 1);
      setStage("Execution complete — loading dashboard…");
      router.push(`/run/${task_id}?exec=${execution.execution_id}`);
    } catch (err) {
      console.error(err);
      setStage("Something went wrong — check the console.");
      setLoading(false);
    }
  };

  return (
    <div
      className="card-glass"
      style={{ padding: "28px 32px 24px" }}
    >
      {/* Engine Status Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <span style={{ fontSize: 13, fontWeight: 600, color: "var(--text-secondary)" }}>
          Natural Language Task Input
        </span>
        <span
          style={{
            fontSize: 10,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            padding: "3px 9px",
            borderRadius: 99,
            background: "rgba(16, 185, 129, 0.12)",
            color: "#34d399",
            border: "1px solid rgba(16, 185, 129, 0.25)",
            fontWeight: 600,
          }}
        >
          ● Autonomous Engine Ready
        </span>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Textarea */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={loading}
          placeholder="Describe any task for Agent Forge to analyze, synthesize, and solve…"
          className="input-field"
          style={{ minHeight: 110, marginBottom: 14 }}
        />

        {/* Canonical Demo Scenario Chips */}
        {!loading && (
          <div style={{ marginBottom: 18 }}>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 8 }}>
              Select a benchmark task scenario:
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {CANONICAL_DEMOS.map((demo) => (
                <button
                  key={demo.tag}
                  type="button"
                  onClick={() => setPrompt(demo.text)}
                  style={{
                    background: prompt === demo.text ? "rgba(99,102,241,0.22)" : "rgba(99,102,241,0.07)",
                    border: prompt === demo.text ? "1px solid rgba(99,102,241,0.5)" : "1px solid rgba(99,102,241,0.18)",
                    borderRadius: 99,
                    padding: "5px 14px",
                    fontSize: 11,
                    color: prompt === demo.text ? "#a5b4fc" : "#818cf8",
                    cursor: "pointer",
                    fontFamily: "inherit",
                    transition: "all .15s ease",
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                  }}
                >
                  <span style={{ opacity: 0.7 }}>⚡</span>
                  <span>{demo.tag}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Footer row */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          {/* Status */}
          <div style={{ fontSize: 12, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 7, minHeight: 22 }}>
            {loading && (
              <>
                <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                <span style={{ color: "#818cf8", fontWeight: 500 }}>{stage}</span>
              </>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="btn btn-primary"
            style={{ whiteSpace: "nowrap", fontSize: 13, padding: "9px 22px" }}
          >
            {loading ? "Forging Architecture…" : "FORGE ARCHITECTURE →"}
          </button>
        </div>
      </form>
    </div>
  );
}
