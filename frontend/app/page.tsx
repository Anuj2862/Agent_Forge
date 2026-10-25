"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import KPICard from "@/components/KPICard";
import ResearchLabOverview from "@/components/ResearchLabOverview";
import { listTasks, listExecutions, getMemoryStatus, TaskDetail, ExecutionDetail } from "@/lib/api";

const PIPELINE_STEPS = [
  { num: 1, label: "Task & Constraints", status: "done" },
  { num: 2, label: "V1 Synthesis", status: "done" },
  { num: 3, label: "LangGraph Execution", status: "active" },
  { num: 4, label: "Evaluation", status: "pending" },
  { num: 5, label: "Failure Diagnosis", status: "pending" },
  { num: 6, label: "Architecture Mutation", status: "pending" },
  { num: 7, label: "V2 Execution", status: "pending" },
  { num: 8, label: "Comparative Analysis", status: "pending" },
  { num: 9, label: "Evolution Verdict", status: "pending" },
  { num: 10, label: "Evolutionary Memory", status: "pending" },
];

export default function Home() {
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [executions, setExecutions] = useState<ExecutionDetail[]>([]);
  const [memoryCount, setMemoryCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true);
        const [taskRes, execRes, memRes] = await Promise.all([
          listTasks().catch(() => ({ tasks: [], total: 0 })),
          listExecutions().catch(() => ({ executions: [], total: 0 })),
          getMemoryStatus().catch(() => ({ total_records: 0 })),
        ]);
        if (taskRes.tasks) setTasks(taskRes.tasks);
        if (execRes.executions) setExecutions(execRes.executions);
        if (typeof memRes.total_records === "number") setMemoryCount(memRes.total_records);
      } catch (err) {
        console.error("Failed to fetch dashboard metrics", err);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  // Compute real metrics
  const totalExperiments = tasks.length;
  const runningExecutions = executions.filter((e) => e.status === "running").length;
  const completedExecutions = executions.filter((e) => e.status === "success" || e.status === "completed").length;
  const totalArchitectures = tasks.reduce((acc, t) => {
    const v2 = t.architecture_versions?.v2 ? 1 : 0;
    return acc + 1 + v2;
  }, 0);

  return (
    <div style={{ maxWidth: 1360, margin: "0 auto", display: "flex", flexDirection: "column", gap: 24 }}>
      {/* ── Page Header & Thesis Context ────────────────────────── */}
      <div className="fade-up" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                padding: "3px 12px",
                borderRadius: 99,
                background: "rgba(34, 211, 238, 0.1)",
                border: "1px solid rgba(34, 211, 238, 0.25)",
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 700, color: "#22D3EE", letterSpacing: "0.06em", textTransform: "uppercase" }}>
                Research Command Center
              </span>
            </div>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Thesis: Failure-Driven, Constraint-Aware Self-Evolution
            </span>
          </div>

          <h1
            style={{
              fontSize: "clamp(1.5rem, 2.5vw, 2.1rem)",
              fontWeight: 800,
              letterSpacing: "-0.025em",
              lineHeight: 1.25,
              color: "var(--text-primary)",
              marginBottom: 6,
            }}
          >
            Autonomous Multi-Agent Architecture Synthesis &amp; Evolution
          </h1>
          <p style={{ fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.55, maxWidth: 820 }}>
            Agent Forge derives constraint-governed multi-agent topologies, dispatches real LangGraph state machines,
            diagnoses execution vulnerabilities via multi-metric reflection, and evolves architectures with deterministic decision gates.
          </p>
        </div>

        <div style={{ display: "flex", gap: 10, alignSelf: "center" }}>
          <Link href="/compose" className="btn btn-primary" style={{ padding: "9px 18px" }}>
            <span>+</span> Launch New Experiment
          </Link>
          <Link href="/architecture" className="btn btn-secondary" style={{ padding: "9px 16px" }}>
            Architecture Studio →
          </Link>
        </div>
      </div>

      {/* ── Translucent KPI Metrics Row (Network Visible Behind) ──── */}
      <div className="fade-up delay-1">
        <div className="kpi-grid">
          <KPICard
            label="Total Experiments"
            value={loading ? "..." : totalExperiments}
            subtext="Persisted research tasks"
            accentColor="#3B82F6"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
              </svg>
            }
          />

          <KPICard
            label="Running Executions"
            value={loading ? "..." : runningExecutions}
            subtext="Active LangGraph pipelines"
            accentColor="#22D3EE"
            delta={runningExecutions > 0 ? { value: "Active", type: "positive" } : { value: "Idle", type: "neutral" }}
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
            }
          />

          <KPICard
            label="Completed Runs"
            value={loading ? "..." : completedExecutions}
            subtext="Evaluated & persisted"
            accentColor="#10B981"
            delta={completedExecutions > 0 ? { value: `${completedExecutions} done`, type: "positive" } : undefined}
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            }
          />

          <KPICard
            label="Architecture Specs"
            value={loading ? "..." : totalArchitectures}
            subtext="V1 base & V2 mutated graphs"
            accentColor="#A78BFA"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="5" r="3" />
                <circle cx="6" cy="19" r="3" />
                <circle cx="18" cy="19" r="3" />
              </svg>
            }
          />

          <KPICard
            label="Evolution Memory"
            value={loading ? "..." : memoryCount}
            subtext="ACID experiential records"
            accentColor="#2DD4BF"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <ellipse cx="12" cy="5" rx="9" ry="3" />
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
              </svg>
            }
          />
        </div>
      </div>

      {/* ── Research Thesis Invariants & Foundation ──────────────── */}
      <div className="fade-up delay-2">
        <ResearchLabOverview />
      </div>

      {/* ── Recent Research Executions Table ──────────────────────── */}
      <div className="card fade-up delay-2" style={{ overflow: "hidden" }}>
        <div className="card-header">
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 16 }}>⚡</span>
            <div>
              <div className="card-title">Recent Autonomous Executions</div>
              <div className="card-subtitle">Real-time runs and persisted task traces</div>
            </div>
          </div>
          <Link href="/history" className="btn btn-secondary btn-sm">
            View All History ({tasks.length}) →
          </Link>
        </div>

        <div style={{ overflowX: "auto" }}>
          {loading ? (
            <div style={{ padding: "32px", textAlign: "center", color: "var(--text-muted)" }}>
              <div className="spinner" style={{ marginBottom: 10 }} />
              <div>Loading real executions from database...</div>
            </div>
          ) : tasks.length === 0 ? (
            <div className="empty-state" style={{ margin: "20px" }}>
              <div className="empty-state-icon">🔬</div>
              <div className="empty-state-title">No experiments launched yet</div>
              <div className="empty-state-desc">
                Submit your first research task to watch Agent Forge dynamically synthesize a multi-agent team and execute it.
              </div>
              <Link href="/compose" className="btn btn-primary btn-sm">
                + Launch First Experiment
              </Link>
            </div>
          ) : (
            <table className="research-table">
              <thead>
                <tr>
                  <th>Task ID</th>
                  <th>Task Prompt &amp; Objective</th>
                  <th>Constraints</th>
                  <th>Arch Status</th>
                  <th>Latest Rating</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {tasks.slice(0, 6).map((task) => {
                  const hasV2 = !!task.architecture_versions?.v2;
                  const evalScore = task.latest_evaluation?.success_rating ?? task.latest_evaluation?.metrics?.overall_score;
                  const taskSpec = task.task_spec || {};
                  const prompt = typeof task.user_prompt === "string" && task.user_prompt ? task.user_prompt : String(taskSpec.user_prompt || "Multi-Agent Research Task");
                  const taskType = String(task.task_type || taskSpec.task_type || "research");
                  const complexity = String(task.complexity || taskSpec.complexity || "medium");
                  const constraints = taskSpec.constraints as Record<string, unknown> | undefined;
                  return (
                    <tr key={task.task_id}>
                      <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "#22D3EE" }}>
                        {task.task_id}
                      </td>
                      <td style={{ maxWidth: 360 }}>
                        <div style={{ fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                          {prompt}
                        </div>
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                          Type: {taskType} • Complexity: {complexity}
                        </div>
                      </td>
                      <td>
                        <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                          <span className="badge badge-slate" style={{ fontSize: 10 }}>
                            max_agents: {String(constraints?.max_agents ?? "Auto")}
                          </span>
                          {Boolean(constraints?.require_verification) && (
                            <span className="badge badge-cyan" style={{ fontSize: 10 }}>
                              Verify
                            </span>
                          )}
                        </div>
                      </td>
                      <td>
                        {hasV2 ? (
                          <span className="badge badge-emerald" style={{ fontSize: 10 }}>
                            ★ Evolved (V2)
                          </span>
                        ) : (
                          <span className="badge badge-indigo" style={{ fontSize: 10 }}>
                            Synthesized (V1)
                          </span>
                        )}
                      </td>
                      <td style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
                        {evalScore !== undefined ? (
                          <span style={{ color: evalScore >= 0.75 ? "#34D399" : evalScore >= 0.5 ? "#FBBF24" : "#F87171" }}>
                            {(evalScore * 100).toFixed(1)}%
                          </span>
                        ) : (
                          <span style={{ color: "var(--text-muted)" }}>Pending</span>
                        )}
                      </td>
                      <td>
                        <Link
                          href={`/run/${task.task_id}`}
                          className="btn btn-secondary btn-sm"
                          style={{ fontSize: 11, padding: "3px 9px" }}
                        >
                          Inspect Run →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* ── 10-Stage Evolution Pipeline Architecture Map ─────────── */}
      <div className="card fade-up delay-3" style={{ padding: "18px 22px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", display: "flex", alignItems: "center", gap: 6 }}>
              <span>🔄</span> Full Autonomous Research Lifecycle
            </div>
            <div style={{ fontSize: 11.5, color: "var(--text-muted)" }}>
              The 10-stage execution and self-evolution sequence triggered automatically on task submission
            </div>
          </div>
          <span className="badge badge-cyan" style={{ fontSize: 10 }}>
            Automated End-to-End
          </span>
        </div>

        <div className="stepper" style={{ gap: 4 }}>
          {PIPELINE_STEPS.map((s, idx) => (
            <div key={s.num} style={{ display: "flex", alignItems: "center", flex: 1, minWidth: 100 }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                <div
                  className={`step-bubble ${s.status}`}
                  style={{
                    background: s.status === "done" ? "#10B981" : s.status === "active" ? "#2563EB" : "var(--bg-card-subtle)",
                    border: s.status === "active" ? "1px solid var(--accent-blue)" : "1px solid var(--border)",
                    color: s.status === "done" ? "#ffffff" : s.status === "active" ? "#ffffff" : "var(--text-muted)",
                  }}
                >
                  {s.num}
                </div>
                <span style={{ fontSize: 10, color: s.status === "active" ? "var(--accent-blue)" : "var(--text-secondary)", textAlign: "center", fontWeight: s.status === "active" ? 700 : 500 }}>
                  {s.label}
                </span>
              </div>
              {idx < PIPELINE_STEPS.length - 1 && (
                <div
                  style={{
                    flex: 1,
                    height: 1.5,
                    background: s.status === "done" ? "#10B981" : "var(--border)",
                    margin: "0 6px 16px",
                  }}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
