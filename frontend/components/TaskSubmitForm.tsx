"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitTask, runExecution } from "@/lib/api";

const EXAMPLES = [
  "Research the societal impact of generative AI on creative industries",
  "Write a Python data pipeline to process and visualize CSV files",
  "Analyze Q4 2025 sales trends and produce an executive summary",
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
    setStage("Analyzing task & synthesizing architecture…");

    try {
      const { task_id, architecture_spec } = await submitTask(trimmed);
      setStage(
        `Synthesized ${architecture_spec.agents.length}-agent ${architecture_spec.topology} topology — starting execution…`
      );
      const execution = await runExecution(task_id, 1);
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
      <form onSubmit={handleSubmit}>
        {/* Textarea */}
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={loading}
          placeholder="Describe a task for Agent Forge to solve…"
          className="input-field"
          style={{ minHeight: 110, marginBottom: 12 }}
        />

        {/* Example chips */}
        {!loading && !prompt && (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 16 }}>
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setPrompt(ex)}
                style={{
                  background: "rgba(99,102,241,0.07)",
                  border: "1px solid rgba(99,102,241,0.18)",
                  borderRadius: 99,
                  padding: "4px 12px",
                  fontSize: 11,
                  color: "#818cf8",
                  cursor: "pointer",
                  fontFamily: "inherit",
                  transition: "background .15s",
                }}
              >
                {ex.length > 52 ? ex.slice(0, 52) + "…" : ex}
              </button>
            ))}
          </div>
        )}

        {/* Footer row */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12 }}>
          {/* Status */}
          <div style={{ fontSize: 12, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 7, minHeight: 22 }}>
            {loading && (
              <>
                <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                <span style={{ color: "#818cf8" }}>{stage}</span>
              </>
            )}
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="btn btn-primary"
            style={{ whiteSpace: "nowrap", fontSize: 13 }}
          >
            {loading ? "Forging…" : "Forge Architecture →"}
          </button>
        </div>
      </form>
    </div>
  );
}
