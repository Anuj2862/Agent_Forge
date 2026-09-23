"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitTask, runExecution } from "@/lib/api";

const EXAMPLE_CHIPS = [
  { label: "Research & Verify", emoji: "🔍" },
  { label: "Data Analysis",    emoji: "📊" },
  { label: "Document Comparison", emoji: "📄" },
  { label: "Planning",         emoji: "🗺️" },
  { label: "Code Generation",  emoji: "💻" },
];

const DEMO_PROMPTS: Record<string, string> = {
  "Research & Verify":
    "Research the impact of electric vehicle adoption in India and produce a concise evidence-backed summary.",
  "Data Analysis":
    "Analyze quarterly financial revenue trends across AI semiconductor companies, calculate growth metrics, and synthesize a verified projection report.",
  "Document Comparison":
    "Compare the architectures of GPT-4 and Gemini Ultra across key dimensions: training data, context length, multimodal capabilities, and reasoning benchmarks.",
  "Planning":
    "Create a comprehensive 90-day go-to-market plan for a new AI-powered developer productivity tool targeting enterprise engineering teams.",
  "Code Generation":
    "Analyze memory leak patterns in asynchronous Python microservices, investigate root causes, verify solutions, and produce actionable recommendations.",
};

export default function TaskSubmitForm() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("");
  const [activeChip, setActiveChip] = useState<string | null>(null);
  const router = useRouter();

  const handleChip = (label: string) => {
    setActiveChip(label);
    setPrompt(DEMO_PROMPTS[label] ?? "");
  };

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
      style={{ padding: "0", overflow: "hidden" }}
    >
      {/* Header bar */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 20px",
          borderBottom: "1px solid rgba(255,255,255,0.05)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 7,
              background: "linear-gradient(135deg, rgba(124,58,237,0.3), rgba(99,102,241,0.3))",
              border: "1px solid rgba(124,58,237,0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#c4b5fd",
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "-0.01em" }}>
              Describe Your Task
            </div>
            <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 1 }}>
              Enter a natural language task and let Agent Forge design, execute, and evolve the best agent architecture.
            </div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              fontSize: 9,
              textTransform: "uppercase",
              letterSpacing: "0.1em",
              padding: "3px 9px",
              borderRadius: 99,
              background: "rgba(16,185,129,0.1)",
              color: "#34d399",
              border: "1px solid rgba(16,185,129,0.2)",
              fontWeight: 700,
            }}
          >
            Advanced Options ▾
          </span>
        </div>
      </div>

      {/* Example chips row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "10px 20px",
          borderBottom: "1px solid rgba(255,255,255,0.04)",
          flexWrap: "wrap",
        }}
      >
        <span style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase", marginRight: 4, flexShrink: 0 }}>
          Examples:
        </span>
        {EXAMPLE_CHIPS.map((chip) => (
          <button
            key={chip.label}
            type="button"
            onClick={() => handleChip(chip.label)}
            className={`example-chip ${activeChip === chip.label ? "selected" : ""}`}
            disabled={loading}
          >
            <span>{chip.emoji}</span>
            <span>{chip.label}</span>
          </button>
        ))}
      </div>

      {/* Textarea + submit */}
      <form onSubmit={handleSubmit} style={{ padding: "16px 20px 18px" }}>
        <textarea
          id="task-prompt-input"
          value={prompt}
          onChange={(e) => {
            setPrompt(e.target.value);
            setActiveChip(null);
          }}
          disabled={loading}
          placeholder="Research the impact of electric vehicle adoption in India and produce a concise evidence-backed summary."
          className="input-field"
          style={{ minHeight: 90, marginBottom: 14, fontSize: 13.5 }}
        />

        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          {/* Status */}
          <div style={{ fontSize: 11.5, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 7, minHeight: 20, flex: 1 }}>
            {loading ? (
              <>
                <span className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} />
                <span style={{ color: "#a5b4fc", fontWeight: 500 }}>{stage}</span>
              </>
            ) : prompt.trim() ? (
              <span style={{ color: "var(--text-muted)" }}>
                {prompt.trim().length} chars · ready to forge
              </span>
            ) : null}
          </div>

          {/* Submit */}
          <button
            id="forge-architecture-btn"
            type="submit"
            disabled={loading || !prompt.trim()}
            className="btn btn-primary"
            style={{
              fontSize: 13,
              padding: "10px 22px",
              gap: 8,
              letterSpacing: "0.02em",
              flexShrink: 0,
            }}
          >
            {loading ? (
              <>
                <span className="spinner" style={{ width: 13, height: 13, borderWidth: 2, borderColor: "rgba(255,255,255,0.3)", borderTopColor: "#fff" }} />
                Forging…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
                </svg>
                Forge Architecture
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
