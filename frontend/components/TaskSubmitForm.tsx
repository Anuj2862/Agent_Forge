"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitTask, runExecution } from "@/lib/api";

interface PresetItem {
  label: string;
  emoji: string;
  prompt: string;
  maxAgents?: number;
  requireVerification?: boolean;
  forbiddenTools?: string[];
}

const RESEARCH_PRESETS: PresetItem[] = [
  {
    label: "Distributed Raft Consensus",
    emoji: "⚡",
    prompt:
      "Investigate distributed consensus failure modes in Raft clusters, verify partition tolerance proofs, and produce an audited mitigation specification.",
    maxAgents: 3,
    requireVerification: true,
  },
  {
    label: "Financial Fraud Analysis",
    emoji: "📊",
    prompt:
      "Analyze quarterly financial transaction anomalies, flag suspicious shell-corporation patterns, and synthesize a verified audit projection.",
    maxAgents: 2,
    forbiddenTools: ["python_tool"],
    requireVerification: false,
  },
  {
    label: "Autonomous Vehicle Safety",
    emoji: "🚗",
    prompt:
      "Audit AI sensor fusion safety in autonomous vehicles, evaluate LiDAR edge-case failures, and verify all critical safety claims.",
    maxAgents: 4,
    requireVerification: true,
  },
  {
    label: "Semiconductor Market Trends",
    emoji: "🔬",
    prompt:
      "Research quarterly revenue trends and supply-chain bottlenecks across AI semiconductor foundries and draft a concise executive brief.",
    maxAgents: 3,
    requireVerification: false,
  },
];

const AVAILABLE_TOOLS = [
  { id: "python_tool", label: "Python Sandbox (subprocess isolated)" },
  { id: "web_search", label: "Web Search (Tavily/Ground truth)" },
  { id: "document_retriever", label: "Document Retriever (Local RAG)" },
];

export default function TaskSubmitForm() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("");
  const [activeChip, setActiveChip] = useState<string | null>(null);
  const [showConstraints, setShowConstraints] = useState(false);
  const [maxAgents, setMaxAgents] = useState<number | "">("");
  const [requireVerification, setRequireVerification] = useState(false);
  const [forbiddenTools, setForbiddenTools] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleSelectPreset = (preset: PresetItem) => {
    setActiveChip(preset.label);
    setPrompt(preset.prompt);
    if (preset.maxAgents !== undefined) setMaxAgents(preset.maxAgents);
    if (preset.requireVerification !== undefined) setRequireVerification(preset.requireVerification);
    if (preset.forbiddenTools !== undefined) setForbiddenTools(preset.forbiddenTools);
    setError(null);
  };

  const toggleForbiddenTool = (toolId: string) => {
    setForbiddenTools((prev) =>
      prev.includes(toolId) ? prev.filter((t) => t !== toolId) : [...prev, toolId]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = prompt.trim();
    if (!trimmed) {
      setError("Please describe your research task before submitting.");
      return;
    }

    setLoading(true);
    setError(null);
    setStage("Decomposing task & extracting capabilities…");

    try {
      const constraints: Record<string, unknown> = {};
      if (typeof maxAgents === "number" && maxAgents > 0) {
        constraints.max_agents = maxAgents;
      }
      if (requireVerification) {
        constraints.require_verification = true;
      }
      if (forbiddenTools.length > 0) {
        constraints.forbidden_tools = forbiddenTools;
      }

      const res = await submitTask({
        user_prompt: trimmed,
        constraints: Object.keys(constraints).length > 0 ? constraints : undefined,
        auto_pipeline: true,
      });

      const execId = res.execution_id;
      setStage(
        `Synthesized ${res.architecture_spec.agents.length}-agent ${res.architecture_spec.topology} architecture — launched autonomous pipeline…`
      );

      if (execId) {
        router.push(`/run/${res.task_id}?exec=${execId}`);
      } else {
        const execution = await runExecution(res.task_id, 1);
        router.push(`/run/${res.task_id}?exec=${execution.execution_id}`);
      }
    } catch (err: unknown) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "An unexpected error occurred while communicating with the backend. Please check connection."
      );
      setLoading(false);
    }
  };

  return (
    <div className="card fade-up" style={{ padding: 0, overflow: "hidden" }}>
      {/* Form Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "16px 20px",
          borderBottom: "1px solid var(--border-soft)",
          background: "var(--bg-card-subtle)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 7,
              background: "rgba(99, 102, 241, 0.15)",
              border: "1px solid rgba(99, 102, 241, 0.3)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#818cf8",
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              Submit Research Task
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Dynamic synthesis, execution, diagnosis, and constraint-aware self-evolution
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={() => setShowConstraints(!showConstraints)}
          className={showConstraints ? "btn btn-primary btn-sm" : "btn btn-secondary btn-sm"}
          style={{ fontSize: 11 }}
        >
          {showConstraints ? "Hide Invariants ▲" : "Configure Constraints ▾"}
        </button>
      </div>

      {/* Preset Chips */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          padding: "10px 20px",
          borderBottom: "1px solid var(--border-soft)",
          flexWrap: "wrap",
          background: "rgba(255, 255, 255, 0.01)",
        }}
      >
        <span style={{ fontSize: 10, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.08em", marginRight: 4 }}>
          Research Presets:
        </span>
        {RESEARCH_PRESETS.map((preset) => (
          <button
            key={preset.label}
            type="button"
            onClick={() => handleSelectPreset(preset)}
            className={`btn btn-sm ${activeChip === preset.label ? "btn-primary" : "btn-secondary"}`}
            disabled={loading}
            style={{ fontSize: 11, padding: "4px 10px" }}
          >
            <span>{preset.emoji}</span>
            <span>{preset.label}</span>
          </button>
        ))}
      </div>

      {/* Constraints Panel (Collapsible) */}
      {showConstraints && (
        <div
          style={{
            padding: "16px 20px",
            background: "rgba(0, 0, 0, 0.25)",
            borderBottom: "1px solid var(--border-soft)",
            display: "flex",
            flexDirection: "column",
            gap: 14,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 11, fontWeight: 700, color: "#a5b4fc", textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Operational Constraints &amp; Hard Invariants
            </span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Inviolable during synthesis &amp; mutation
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16 }}>
            {/* Max Agents Budget */}
            <div className="form-group">
              <label className="form-label" htmlFor="max-agents-input">
                Max Agents Budget (Hard Cap)
              </label>
              <input
                id="max-agents-input"
                type="number"
                min="1"
                max="8"
                placeholder="e.g. 2 or 3"
                value={maxAgents}
                onChange={(e) => setMaxAgents(e.target.value ? parseInt(e.target.value) : "")}
                disabled={loading}
                className="form-control"
              />
              <span style={{ fontSize: 10, color: "var(--text-muted)" }}>
                Meta-controller will cluster subtasks if required
              </span>
            </div>

            {/* Verification Requirement */}
            <div className="form-group" style={{ justifyContent: "center" }}>
              <label className="form-label">Verification Gate</label>
              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  fontSize: 12,
                  color: "var(--text-primary)",
                  cursor: "pointer",
                  marginTop: 6,
                }}
              >
                <input
                  type="checkbox"
                  checked={requireVerification}
                  onChange={(e) => setRequireVerification(e.target.checked)}
                  disabled={loading}
                  style={{ width: 16, height: 16, accentColor: "#6366f1" }}
                />
                Require Independent Fact Verification
              </label>
              <span style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 4 }}>
                Forces synthetic verification node in architecture
              </span>
            </div>

            {/* Forbidden Tools Selector */}
            <div className="form-group">
              <label className="form-label">Forbidden Tool Restrictions</label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 4 }}>
                {AVAILABLE_TOOLS.map((tool) => {
                  const isForbidden = forbiddenTools.includes(tool.id);
                  return (
                    <button
                      key={tool.id}
                      type="button"
                      onClick={() => toggleForbiddenTool(tool.id)}
                      disabled={loading}
                      style={{
                        padding: "4px 8px",
                        borderRadius: 6,
                        fontSize: 10,
                        fontWeight: 600,
                        cursor: "pointer",
                        border: "1px solid",
                        background: isForbidden ? "rgba(244, 63, 94, 0.15)" : "rgba(255, 255, 255, 0.04)",
                        borderColor: isForbidden ? "rgba(244, 63, 94, 0.4)" : "var(--border)",
                        color: isForbidden ? "#fb7185" : "var(--text-secondary)",
                      }}
                      title={tool.label}
                    >
                      {isForbidden ? `✕ Blocked: ${tool.id}` : `+ Block ${tool.id}`}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error alert */}
      {error && (
        <div
          style={{
            margin: "16px 20px 0",
            padding: "10px 14px",
            borderRadius: 8,
            background: "rgba(244, 63, 94, 0.1)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            color: "#fb7185",
            fontSize: 12,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setError(null)}
            style={{ background: "none", border: "none", color: "#fb7185", cursor: "pointer", fontSize: 13 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Prompt Input Area */}
      <form onSubmit={handleSubmit} style={{ padding: "18px 20px" }}>
        <div className="form-group">
          <label className="form-label" htmlFor="task-prompt-input">
            Task Specification (Natural Language Prompt)
          </label>
          <textarea
            id="task-prompt-input"
            value={prompt}
            onChange={(e) => {
              setPrompt(e.target.value);
              setActiveChip(null);
            }}
            disabled={loading}
            placeholder="e.g. Investigate distributed consensus failure modes in Raft clusters, verify partition tolerance proofs, and produce an audited mitigation specification."
            className="form-control"
            style={{ minHeight: 96, fontSize: 13.5 }}
          />
        </div>

        {/* Footer controls & progress */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 14,
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "var(--text-muted)" }}>
            {loading ? (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="spinner" />
                <span style={{ color: "#a5b4fc", fontWeight: 600 }}>{stage}</span>
              </div>
            ) : prompt.trim() ? (
              <span>
                {prompt.trim().length} characters · Constraints:{" "}
                {maxAgents ? `max ${maxAgents} agents, ` : ""}
                {requireVerification ? "verification required, " : ""}
                {forbiddenTools.length ? `${forbiddenTools.length} tool(s) forbidden` : "standard invariants"}
              </span>
            ) : (
              <span>Select a research preset above or type your task prompt.</span>
            )}
          </div>

          <button
            id="forge-architecture-btn"
            type="submit"
            disabled={loading || !prompt.trim()}
            className="btn btn-primary"
            style={{ padding: "9px 20px" }}
          >
            {loading ? (
              <>
                <span className="spinner" />
                Processing Pipeline…
              </>
            ) : (
              <>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="5 3 19 12 5 21 5 3" />
                </svg>
                Synthesize Architecture &amp; Execute Run 1
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
