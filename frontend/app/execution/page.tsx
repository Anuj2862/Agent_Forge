"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  listExecutions,
  listTasks,
  AgentLog,
} from "@/lib/api";
import ExecutionTimeline from "@/components/execution/ExecutionTimeline";

export default function ExecutionPage() {
  const [executions, setExecutions] = useState<any[]>([]);
  const [selectedExecId, setSelectedExecId] = useState<string>("");
  const [execData, setExecData] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"timeline" | "raw" | "tools">("timeline");
  const [loading, setLoading] = useState<boolean>(true);

  // Load available executions
  useEffect(() => {
    async function loadExecutions() {
      try {
        setLoading(true);
        const data = await listExecutions();
        if (data.executions && data.executions.length > 0) {
          setExecutions(data.executions);
          setSelectedExecId(data.executions[0].execution_id);
        } else {
          // Check if there are any tasks with executions
          const tasksData = await listTasks();
          if (tasksData.tasks && tasksData.tasks.length > 0) {
            // Task without separate execution list, we can load task detail
            const firstTask = await api.get(`/tasks/${tasksData.tasks[0].task_id}`);
            if (firstTask.data.latest_execution) {
              setExecData(firstTask.data.latest_execution);
            }
          }
        }
      } catch (err) {
        console.error("Failed to load executions", err);
      } finally {
        setLoading(false);
      }
    }
    loadExecutions();
  }, []);

  // When selected execution changes, load full execution data
  useEffect(() => {
    if (!selectedExecId) return;
    async function loadExecDetails() {
      try {
        const res = await api.get(`/execution/${selectedExecId}`);
        setExecData(res.data);
      } catch (err) {
        console.error("Failed to load execution details", err);
      }
    }
    loadExecDetails();
  }, [selectedExecId]);

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 16 }}>
        <span className="spinner" style={{ width: 36, height: 36 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading execution runtime records…</p>
      </div>
    );
  }

  const logs: AgentLog[] = execData?.agent_logs || [];
  const totalToolCalls = logs.reduce((acc, l) => acc + (l.tool_calls?.length || 0), 0);

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "24px 20px 80px" }}>
      {/* Top selector & Action bar */}
      <div
        className="fade-up"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
          marginBottom: 24,
          padding: "16px 20px",
          background: "var(--bg-card)",
          borderRadius: 12,
          border: "1px solid var(--border)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Execution Trace:
          </span>
          {executions.length > 0 ? (
            <select
              value={selectedExecId}
              onChange={(e) => setSelectedExecId(e.target.value)}
              style={{
                background: "var(--bg-secondary)",
                color: "#f1f5f9",
                border: "1px solid var(--border)",
                borderRadius: 6,
                padding: "6px 12px",
                fontSize: 13,
                cursor: "pointer",
              }}
            >
              {executions.map((e) => (
                <option key={e.execution_id} value={e.execution_id}>
                  {e.execution_id} (Run #{e.run_number || 1} · {e.status})
                </option>
              ))}
            </select>
          ) : (
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No execution traces logged yet</span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {execData?.task_id && (
            <>
              <Link
                href={`/architecture`}
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: "7px 14px" }}
              >
                View Architecture Spec
              </Link>
              <Link
                href={`/run/${execData.task_id}?exec=${execData.execution_id}`}
                className="btn btn-primary"
                style={{ fontSize: 12, padding: "7px 14px" }}
              >
                Live Interactive Run
              </Link>
            </>
          )}
        </div>
      </div>

      {execData ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Execution Metric KPI Cards */}
          <div
            className="fade-up"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: 16,
            }}
          >
            <div className="card" style={{ padding: "18px 20px" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Execution Status
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 6 }}>
                <div className={`status-dot ${execData.status === "completed" ? "live" : "standby"}`} />
                <span style={{ fontSize: 18, fontWeight: 800, color: execData.status === "completed" ? "#34d399" : "#f59e0b", textTransform: "capitalize" }}>
                  {execData.status || "Unknown"}
                </span>
              </div>
            </div>

            <div className="card" style={{ padding: "18px 20px" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Total Duration
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#38bdf8", marginTop: 4 }}>
                {execData.duration_seconds !== undefined
                  ? `${execData.duration_seconds.toFixed(3)}s`
                  : "0.02s"}
              </div>
            </div>

            <div className="card" style={{ padding: "18px 20px" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Agents Executed
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#818cf8", marginTop: 4 }}>
                {logs.length} Agents
              </div>
            </div>

            <div className="card" style={{ padding: "18px 20px" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Tool Invocations
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#c084fc", marginTop: 4 }}>
                {totalToolCalls} Calls
              </div>
            </div>

            <div className="card" style={{ padding: "18px 20px" }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
                Run Iteration
              </div>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#f1f5f9", marginTop: 4 }}>
                Run #{execData.run_number || 1}
              </div>
            </div>
          </div>

          {/* Detailed Timeline and Output Tabs */}
          <div className="card fade-up" style={{ padding: "24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 700 }}>
                  LangGraph Agent Execution Pipeline
                </h3>
                <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                  Step-by-step trace of each agent node invoking tools and generating intermediate states
                </p>
              </div>

              {/* View Switcher Tabs */}
              <div style={{ display: "flex", gap: 6, background: "var(--bg-secondary)", padding: 4, borderRadius: 8 }}>
                <button
                  onClick={() => setActiveTab("timeline")}
                  style={{
                    padding: "5px 12px",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    border: "none",
                    background: activeTab === "timeline" ? "var(--bg-card)" : "transparent",
                    color: activeTab === "timeline" ? "#e2e8f0" : "var(--text-muted)",
                  }}
                >
                  Visual Timeline
                </button>
                <button
                  onClick={() => setActiveTab("tools")}
                  style={{
                    padding: "5px 12px",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    border: "none",
                    background: activeTab === "tools" ? "var(--bg-card)" : "transparent",
                    color: activeTab === "tools" ? "#e2e8f0" : "var(--text-muted)",
                  }}
                >
                  Tool Calls ({totalToolCalls})
                </button>
                <button
                  onClick={() => setActiveTab("raw")}
                  style={{
                    padding: "5px 12px",
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    border: "none",
                    background: activeTab === "raw" ? "var(--bg-card)" : "transparent",
                    color: activeTab === "raw" ? "#e2e8f0" : "var(--text-muted)",
                  }}
                >
                  Synthesized Output
                </button>
              </div>
            </div>

            {/* Tab 1: Timeline */}
            {activeTab === "timeline" && (
              <div style={{ maxWidth: 880, margin: "0 auto", padding: "10px 0" }}>
                {logs.length > 0 ? (
                  <ExecutionTimeline logs={logs} />
                ) : (
                  <div style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    No agent logs recorded in this execution trace.
                  </div>
                )}
              </div>
            )}

            {/* Tab 2: Tool Calls */}
            {activeTab === "tools" && (
              <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                {logs.flatMap((l) => l.tool_calls || []).length > 0 ? (
                  logs.flatMap((l, lIdx) =>
                    (l.tool_calls || []).map((tc, tcIdx) => (
                      <div
                        key={`${lIdx}-${tcIdx}`}
                        style={{
                          padding: "14px 16px",
                          borderRadius: 8,
                          background: "var(--bg-secondary)",
                          border: "1px solid var(--border-soft)",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                          <span className="badge badge-cyan" style={{ fontSize: 11 }}>
                            ⚡ {tc.tool}
                          </span>
                          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                            Agent: {l.agent_name || l.agent_id}
                          </span>
                        </div>
                        {tc.query && (
                          <div style={{ fontSize: 12, color: "#e2e8f0", marginBottom: 6 }}>
                            <strong style={{ color: "var(--text-muted)" }}>Query: </strong>
                            {tc.query}
                          </div>
                        )}
                        {tc.output && (
                          <div
                            style={{
                              fontSize: 11,
                              fontFamily: "monospace",
                              padding: "8px 12px",
                              background: "rgba(0,0,0,0.3)",
                              borderRadius: 6,
                              color: "#94a3b8",
                            }}
                          >
                            {tc.output}
                          </div>
                        )}
                      </div>
                    ))
                  )
                ) : (
                  <div style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)" }}>
                    No external tool calls executed during this run.
                  </div>
                )}
              </div>
            )}

            {/* Tab 3: Synthesized Output */}
            {activeTab === "raw" && (
              <div>
                <pre
                  style={{
                    background: "var(--bg-secondary)",
                    padding: "20px",
                    borderRadius: 8,
                    border: "1px solid var(--border-soft)",
                    fontSize: 12,
                    lineHeight: 1.6,
                    color: "#cbd5e1",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    maxHeight: 500,
                    overflowY: "auto",
                  }}
                >
                  {execData.final_output ||
                    execData.raw_output ||
                    JSON.stringify(execData, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: "48px 24px", textAlign: "center" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>No Executions Found</h3>
          <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>
            Run a task execution from the home workspace to observe LangGraph execution traces.
          </p>
          <Link href="/" className="btn btn-primary" style={{ display: "inline-block" }}>
            + Create New Task
          </Link>
        </div>
      )}
    </div>
  );
}
