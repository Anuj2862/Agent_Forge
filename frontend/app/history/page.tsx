"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import KPICard from "@/components/KPICard";
import EvolutionHistoryTable from "@/components/evaluation/EvolutionHistoryTable";
import { listTasks, listExecutions, TaskDetail, ExecutionDetail } from "@/lib/api";

export default function HistoryPage() {
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [executions, setExecutions] = useState<ExecutionDetail[]>([]);
  const [activeTab, setActiveTab] = useState<"tasks" | "memory">("tasks");
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [tData, eData] = await Promise.all([
          listTasks().catch(() => ({ tasks: [], total: 0 })),
          listExecutions().catch(() => ({ executions: [], total: 0 })),
        ]);
        if (tData.tasks) setTasks(tData.tasks);
        if (eData.executions) setExecutions(eData.executions);
      } catch (err) {
        console.error("Failed to load history data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const totalTasks = tasks.length;
  const completedCount = executions.filter((e) => e.status === "completed" || e.status === "success").length;
  const evolvedCount = tasks.filter((t) => !!t.architecture_versions?.v2).length;

  const filteredTasks = tasks.filter((t) => {
    const spec = t.task_spec || {};
    const prompt = typeof t.user_prompt === "string" && t.user_prompt ? t.user_prompt : String(spec.user_prompt || "");
    const matchSearch =
      !searchTerm ||
      t.task_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      prompt.toLowerCase().includes(searchTerm.toLowerCase());
    const matchStatus =
      statusFilter === "all" ||
      (statusFilter === "evolved" && !!t.architecture_versions?.v2) ||
      (statusFilter === "baseline" && !t.architecture_versions?.v2);
    return matchSearch && matchStatus;
  });

  return (
    <div style={{ maxWidth: 1360, margin: "0 auto", display: "flex", flexDirection: "column", gap: 22 }}>
      {/* ── Page Header ─────────────────────────────────────────── */}
      <div className="fade-up" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 14 }}>
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
                Audited Log
              </span>
            </div>
            <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
              Persistent Multi-Agent Research History
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
            Experiments &amp; Execution History
          </h1>
          <p style={{ fontSize: 13.5, color: "var(--text-secondary)", lineHeight: 1.55, maxWidth: 760 }}>
            Inspect all synthesized multi-agent architectures, execution timelines, evaluated ratings, and deterministic evolution decisions.
          </p>
        </div>

        <Link href="/compose" className="btn btn-primary" style={{ padding: "9px 18px" }}>
          + Launch New Experiment
        </Link>
      </div>

      {/* ── Translucent KPI Cards Row ───────────────────────────── */}
      <div className="fade-up delay-1">
        <div className="kpi-grid">
          <KPICard
            label="Total Experiments"
            value={loading ? "..." : totalTasks}
            subtext="Persisted research sessions"
            accentColor="#3B82F6"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 20v-6M6 20V10M18 20V4" />
              </svg>
            }
          />

          <KPICard
            label="Completed Runs"
            value={loading ? "..." : completedCount}
            subtext="Evaluated & verified"
            accentColor="#10B981"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            }
          />

          <KPICard
            label="Evolved (V2) Tasks"
            value={loading ? "..." : evolvedCount}
            subtext="Addressed failure critiques"
            accentColor="#22D3EE"
            delta={evolvedCount > 0 ? { value: `${evolvedCount} evolved`, type: "positive" } : undefined}
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 2v6h-6" />
                <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
              </svg>
            }
          />

          <KPICard
            label="ACID Storage"
            value="SQLite"
            subtext="Persistent relational database"
            accentColor="#A78BFA"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <ellipse cx="12" cy="5" rx="9" ry="3" />
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
              </svg>
            }
          />
        </div>
      </div>

      {/* ── View Switcher & Filter Toolbar ──────────────────────── */}
      <div className="card fade-up delay-2" style={{ padding: "0", overflow: "hidden" }}>
        <div
          style={{
            padding: "14px 20px",
            background: "var(--bg-card-subtle)",
            borderBottom: "1px solid var(--border-soft)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          {/* Tabs */}
          <div style={{ display: "flex", gap: 6 }}>
            <button
              onClick={() => setActiveTab("tasks")}
              className={`btn btn-sm ${activeTab === "tasks" ? "btn-primary" : "btn-ghost"}`}
              style={{ fontSize: 12 }}
            >
              All Task Experiments ({tasks.length})
            </button>
            <button
              onClick={() => setActiveTab("memory")}
              className={`btn btn-sm ${activeTab === "memory" ? "btn-primary" : "btn-ghost"}`}
              style={{ fontSize: 12 }}
            >
              Evolutionary Memory Log
            </button>
          </div>

          {activeTab === "tasks" && (
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <input
                type="text"
                placeholder="Search by ID or task prompt..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="form-control"
                style={{ width: 260, fontSize: 12, padding: "6px 12px" }}
              />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="form-control"
                style={{ width: 160, fontSize: 12, padding: "6px 26px 6px 10px" }}
                aria-label="Filter status"
              >
                <option value="all">All Stages</option>
                <option value="evolved">★ Evolved (V2)</option>
                <option value="baseline">Baseline Only (V1)</option>
              </select>
            </div>
          )}
        </div>

        {activeTab === "tasks" ? (
          <div style={{ overflowX: "auto" }}>
            {loading ? (
              <div style={{ padding: "40px", textAlign: "center", color: "var(--text-muted)" }}>
                <div className="spinner" style={{ marginBottom: 10 }} />
                <div>Loading historical experiments...</div>
              </div>
            ) : filteredTasks.length === 0 ? (
              <div className="empty-state" style={{ margin: "20px" }}>
                <div className="empty-state-icon">📋</div>
                <div className="empty-state-title">No matching experiments found</div>
                <div className="empty-state-desc">
                  Try adjusting your search terms or filter criteria.
                </div>
              </div>
            ) : (
              <table className="research-table">
                <thead>
                  <tr>
                    <th>Task ID</th>
                    <th>Task Objective</th>
                    <th>Topology</th>
                    <th>Agents</th>
                    <th>Status</th>
                    <th>Composite Score</th>
                    <th style={{ textAlign: "right" }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTasks.map((t) => {
                    const hasV2 = !!t.architecture_versions?.v2;
                    const rating = t.latest_evaluation?.success_rating ?? t.latest_evaluation?.metrics?.overall_score;
                    const spec = t.task_spec || {};
                    const prompt = typeof t.user_prompt === "string" && t.user_prompt ? t.user_prompt : String(spec.user_prompt || "Multi-Agent Research Task");
                    const taskType = String(t.task_type || spec.task_type || "research");
                    const complexity = String(t.complexity || spec.complexity || "medium");
                    const agentCount = t.architecture_spec?.agents?.length || 2;
                    return (
                      <tr key={t.task_id}>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "#22D3EE" }}>
                          {t.task_id}
                        </td>
                        <td style={{ maxWidth: 360 }}>
                          <div style={{ fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {prompt}
                          </div>
                          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                            {taskType} • {complexity}
                          </div>
                        </td>
                        <td>
                          <span className="badge badge-indigo">
                            {t.architecture_spec?.topology || "parallel"}
                          </span>
                        </td>
                        <td>
                          <span style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                            {agentCount} {agentCount === 1 ? "Agent" : "Agents"}
                          </span>
                        </td>
                        <td>
                          {hasV2 ? (
                            <span className="badge badge-emerald" style={{ fontSize: 10 }}>
                              ★ V2 Mutated
                            </span>
                          ) : (
                            <span className="badge badge-slate" style={{ fontSize: 10 }}>
                              V1 Baseline
                            </span>
                          )}
                        </td>
                        <td style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700 }}>
                          {rating !== undefined ? (
                            <span style={{ color: rating >= 0.75 ? "#34D399" : rating >= 0.5 ? "#FBBF24" : "#F87171" }}>
                              {(rating * 100).toFixed(1)}%
                            </span>
                          ) : (
                            <span style={{ color: "var(--text-muted)" }}>—</span>
                          )}
                        </td>
                        <td style={{ textAlign: "right" }}>
                          <Link
                            href={`/run/${t.task_id}`}
                            className="btn btn-secondary btn-sm"
                            style={{ fontSize: 11, padding: "3px 10px" }}
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
        ) : (
          <div style={{ padding: "16px" }}>
            <EvolutionHistoryTable />
          </div>
        )}
      </div>
    </div>
  );
}
