"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  listExecutions,
  listTasks,
  getExecution,
  getExecutionEventsHistory,
  subscribeToExecutionEvents,
  AgentLog,
  ExecutionDetail,
  TaskDetail,
  ExecutionEvent,
} from "@/lib/api";
import ExecutionTimeline from "@/components/execution/ExecutionTimeline";
import LiveExecutionStatus, { StreamConnectionStatus } from "@/components/execution/LiveExecutionStatus";
import TaskSelector from "@/components/TaskSelector";

export default function ExecutionPage() {
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [executions, setExecutions] = useState<ExecutionDetail[]>([]);
  const [selectedExecId, setSelectedExecId] = useState<string>("");
  const [execData, setExecData] = useState<ExecutionDetail | null>(null);
  const [activeTab, setActiveTab] = useState<"timeline" | "raw" | "tools">("timeline");
  const [loading, setLoading] = useState<boolean>(true);

  // Streaming & event states
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [streamState, setStreamState] = useState<StreamConnectionStatus>("disconnected");
  const [isStreaming, setIsStreaming] = useState(false);


  // Load available tasks & executions
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [tasksRes, execsRes] = await Promise.all([
          listTasks().catch(() => ({ tasks: [], total: 0 })),
          listExecutions().catch(() => ({ executions: [], total: 0 })),
        ]);

        if (tasksRes.tasks && tasksRes.tasks.length > 0) {
          setTasks(tasksRes.tasks);
          setSelectedTaskId(tasksRes.tasks[0].task_id);
        }

        if (execsRes.executions && execsRes.executions.length > 0) {
          setExecutions(execsRes.executions);
          setSelectedExecId(execsRes.executions[0].execution_id);
          setExecData(execsRes.executions[0]);
        }
      } catch (err) {
        console.error("Failed to load executions", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // When selected task changes, try to load its execution
  useEffect(() => {
    if (!selectedTaskId) return;
    async function loadTaskExecutions() {
      try {
        const res = await api.get(`/tasks/${selectedTaskId}`);
        if (res.data.latest_execution) {
          setExecData(res.data.latest_execution);
          setSelectedExecId(res.data.latest_execution.execution_id);
        }
      } catch (err) {
        console.error("Failed to load task executions", err);
      }
    }
    loadTaskExecutions();
  }, [selectedTaskId]);

  // When selected execution changes directly
  useEffect(() => {
    let unsub: (() => void) | null = null;
    let isMounted = true;

    async function loadExecDetails() {
      if (!selectedExecId) {
        setEvents([]);
        return;
      }
      try {
        const [res, evHistory] = await Promise.all([
          api.get(`/execution/${selectedExecId}`).catch(() => null),
          getExecutionEventsHistory(selectedExecId).catch(() => ({ events: [] })),
        ]);

        if (!isMounted) return;

        if (res?.data) {
          setExecData(res.data);
        }

        const loadedEvents = evHistory.events || [];
        setEvents(loadedEvents);

        // If execution is running, subscribe to SSE
        if (res?.data?.status === "running") {
          setStreamState("streaming");
          setIsStreaming(true);

          const afterSeq = loadedEvents.length
            ? loadedEvents[loadedEvents.length - 1].sequence_number
            : 0;

          unsub = subscribeToExecutionEvents(
            selectedExecId,
            {
              onOpen: () => {
                if (isMounted) setStreamState("streaming");
              },
              onEvent: (ev) => {
                if (!isMounted) return;
                setEvents((prev) => {
                  if (prev.some((e) => e.event_id === ev.event_id)) return prev;
                  return [...prev, ev];
                });
                if (ev.event_type === "execution.completed") {
                  setStreamState("completed");
                  setIsStreaming(false);
                  getExecution(selectedExecId).then((fresh) => {
                    if (isMounted) setExecData(fresh);
                  });
                } else if (ev.event_type === "execution.failed") {
                  setStreamState("completed");
                  setIsStreaming(false);
                }
              },
              onError: () => {
                if (isMounted) setStreamState("reconnecting");
              },
            },
            afterSeq
          );
        } else {
          setStreamState(res?.data?.status === "completed" ? "completed" : "disconnected");
          setIsStreaming(false);
        }
      } catch (err) {
        console.error("Failed to load execution details", err);
      }
    }
    loadExecDetails();

    return () => {
      isMounted = false;
      if (unsub) unsub();
    };
  }, [selectedExecId]);


  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 14 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading execution runtime traces…</p>
      </div>
    );
  }

  const logs: AgentLog[] = execData?.agent_logs || [];
  const totalToolCalls = logs.reduce((acc, l) => acc + (l.tool_calls?.length || 0), 0);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Task Selector */}
      <TaskSelector
        tasks={tasks}
        selectedTaskId={selectedTaskId}
        onSelectTaskId={setSelectedTaskId}
        label="Execution Target"
        actionRight={
          execData?.task_id ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {executions.length > 1 && (
                <select
                  value={selectedExecId}
                  onChange={(e) => setSelectedExecId(e.target.value)}
                  className="form-control"
                  style={{ fontSize: 11, fontFamily: "var(--font-mono, monospace)", padding: "4px 24px 4px 8px" }}
                  aria-label="Select execution ID"
                >
                  {executions.map((e) => (
                    <option key={e.execution_id} value={e.execution_id}>
                      Trace: {e.execution_id} (Run #{e.run_number || 1})
                    </option>
                  ))}
                </select>
              )}
              <Link href={`/run/${execData.task_id}?exec=${execData.execution_id}`} className="btn btn-primary btn-sm">
                Interactive Run Workbench →
              </Link>
            </div>
          ) : undefined
        }
      />

      {execData ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Execution KPI Cards */}
          <div className="kpi-grid fade-up">
            <div className="kpi-card">
              <span className="kpi-label">Status</span>
              <div className="kpi-value-row">
                <span className={`status-dot ${execData.status === "completed" ? "live" : "failed"}`} />
                <span className="kpi-value" style={{ fontSize: 18, textTransform: "capitalize", color: execData.status === "completed" ? "#34d399" : "#fbbf24" }}>
                  {execData.status || "Completed"}
                </span>
              </div>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Execution Latency</span>
              <div className="kpi-value-row">
                <span className="kpi-value" style={{ color: "#38bdf8" }}>
                  {execData.duration_seconds !== undefined
                    ? `${execData.duration_seconds.toFixed(2)}s`
                    : "0.02s"}
                </span>
              </div>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Agent Team Active</span>
              <div className="kpi-value-row">
                <span className="kpi-value" style={{ color: "#818cf8" }}>
                  {logs.length} Nodes
                </span>
              </div>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Tool Dispatches</span>
              <div className="kpi-value-row">
                <span className="kpi-value" style={{ color: "#c4b5fd" }}>
                  {totalToolCalls} Calls
                </span>
              </div>
            </div>

            <div className="kpi-card">
              <span className="kpi-label">Iteration</span>
              <div className="kpi-value-row">
                <span className="kpi-value">
                  Run #{execData.run_number || 1}
                </span>
              </div>
            </div>
          </div>

          {/* Security Sandbox Badge */}
          <div
            style={{
              padding: "10px 16px",
              borderRadius: 8,
              background: "rgba(99, 102, 241, 0.06)",
              border: "1px solid rgba(99, 102, 241, 0.2)",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: 8,
              fontSize: 12,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 14 }}>🔒</span>
              <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>
                Isolated Execution Sandbox:
              </span>
              <span style={{ color: "var(--text-secondary)" }}>
                Code tools run in hardened sub-processes (`python3 -I -c`) with AST safety analysis, stripped environment, and 5-second execution timeout.
              </span>
            </div>
            <span className="badge badge-indigo">Subprocess Enforced</span>
          </div>

          {/* Main Card with Tabs */}
          <div className="card fade-up">
            <div className="card-header">
              <div>
                <div className="card-title">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="5 3 19 12 5 21 5 3" />
                  </svg>
                  LangGraph Agent Execution Pipeline
                </div>
                <div className="card-subtitle">
                  Step-by-step trace of each agent node invoking tools and generating intermediate states
                </div>
              </div>

              {/* View Switcher Tabs */}
              <div style={{ display: "flex", gap: 4, background: "var(--bg-card-subtle)", padding: 3, borderRadius: 6, border: "1px solid var(--border)" }}>
                <button
                  onClick={() => setActiveTab("timeline")}
                  className={`btn btn-sm ${activeTab === "timeline" ? "btn-primary" : "btn-ghost"}`}
                  style={{ fontSize: 11 }}
                >
                  Visual Timeline
                </button>
                <button
                  onClick={() => setActiveTab("tools")}
                  className={`btn btn-sm ${activeTab === "tools" ? "btn-primary" : "btn-ghost"}`}
                  style={{ fontSize: 11 }}
                >
                  Tool Invocations ({totalToolCalls})
                </button>
                <button
                  onClick={() => setActiveTab("raw")}
                  className={`btn btn-sm ${activeTab === "raw" ? "btn-primary" : "btn-ghost"}`}
                  style={{ fontSize: 11 }}
                >
                  Synthesized Output
                </button>
              </div>
            </div>

            <div style={{ padding: "20px" }}>
              {/* Tab 1: Visual Timeline */}
              {activeTab === "timeline" && (
                <div style={{ maxWidth: 880, margin: "0 auto", display: "flex", flexDirection: "column", gap: 16 }}>
                  {selectedExecId && (
                    <LiveExecutionStatus
                      executionId={selectedExecId}
                      status={execData?.status}
                      stage={events.length > 0 ? events[events.length - 1].stage : "agent_execution"}
                      eventCount={events.length}
                      connectionStatus={streamState}
                      durationSeconds={execData?.duration_seconds}
                      error={execData?.error}
                    />
                  )}
                  {events.length > 0 || logs.length > 0 ? (
                    <ExecutionTimeline
                      events={events}
                      logs={logs}
                      isStreaming={isStreaming}
                    />
                  ) : (
                    <div style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)", fontSize: 13 }}>
                      No execution events or agent logs recorded in this trace.
                    </div>
                  )}
                </div>
              )}

              {/* Tab 2: Tool Calls Breakdown */}
              {activeTab === "tools" && (
                <div>
                  {totalToolCalls === 0 ? (
                    <div style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)", fontSize: 13 }}>
                      No external tool invocations in this execution. Agents performed pure cognitive reasoning.
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                      {logs.map((agent) =>
                        (agent.tool_calls || []).map((tool, idx) => (
                          <div
                            key={`${agent.agent_id}-${idx}`}
                            style={{
                              padding: "14px 16px",
                              borderRadius: 8,
                              background: "var(--bg-card-subtle)",
                              border: "1px solid var(--border-soft)",
                            }}
                          >
                            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <span className="badge badge-indigo">{tool.tool}</span>
                                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                                  Invoked by: <strong style={{ color: "var(--text-primary)" }}>{agent.role}</strong>
                                </span>
                              </div>
                              {tool.duration !== undefined && (
                                <span style={{ fontSize: 11, fontFamily: "var(--font-mono, monospace)", color: "var(--text-muted)" }}>
                                  Latency: {tool.duration.toFixed(3)}s
                                </span>
                              )}
                            </div>

                            {tool.query && (
                              <div style={{ marginBottom: 6 }}>
                                <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: 2 }}>
                                  Query / Input Payload:
                                </span>
                                <pre style={{ fontSize: 11.5, background: "var(--bg-card-subtle)", border: "1px solid var(--border)", padding: "8px 12px", borderRadius: 6, overflowX: "auto", color: "var(--text-primary)" }}>
                                  {tool.query}
                                </pre>
                              </div>
                            )}

                            {tool.output && (
                              <div>
                                <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: "var(--text-muted)", display: "block", marginBottom: 2 }}>
                                  Tool Execution Result:
                                </span>
                                <pre style={{ fontSize: 11.5, background: "var(--bg-card-subtle)", border: "1px solid var(--border)", padding: "8px 12px", borderRadius: 6, overflowX: "auto", color: "var(--text-secondary)", maxHeight: 180, overflowY: "auto" }}>
                                  {typeof tool.output === "object" ? JSON.stringify(tool.output, null, 2) : tool.output}
                                </pre>
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Synthesized Output */}
              {activeTab === "raw" && (
                <div>
                  {execData.final_output ? (
                    <div style={{ background: "var(--bg-card-subtle)", padding: "18px 20px", borderRadius: 8, border: "1px solid var(--border-soft)" }}>
                      <span style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: "#818cf8", display: "block", marginBottom: 8 }}>
                        Compiled Final State Artifact:
                      </span>
                      <pre style={{ whiteSpace: "pre-wrap", fontSize: 13, color: "var(--text-primary)", lineHeight: 1.6, fontFamily: "inherit" }}>
                        {execData.final_output}
                      </pre>
                    </div>
                  ) : (
                    <div style={{ textAlign: "center", padding: "40px", color: "var(--text-muted)", fontSize: 13 }}>
                      No synthesized final output returned in this execution trace.
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-title">No Execution Traces Found</div>
          <div className="empty-state-desc">
            Submit a task from the overview page to trigger dynamic execution in the LangGraph engine.
          </div>
          <Link href="/" className="btn btn-primary btn-sm">
            + Launch New Experiment
          </Link>
        </div>
      )}
    </div>
  );
}
