"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  listTasks,
  compareTaskRuns,
  runExecution,
  evaluateExecution,
  TaskComparisonResponse,
  TaskDetail,
  AgentConfig,
  api,
} from "@/lib/api";
import TaskSelector from "@/components/TaskSelector";
import DecisionVerdictCard from "@/components/DecisionVerdictCard";

export default function EvolutionPage() {
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [taskData, setTaskData] = useState<TaskDetail | null>(null);
  const [comparison, setComparison] = useState<TaskComparisonResponse | null>(null);
  const [isExecutingV2, setIsExecutingV2] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadTasks() {
      try {
        setLoading(true);
        const data = await listTasks();
        if (data.tasks && data.tasks.length > 0) {
          setTasks(data.tasks);
          setSelectedTaskId(data.tasks[0].task_id);
        }
      } catch (err) {
        console.error("Failed to load tasks", err);
      } finally {
        setLoading(false);
      }
    }
    loadTasks();
  }, []);

  useEffect(() => {
    if (!selectedTaskId) return;
    async function loadComparison() {
      try {
        setError(null);
        const tResp = await api.get(`/tasks/${selectedTaskId}`);
        setTaskData(tResp.data);

        const comp = await compareTaskRuns(selectedTaskId);
        setComparison(comp);
      } catch (err: unknown) {
        console.error("Failed to load comparison", err);
      }
    }
    loadComparison();
  }, [selectedTaskId]);

  const handleExecuteRun2 = async () => {
    if (!selectedTaskId) return;
    setIsExecutingV2(true);
    setError(null);
    try {
      const execResult = await runExecution(selectedTaskId, 2);
      await evaluateExecution(execResult.execution_id, selectedTaskId);
      const comp = await compareTaskRuns(selectedTaskId);
      setComparison(comp);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to execute Run 2");
    } finally {
      setIsExecutingV2(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 14 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading comparative evolution analytics…</p>
      </div>
    );
  }

  const hasV2 = !!taskData?.architecture_versions?.v2;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Target Task Selector */}
      <TaskSelector
        tasks={tasks}
        selectedTaskId={selectedTaskId}
        onSelectTaskId={setSelectedTaskId}
        label="Evolution Task"
        actionRight={
          selectedTaskId ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Link href="/history" className="btn btn-secondary btn-sm">
                Memory Log →
              </Link>
              <Link href={`/run/${selectedTaskId}`} className="btn btn-primary btn-sm">
                Open Full Workbench
              </Link>
            </div>
          ) : undefined
        }
      />

      {error && (
        <div
          className="fade-up"
          style={{
            padding: "12px 18px",
            borderRadius: 8,
            background: "rgba(244, 63, 94, 0.12)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            color: "#fb7185",
            fontSize: 12.5,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>⚠ {error}</span>
          <button
            onClick={() => setError(null)}
            style={{ background: "none", border: "none", color: "#fb7185", cursor: "pointer", fontSize: 13 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Header Banner */}
      <div
        className="card fade-up"
        style={{
          padding: "20px 24px",
          background: "linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%)",
          borderColor: "rgba(99, 102, 241, 0.25)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 6 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 18 }}>🧬</span>
            <h2 style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)" }}>
              Empirical Evolution Tracker &amp; Selection Gating
            </h2>
          </div>
          {hasV2 && (
            <span className="badge badge-emerald">
              ★ Candidate V2 Synthesized
            </span>
          )}
        </div>
        <p style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 880, lineHeight: 1.5 }}>
          Visualizing the empirical delta between the baseline synthesized architecture (Run 1) and the autonomously evolved graph (Run 2) after addressing reflection critiques.
        </p>
      </div>

      {/* Deterministic Evolution Decision Banner */}
      <DecisionVerdictCard
        decision={comparison?.evolution_decision || taskData?.evolution_decision}
        hasRuns={!!(comparison?.run_1 && comparison?.run_2)}
      />

      {/* Comparison Content */}
      {comparison && comparison.has_comparison ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Comparison Delta Table */}
          <div className="card fade-up">
            <div className="card-header">
              <div className="card-title">
                Performance Metrics Delta (Baseline V1 vs Candidate V2)
              </div>
              <span className="badge badge-indigo">Empirical Deltas</span>
            </div>

            <div style={{ overflowX: "auto" }}>
              <table className="research-table">
                <thead>
                  <tr>
                    <th>Metric Dimension</th>
                    <th>Run #1 (Initial Baseline)</th>
                    <th>Run #2 (Mutated V2)</th>
                    <th>Delta (Δ)</th>
                    <th>Evaluation Impact</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontWeight: 600 }}>Task Success Rate</td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                      {comparison.run_1?.evaluation?.metrics?.task_success !== undefined
                        ? `${(comparison.run_1.evaluation.metrics.task_success * 100).toFixed(0)}%`
                        : "N/A"}
                    </td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#34d399" }}>
                      {comparison.run_2?.evaluation?.metrics?.task_success !== undefined
                        ? `${(comparison.run_2.evaluation.metrics.task_success * 100).toFixed(0)}%`
                        : "N/A"}
                    </td>
                    <td
                      style={{
                        fontFamily: "var(--font-mono, monospace)",
                        fontWeight: 700,
                        color: (comparison.deltas?.task_success ?? 0) >= 0 ? "#34d399" : "#fb7185",
                      }}
                    >
                      {comparison.deltas?.task_success !== undefined
                        ? `${comparison.deltas.task_success >= 0 ? "+" : ""}${(comparison.deltas.task_success * 100).toFixed(1)}%`
                        : "0.0%"}
                    </td>
                    <td>
                      <span className={(comparison.deltas?.task_success ?? 0) >= 0 ? "badge badge-emerald" : "badge badge-rose"}>
                        {(comparison.deltas?.task_success ?? 0) >= 0 ? "↑ Improved" : "↓ Regressed"}
                      </span>
                    </td>
                  </tr>

                  <tr>
                    <td style={{ fontWeight: 600 }}>Output Quality</td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                      {comparison.run_1?.evaluation?.metrics?.quality !== undefined
                        ? `${(comparison.run_1.evaluation.metrics.quality * 100).toFixed(0)}%`
                        : "N/A"}
                    </td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#34d399" }}>
                      {comparison.run_2?.evaluation?.metrics?.quality !== undefined
                        ? `${(comparison.run_2.evaluation.metrics.quality * 100).toFixed(0)}%`
                        : "N/A"}
                    </td>
                    <td
                      style={{
                        fontFamily: "var(--font-mono, monospace)",
                        fontWeight: 700,
                        color: (comparison.deltas?.quality ?? 0) >= 0 ? "#34d399" : "#fb7185",
                      }}
                    >
                      {comparison.deltas?.quality !== undefined
                        ? `${comparison.deltas.quality >= 0 ? "+" : ""}${(comparison.deltas.quality * 100).toFixed(1)}%`
                        : "0.0%"}
                    </td>
                    <td>
                      <span className={(comparison.deltas?.quality ?? 0) >= 0 ? "badge badge-emerald" : "badge badge-rose"}>
                        {(comparison.deltas?.quality ?? 0) >= 0 ? "↑ Enhanced" : "↓ Regressed"}
                      </span>
                    </td>
                  </tr>

                  <tr>
                    <td style={{ fontWeight: 600 }}>Factual Accuracy</td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                      {comparison.run_1?.evaluation?.metrics?.accuracy !== undefined
                        ? `${(comparison.run_1.evaluation.metrics.accuracy * 100).toFixed(0)}%`
                        : "N/A"}
                    </td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#34d399" }}>
                      {comparison.run_2?.evaluation?.metrics?.accuracy !== undefined
                        ? `${(comparison.run_2.evaluation.metrics.accuracy * 100).toFixed(0)}%`
                        : "N/A"}
                    </td>
                    <td
                      style={{
                        fontFamily: "var(--font-mono, monospace)",
                        fontWeight: 700,
                        color: (comparison.deltas?.accuracy ?? 0) >= 0 ? "#34d399" : "#fb7185",
                      }}
                    >
                      {comparison.deltas?.accuracy !== undefined
                        ? `${comparison.deltas.accuracy >= 0 ? "+" : ""}${(comparison.deltas.accuracy * 100).toFixed(1)}%`
                        : "0.0%"}
                    </td>
                    <td>
                      <span className={(comparison.deltas?.accuracy ?? 0) >= 0 ? "badge badge-emerald" : "badge badge-rose"}>
                        {(comparison.deltas?.accuracy ?? 0) >= 0 ? "↑ Corroborated" : "↓ Regressed"}
                      </span>
                    </td>
                  </tr>

                  <tr>
                    <td style={{ fontWeight: 600 }}>Agent Team Count</td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                      {comparison.run_1?.architecture?.agents?.length || 1} agents
                    </td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                      {comparison.run_2?.architecture?.agents?.length || 1} agents
                    </td>
                    <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#818cf8" }}>
                      {(comparison.deltas?.agent_count ?? 0) >= 0 ? "+" : ""}
                      {comparison.deltas?.agent_count ?? 0}
                    </td>
                    <td>
                      <span className="badge badge-slate">Topology Shift</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Topological Graph Diff */}
          {comparison.architecture_diff && (
            <div className="card fade-up">
              <div className="card-header">
                <div className="card-title">
                  Topological Graph Mutation Diff
                </div>
                <span className="badge badge-emerald">Graph Mutated</span>
              </div>

              <div style={{ padding: "18px 20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <div style={{ background: "rgba(16, 185, 129, 0.05)", border: "1px solid rgba(16, 185, 129, 0.2)", borderRadius: 8, padding: 14 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#34d399", textTransform: "uppercase", marginBottom: 8 }}>
                    + Added Agent Nodes
                  </div>
                  {comparison.architecture_diff.added_agents?.length ? (
                    comparison.architecture_diff.added_agents.map((a: AgentConfig) => (
                      <div key={a.agent_id} style={{ fontSize: 12, color: "var(--text-primary)", marginBottom: 4 }}>
                        • <strong>{a.name}</strong> ({a.role}) — tools: {a.tools?.join(", ") || "cognitive"}
                      </div>
                    ))
                  ) : (
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                      Terminal agent augmented with independent verification capability
                    </span>
                  )}
                </div>

                <div style={{ background: "rgba(99, 102, 241, 0.05)", border: "1px solid rgba(99, 102, 241, 0.2)", borderRadius: 8, padding: 14 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#818cf8", textTransform: "uppercase", marginBottom: 8 }}>
                    Edge &amp; Dependency Rewiring
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                    Dependencies re-routed to route upstream synthesis through verification stage with DAG cycle validation.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-title">Awaiting Dual-Run Evidence</div>
          <div className="empty-state-desc">
            Comparative evolution analysis requires complete execution and evaluation records for both Run #1 and Run #2.
          </div>
          {hasV2 ? (
            <button
              onClick={handleExecuteRun2}
              disabled={isExecutingV2}
              className="btn btn-emerald btn-sm"
            >
              {isExecutingV2 ? "Executing Architecture V2…" : "▶ Execute Architecture V2 Now"}
            </button>
          ) : (
            <Link href={`/run/${selectedTaskId}`} className="btn btn-primary btn-sm">
              Go to Run Workbench →
            </Link>
          )}
        </div>
      )}
    </div>
  );
}
