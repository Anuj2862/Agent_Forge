"use client";

import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import Link from "next/link";
import {
  evaluateExecution,
  startExecutionAsync,
  getExecution,
  getExecutionEventsHistory,
  subscribeToExecutionEvents,
  evolveArchitecture,
  compareTaskRuns,
  api,
  ArchitectureSpec,
  TaskComparisonResponse,
  TaskDetail,
  ExecutionDetail,
  EvaluationDetail,
  ExecutionEvent,
  AgentConfig,
} from "@/lib/api";
import ArchitectureGraph from "@/components/architecture/ArchitectureGraph";
import ExecutionTimeline from "@/components/execution/ExecutionTimeline";
import LiveExecutionStatus, { StreamConnectionStatus } from "@/components/execution/LiveExecutionStatus";
import MetricsPanel from "@/components/evaluation/MetricsPanel";
import ReflectionPanel from "@/components/evaluation/ReflectionPanel";
import DecisionVerdictCard from "@/components/DecisionVerdictCard";

export default function RunPage({ params }: { params?: { task_id?: string } }) {
  const routerParams = useParams();
  const taskId =
    (routerParams?.task_id as string) ||
    (params && typeof params.task_id === "string" ? params.task_id : "");
  const searchParams = useSearchParams();
  const execParam = searchParams.get("exec");

  const [activeTab, setActiveTab] = useState<"run_1" | "run_2" | "comparison">("run_1");
  const [taskData, setTaskData] = useState<TaskDetail | null>(null);
  const [execData, setExecData] = useState<ExecutionDetail | null>(null);
  const [evalData, setEvalData] = useState<EvaluationDetail | null>(null);
  const [archV1, setArchV1] = useState<ArchitectureSpec | null>(null);
  const [archV2, setArchV2] = useState<ArchitectureSpec | null>(null);
  const [comparison, setComparison] = useState<TaskComparisonResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [isEvolving, setIsEvolving] = useState(false);
  const [isExecutingV1, setIsExecutingV1] = useState(false);
  const [isExecutingV2, setIsExecutingV2] = useState(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Real-time execution events & streaming state
  const [events, setEvents] = useState<ExecutionEvent[]>([]);
  const [streamState, setStreamState] = useState<StreamConnectionStatus>("disconnected");
  const [isStreaming, setIsStreaming] = useState(false);
  const [showConstraints, setShowConstraints] = useState(false);

  const currentExecutionId = execData?.execution_id;
  const currentExecutionStatus = execData?.status;

  // Subscribe to SSE stream and load event history when execution changes
  useEffect(() => {
    let unsub: (() => void) | null = null;
    let isMounted = true;

    async function loadEventsAndSubscribe() {
      if (!currentExecutionId) {
        setEvents([]);
        setStreamState("disconnected");
        setIsStreaming(false);
        return;
      }

      try {
        const history = await getExecutionEventsHistory(currentExecutionId);
        if (isMounted) {
          setEvents(history.events || []);
        }

        // If currently running, establish live SSE subscription
        if (currentExecutionStatus === "running") {
          setStreamState("streaming");
          setIsStreaming(true);

          const afterSeq = history.events?.length
            ? history.events[history.events.length - 1].sequence_number
            : 0;

          unsub = subscribeToExecutionEvents(
            currentExecutionId,
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
                if (ev.event_type === "evaluation.completed") {
                  api.get(`/tasks/${taskId}`).then((tResp) => {
                    if (isMounted) {
                      setTaskData(tResp.data);
                      if (tResp.data.latest_evaluation) {
                        setEvalData(tResp.data.latest_evaluation);
                      }
                    }
                  }).catch(() => null);
                } else if (ev.event_type === "evolution.validated" || ev.event_type === "evolution.proposed") {
                  api.get(`/tasks/${taskId}`).then((tResp) => {
                    if (isMounted && tResp.data.architecture_versions?.v2) {
                      setArchV2(tResp.data.architecture_versions.v2);
                    }
                  }).catch(() => null);
                } else if (ev.event_type === "evolution.accepted" || ev.event_type === "evolution.rejected") {
                  compareTaskRuns(taskId).then((comp) => {
                    if (isMounted) setComparison(comp);
                  }).catch(() => null);
                } else if (ev.event_type === "execution.completed") {
                  setStreamState("completed");
                  setIsStreaming(false);
                  getExecution(currentExecutionId).then((fresh) => {
                    if (isMounted) setExecData(fresh);
                  }).catch(() => null);
                  api.get(`/tasks/${taskId}`).then((tResp) => {
                    if (isMounted) {
                      setTaskData(tResp.data);
                      if (tResp.data.latest_evaluation) {
                        setEvalData(tResp.data.latest_evaluation);
                      }
                      if (tResp.data.architecture_versions?.v2) {
                        setArchV2(tResp.data.architecture_versions.v2);
                      }
                    }
                  }).catch(() => null);
                  compareTaskRuns(taskId).then((comp) => {
                    if (isMounted) setComparison(comp);
                  }).catch(() => null);
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
          setStreamState(currentExecutionStatus === "completed" ? "completed" : "disconnected");
          setIsStreaming(false);
        }
      } catch {
        if (isMounted) setStreamState("disconnected");
      }
    }

    loadEventsAndSubscribe();

    return () => {
      isMounted = false;
      if (unsub) unsub();
    };
  }, [currentExecutionId, currentExecutionStatus, taskId]);


  useEffect(() => {
    if (!taskId) return;
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const tResp = await api.get(`/tasks/${taskId}`);
        setTaskData(tResp.data);

        // Track architecture versions
        if (tResp.data.architecture_spec) {
          setArchV1(tResp.data.architecture_versions?.v1 || tResp.data.architecture_spec);
        }
        if (tResp.data.architecture_versions?.v2) {
          setArchV2(tResp.data.architecture_versions.v2);
        }

        // Load execution if provided or check task executions
        let currentExec: ExecutionDetail | null = null;
        if (execParam) {
          try {
            const eResp = await api.get(`/execution/${execParam}`);
            currentExec = eResp.data;
            setExecData(currentExec);
            if (currentExec?.run_number === 2) {
              setActiveTab("run_2");
            }
          } catch {
            // Optional execution param load failure ignored
          }
        } else if (tResp.data.latest_execution) {
          currentExec = tResp.data.latest_execution;
          setExecData(currentExec);
        }

        // Load evaluation if exists
        const evalId = tResp.data.latest_evaluation_id;
        if (evalId) {
          try {
            const evResp = await api.get(`/evaluation/${evalId}`);
            setEvalData(evResp.data);
          } catch {
            // Handled gracefully
          }
        }

        // Check for existing comparison
        try {
          const compResp = await compareTaskRuns(taskId);
          if (compResp.has_comparison || compResp.evolution_decision) {
            setComparison(compResp);
          }
        } catch {
          // Handled gracefully
        }
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load experiment session data.");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [taskId, execParam]);

  // Trigger evaluation of current execution
  const handleEvaluate = async () => {
    if (!execData) return;
    setEvaluating(true);
    setError(null);
    try {
      const result = await evaluateExecution(execData.execution_id, taskId);
      setEvalData(result);
      setTaskData((p: TaskDetail | null) => (p ? {
        ...p,
        latest_evaluation_id: result.evaluation_id,
        latest_evaluation: result,
      } : p));

      setActionSuccess(`Evaluation completed. Overall score: ${((result.success_rating ?? 0.8) * 100).toFixed(0)}%`);
      setTimeout(() => setActionSuccess(null), 4000);

      // Check comparison if run 2
      if (execData.run_number >= 2) {
        try {
          const compResp = await compareTaskRuns(taskId);
          setComparison(compResp);
          setActiveTab("comparison");
        } catch {
          // Comparison handled gracefully
        }
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  };

  // Evolve Architecture via Member 3 ArchitectureModifier
  const handleApplyRecommendationAndEvolve = async () => {
    setIsEvolving(true);
    setError(null);
    try {
      const res = await evolveArchitecture(taskId);
      setArchV2(res.evolved_architecture);
      setTaskData((prev: TaskDetail | null) => (prev ? {
        ...prev,
        architecture_spec: res.evolved_architecture,
        architecture_versions: {
          ...(prev.architecture_versions || {}),
          v1: archV1 || prev.architecture_spec || res.evolved_architecture,
          v2: res.evolved_architecture,
        },
      } : prev));

      setActionSuccess(`Architecture mutated into Version 2! Applied: ${res.modifications_applied.join(", ")}`);
      setTimeout(() => setActionSuccess(null), 5000);
      setActiveTab("run_2");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to evolve architecture");
    } finally {
      setIsEvolving(false);
    }
  };

  // Execute Architecture v1
  const handleExecuteV1 = async () => {
    setIsExecutingV1(true);
    setError(null);
    setEvents([]);
    try {
      const startRes = await startExecutionAsync(taskId, 1);
      const partialExec: ExecutionDetail = {
        execution_id: startRes.execution_id,
        task_id: taskId,
        architecture_id: startRes.architecture_id,
        run_number: 1,
        status: "running",
        duration_seconds: 0,
        total_steps: 0,
        agent_count: archV1?.agents?.length || 1,
        tool_call_count: 0,
        overall_success_rate: 0,
        step_history: [],
        agent_traces: [],
        agent_logs: [],
      };
      setExecData(partialExec);
      setStreamState("streaming");
      setIsStreaming(true);

      await new Promise<void>((resolve, reject) => {
        const unsub = subscribeToExecutionEvents(startRes.execution_id, {
          onEvent: (ev) => {
            setEvents((prev) => (prev.some((e) => e.event_id === ev.event_id) ? prev : [...prev, ev]));
            if (ev.event_type === "execution.completed") {
              unsub();
              resolve();
            } else if (ev.event_type === "execution.failed") {
              unsub();
              reject(new Error(ev.error || "Execution failed"));
            }
          },
          onError: () => {
            api.get(`/execution/${startRes.execution_id}`).then((r) => {
              if (r.data.status === "completed") resolve();
            });
          },
        });
      });

      const freshExec = await getExecution(startRes.execution_id);
      setExecData(freshExec);
      setActionSuccess("Architecture V1 executed successfully with live streaming telemetry!");
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Execution of Architecture V1 failed");
    } finally {
      setIsExecutingV1(false);
      setIsStreaming(false);
    }
  };

  // Execute Architecture v2
  const handleExecuteV2 = async () => {
    setIsExecutingV2(true);
    setError(null);
    setEvents([]);
    try {
      const startRes = await startExecutionAsync(taskId, 2);
      const partialExec: ExecutionDetail = {
        execution_id: startRes.execution_id,
        task_id: taskId,
        architecture_id: startRes.architecture_id,
        run_number: 2,
        status: "running",
        duration_seconds: 0,
        total_steps: 0,
        agent_count: archV2?.agents?.length || 1,
        tool_call_count: 0,
        overall_success_rate: 0,
        step_history: [],
        agent_traces: [],
        agent_logs: [],
      };
      setExecData(partialExec);
      setStreamState("streaming");
      setIsStreaming(true);

      await new Promise<void>((resolve, reject) => {
        const unsub = subscribeToExecutionEvents(startRes.execution_id, {
          onEvent: (ev) => {
            setEvents((prev) => (prev.some((e) => e.event_id === ev.event_id) ? prev : [...prev, ev]));
            if (ev.event_type === "execution.completed") {
              unsub();
              resolve();
            } else if (ev.event_type === "execution.failed") {
              unsub();
              reject(new Error(ev.error || "Execution failed"));
            }
          },
          onError: () => {
            api.get(`/execution/${startRes.execution_id}`).then((r) => {
              if (r.data.status === "completed") resolve();
            });
          },
        });
      });

      const freshExec = await getExecution(startRes.execution_id);
      setExecData(freshExec);

      // Auto evaluate Run 2
      const evalResult = await evaluateExecution(freshExec.execution_id, taskId);
      setEvalData(evalResult);

      // Fetch side-by-side comparison
      const comp = await compareTaskRuns(taskId);
      setComparison(comp);
      setActiveTab("comparison");

      setActionSuccess("Architecture V2 executed & evaluated successfully with live stream telemetry!");
      setTimeout(() => setActionSuccess(null), 4000);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Execution of Architecture V2 failed");
    } finally {
      setIsExecutingV2(false);
      setIsStreaming(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh", gap: 14 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading experiment session &amp; runtime records…</p>
      </div>
    );
  }

  if (error && !taskData) {
    return (
      <div style={{ maxWidth: 540, margin: "60px auto", padding: "28px", background: "rgba(244, 63, 94, 0.06)", border: "1px solid rgba(244, 63, 94, 0.25)", borderRadius: 12, textAlign: "center" }}>
        <div style={{ fontWeight: 800, color: "#fb7185", fontSize: 16, marginBottom: 8 }}>
          Experiment Session Unavailable
        </div>
        <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 18, lineHeight: 1.5 }}>
          {error || "Could not retrieve task specifications from local SQLite database."}
        </p>
        <Link href="/" className="btn btn-primary btn-sm">
          ← Return to Task Input
        </Link>
      </div>
    );
  }

  const taskSpec = taskData?.task_spec || {};
  const currentArchSpec: ArchitectureSpec =
    (activeTab === "run_2" && archV2 ? archV2 : archV1 || taskData?.architecture_spec) || {
      architecture_id: "default",
      task_id: taskId,
      topology: "pipeline",
      agents: [],
      connections: [],
    };
  const runNumber = activeTab === "run_2" ? 2 : 1;

  // Newly evolved agents in v2
  const v1AgentIds = new Set((archV1?.agents || []).map((a) => a.agent_id));
  const evolvedAgentIds = (archV2?.agents || [])
    .filter((a) => !v1AgentIds.has(a.agent_id))
    .map((a) => a.agent_id);

  const taskTypeStr = String(taskSpec.task_type || taskData?.task_type || "general");
  const complexityStr = String(taskSpec.complexity || taskData?.complexity || "low");
  const userPromptStr = String(taskSpec.user_prompt || taskData?.user_prompt || "");

  // Extract constraints
  const rawConstraints = taskSpec.constraints;
  const constraintsList: string[] = Array.isArray(rawConstraints)
    ? rawConstraints.map(String)
    : typeof rawConstraints === "object" && rawConstraints !== null
    ? Object.entries(rawConstraints).map(([k, v]) => `${k}: ${v}`)
    : [];

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* ── Action Success Confirmation Banner ─────────────────── */}
      {actionSuccess && (
        <div
          className="fade-up"
          style={{
            padding: "10px 16px",
            borderRadius: 8,
            background: "rgba(16, 185, 129, 0.12)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            color: "#34d399",
            fontSize: 12.5,
            fontWeight: 600,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>✓ {actionSuccess}</span>
          <button
            onClick={() => setActionSuccess(null)}
            style={{ background: "none", border: "none", color: "#34d399", cursor: "pointer", fontSize: 13 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* ── Error Banner ────────────────────────────────────────── */}
      {error && (
        <div
          className="fade-up"
          style={{
            padding: "10px 16px",
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
          <span>✕ {error}</span>
          <button
            onClick={() => setError(null)}
            style={{ background: "none", border: "none", color: "#fb7185", cursor: "pointer", fontSize: 13 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* ── Research Brief & Run Selector ────────────────────────── */}
      <div
        className="card fade-up"
        style={{
          padding: "20px 24px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 16 }}>
          {/* Left: Experiment Description & Technical Meta */}
          <div style={{ flex: 1, minWidth: 320 }}>
            {/* Experiment Title / User Prompt */}
            <h1
              style={{
                fontSize: 20,
                fontWeight: 700,
                color: "var(--text-primary)",
                lineHeight: 1.4,
                marginBottom: 8,
                letterSpacing: "-0.01em",
              }}
            >
              {userPromptStr || "Autonomous Multi-Agent Task Execution"}
            </h1>

            {/* Subtle Inline Technical Metadata */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 8,
                fontSize: 12.5,
                color: "var(--text-secondary)",
              }}
            >
              <span>
                Task ID:{" "}
                <code
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 12,
                    color: "var(--blue-primary)",
                  }}
                >
                  {taskId}
                </code>
              </span>
              <span style={{ color: "var(--border-strong)" }}>·</span>
              <span>Type: <strong style={{ color: "var(--text-primary)", fontWeight: 500 }}>{taskTypeStr.replace(/_/g, " ")}</strong></span>
              <span style={{ color: "var(--border-strong)" }}>·</span>
              <span>Complexity: <strong style={{ color: "var(--text-primary)", fontWeight: 500 }}>{complexityStr}</strong></span>
              <span style={{ color: "var(--border-strong)" }}>·</span>
              <span style={{ display: "inline-flex", alignItems: "center", gap: 5 }}>
                <span
                  style={{
                    width: 6,
                    height: 6,
                    borderRadius: "50%",
                    background: archV2 ? "var(--emerald)" : "var(--blue-bright)",
                  }}
                />
                <span style={{ color: archV2 ? "var(--emerald)" : "var(--text-secondary)" }}>
                  {archV2 ? "V2 Candidate Available" : "Baseline V1 Active"}
                </span>
              </span>

              {constraintsList.length > 0 && (
                <>
                  <span style={{ color: "var(--border-strong)" }}>·</span>
                  <button
                    onClick={() => setShowConstraints(!showConstraints)}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--blue-primary)",
                      fontSize: 12,
                      cursor: "pointer",
                      padding: 0,
                      textDecoration: "underline",
                    }}
                  >
                    {showConstraints ? "Hide constraints ▴" : `View constraints (${constraintsList.length}) ▾`}
                  </button>
                </>
              )}
            </div>

            {/* Collapsible Constraints Specification Drawer */}
            {showConstraints && constraintsList.length > 0 && (
              <div
                style={{
                  marginTop: 14,
                  padding: "12px 16px",
                  background: "var(--bg-card-subtle)",
                  border: "1px solid var(--border)",
                  borderRadius: 8,
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 8 }}>
                  Constraint Specification (Hard Invariants)
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 8 }}>
                  {constraintsList.map((c, idx) => (
                    <div key={idx} style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                      <span style={{ color: "var(--blue-primary)", marginRight: 6 }}>•</span>
                      {c}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right: Restrained Run Selector Segmented Control */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              background: "var(--bg-card-subtle)",
              padding: 3,
              borderRadius: 8,
              border: "1px solid var(--border)",
            }}
          >
            <button
              onClick={() => setActiveTab("run_1")}
              style={{
                fontSize: 12,
                fontWeight: activeTab === "run_1" ? 600 : 500,
                color: activeTab === "run_1" ? "var(--blue-primary)" : "var(--text-muted)",
                background: activeTab === "run_1" ? "rgba(37, 99, 235, 0.12)" : "transparent",
                border: activeTab === "run_1" ? "1px solid var(--border-active)" : "1px solid transparent",
                borderRadius: 6,
                padding: "6px 14px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Run 1 (Baseline V1)
            </button>
            <button
              onClick={() => setActiveTab("run_2")}
              style={{
                fontSize: 12,
                fontWeight: activeTab === "run_2" ? 600 : 500,
                color: activeTab === "run_2" ? "var(--blue-primary)" : "var(--text-muted)",
                background: activeTab === "run_2" ? "rgba(37, 99, 235, 0.12)" : "transparent",
                border: activeTab === "run_2" ? "1px solid var(--border-active)" : "1px solid transparent",
                borderRadius: 6,
                padding: "6px 14px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Run 2 {archV2 ? "(Candidate V2)" : "(Pending Mutation)"}
            </button>
            <button
              onClick={() => setActiveTab("comparison")}
              style={{
                fontSize: 12,
                fontWeight: activeTab === "comparison" ? 600 : 500,
                color: activeTab === "comparison" ? "var(--emerald)" : "var(--text-muted)",
                background: activeTab === "comparison" ? "rgba(5, 150, 105, 0.12)" : "transparent",
                border: activeTab === "comparison" ? "1px solid var(--decision-accepted-border)" : "1px solid transparent",
                borderRadius: 6,
                padding: "6px 14px",
                cursor: "pointer",
                transition: "all 0.15s ease",
              }}
            >
              Comparative Verdict
            </button>
          </div>
        </div>
      </div>

      {/* ── TAB 3: EVOLUTION COMPARISON & DETERMINISTIC DECISION ──── */}
      {activeTab === "comparison" && (
        <div className="fade-up" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Decision Verdict Card */}
          <DecisionVerdictCard
            decision={comparison?.evolution_decision || taskData?.evolution_decision}
            hasRuns={!!(comparison?.run_1 && comparison?.run_2)}
          />

          {/* Metric Comparison Table */}
          {comparison?.has_comparison && comparison.run_1 && comparison.run_2 ? (
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                    </svg>
                    Run 1 vs Run 2 Metric Deltas (Empirical Evidence)
                  </div>
                  <div className="card-subtitle">
                    Absolute differences evaluated against baseline performance
                  </div>
                </div>
              </div>

              <div style={{ overflowX: "auto" }}>
                <table className="research-table">
                  <thead>
                    <tr>
                      <th>Metric Dimension</th>
                      <th>Run #1 (Baseline V1)</th>
                      <th>Run #2 (Candidate V2)</th>
                      <th>Delta (Δ)</th>
                      <th>Statistical Direction</th>
                    </tr>
                  </thead>
                  <tbody>
                    {/* Task Success */}
                    <tr>
                      <td style={{ fontWeight: 600 }}>Task Success Rate</td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                        {comparison.run_1.evaluation?.metrics?.task_success !== undefined
                          ? `${(comparison.run_1.evaluation.metrics.task_success * 100).toFixed(0)}%`
                          : "N/A"}
                      </td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#34d399" }}>
                        {comparison.run_2.evaluation?.metrics?.task_success !== undefined
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

                    {/* Output Quality */}
                    <tr>
                      <td style={{ fontWeight: 600 }}>Output Quality</td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                        {comparison.run_1.evaluation?.metrics?.quality !== undefined
                          ? `${(comparison.run_1.evaluation.metrics.quality * 100).toFixed(0)}%`
                          : "N/A"}
                      </td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#34d399" }}>
                        {comparison.run_2.evaluation?.metrics?.quality !== undefined
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

                    {/* Factual Accuracy */}
                    <tr>
                      <td style={{ fontWeight: 600 }}>Factual Accuracy</td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                        {comparison.run_1.evaluation?.metrics?.accuracy !== undefined
                          ? `${(comparison.run_1.evaluation.metrics.accuracy * 100).toFixed(0)}%`
                          : "N/A"}
                      </td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)", color: "#34d399" }}>
                        {comparison.run_2.evaluation?.metrics?.accuracy !== undefined
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

                    {/* Agent Team Count */}
                    <tr>
                      <td style={{ fontWeight: 600 }}>Agent Team Count</td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                        {comparison.run_1.architecture?.agents?.length || 1} agents
                      </td>
                      <td style={{ fontFamily: "var(--font-mono, monospace)" }}>
                        {comparison.run_2.architecture?.agents?.length || 1} agents
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
          ) : (
            <div className="card" style={{ padding: "28px", textAlign: "center" }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", marginBottom: 6 }}>
                Awaiting Run #2 Execution Traces
              </div>
              <p style={{ fontSize: 13, color: "var(--text-muted)", maxWidth: 440, margin: "0 auto 16px" }}>
                Execute the mutated Architecture V2 to compare metric deltas against the Baseline Run 1.
              </p>
              {archV2 ? (
                <button
                  onClick={handleExecuteV2}
                  disabled={isExecutingV2}
                  className="btn btn-emerald btn-sm"
                >
                  {isExecutingV2 ? "Executing Architecture V2…" : "▶ Execute Architecture V2 Now"}
                </button>
              ) : (
                <button
                  onClick={handleApplyRecommendationAndEvolve}
                  disabled={isEvolving}
                  className="btn btn-primary btn-sm"
                >
                  {isEvolving ? "Mutating…" : "Apply Recommendations & Mutate V2"}
                </button>
              )}
            </div>
          )}

          {/* Architecture Diff Card */}
          {comparison?.architecture_diff && (
            <div className="card">
              <div className="card-header">
                <div>
                  <div className="card-title">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7" rx="1.5" />
                      <rect x="14" y="3" width="7" height="7" rx="1.5" />
                      <rect x="14" y="14" width="7" height="7" rx="1.5" />
                      <rect x="3" y="14" width="7" height="7" rx="1.5" />
                    </svg>
                    Topological Architecture Diff
                  </div>
                  <div className="card-subtitle">
                    Exact graph mutation applied by Member 3 ArchitectureModifier
                  </div>
                </div>
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
                    Graph connections rewired to route intermediate synthesis through verification with DAG cycle validation.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── TAB 1 & 2: RUN 1 or RUN 2 WORKBENCH ───────────────────── */}
      {activeTab !== "comparison" && (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 390px",
            gap: 20,
            alignItems: "start",
          }}
        >
          {/* LEFT: Architecture Graph + Evaluation + Mutation CTA */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Architecture Card */}
            <div
              className="card"
              style={{
                borderRadius: 12,
                overflow: "hidden",
                border: "1px solid var(--border)",
              }}
            >
              <div
                style={{
                  padding: "16px 20px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <div>
                  <h2 style={{ fontSize: 16, fontWeight: 700, color: "var(--text-primary)" }}>
                    {activeTab === "run_2" ? "Mutated Architecture Candidate (V2)" : "Synthesized Baseline Architecture (V1)"}
                  </h2>
                  <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>
                    {currentArchSpec.agents.length} agent nodes · {currentArchSpec.topology} topology · Click any node to inspect in drawer
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Architecture ID:</span>
                  <code style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--accent-blue)", background: "var(--accent-blue-subtle)", padding: "2px 8px", borderRadius: 4, border: "1px solid var(--border-soft)" }}>
                    {currentArchSpec.architecture_id}
                  </code>
                </div>
              </div>

              {currentArchSpec.meta_reasoning && (
                <div
                  style={{
                    padding: "10px 20px",
                    background: "var(--bg-card-subtle)",
                    borderBottom: "1px solid var(--border)",
                    fontSize: 12.5,
                    color: "var(--text-secondary)",
                    fontStyle: "italic",
                    lineHeight: 1.5,
                  }}
                >
                  &ldquo;{currentArchSpec.meta_reasoning}&rdquo;
                </div>
              )}

              <div style={{ height: 500 }}>
                <ArchitectureGraph
                  architecture={currentArchSpec}
                  evolvedAgentIds={activeTab === "run_2" ? evolvedAgentIds : []}
                />
              </div>
            </div>

            {/* Run 2 Execution CTA if Architecture v2 is loaded but not yet executed */}
            {activeTab === "run_2" && archV2 && (!execData || execData.run_number === 1) && (
              <div
                className="card fade-up"
                style={{
                  padding: "24px",
                  textAlign: "center",
                  background: "linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(99, 102, 241, 0.08) 100%)",
                  borderColor: "rgba(16, 185, 129, 0.3)",
                }}
              >
                <div style={{ fontSize: 11, fontWeight: 700, color: "#34d399", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
                  Architecture Candidate V2 Ready
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 8, color: "var(--text-primary)" }}>
                  Execute Mutated Architecture (Run 2)
                </h3>
                <p style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 500, margin: "0 auto 18px", lineHeight: 1.5 }}>
                  Execute the newly evolved graph through LangGraph with independent factual verification to observe impact on accuracy and quality.
                </p>
                <button
                  onClick={handleExecuteV2}
                  disabled={isExecutingV2}
                  className="btn btn-emerald"
                  style={{ padding: "10px 22px" }}
                >
                  {isExecutingV2 ? (
                    <><span className="spinner" /> Executing Architecture V2…</>
                  ) : (
                    "▶ Execute Architecture V2"
                  )}
                </button>
              </div>
            )}

            {/* Evaluation & Metrics */}
            {evalData && (
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                      </svg>
                      Evaluation Metrics (Run #{evalData.run_number || runNumber})
                    </div>
                    <div className="card-subtitle">
                      Composite Score: {((evalData.success_rating ?? 0.8) * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>
                <div style={{ padding: "18px 20px" }}>
                  <MetricsPanel metrics={(evalData.metrics || evalData.evaluation_result?.metrics)!} />
                </div>
              </div>
            )}

            {/* Failure Diagnosis & Reflection */}
            {evalData?.reflection_result && (
              <div className="card">
                <div className="card-header">
                  <div>
                    <div className="card-title">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="10" />
                        <line x1="12" y1="8" x2="12" y2="12" />
                        <line x1="12" y1="16" x2="12.01" y2="16" />
                      </svg>
                      Failure Diagnosis &amp; Root-Cause Analysis
                    </div>
                    <div className="card-subtitle">
                      {evalData.reflection_result.identified_issues.length} identified issue(s) · {evalData.reflection_result.recommendations.length} recommendation(s)
                    </div>
                  </div>
                </div>
                <div style={{ padding: "18px 20px" }}>
                  <ReflectionPanel reflection={evalData.reflection_result} />
                </div>
              </div>
            )}

            {/* Mutation CTA in Run 1 */}
            {activeTab === "run_1" && !archV2 && evalData?.reflection_result && (
              evalData.reflection_result.recommendations.length > 0 ? (
                <div
                  className="card fade-up"
                  style={{
                    padding: "24px",
                    textAlign: "center",
                    background: "linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%)",
                    borderColor: "rgba(99, 102, 241, 0.3)",
                  }}
                >
                  <div style={{ fontSize: 11, fontWeight: 700, color: "#818cf8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
                    Architectural Mutation Engine
                  </div>
                  <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 8, color: "var(--text-primary)" }}>
                    Apply Recommendations &amp; Mutate Architecture into V2
                  </h3>
                  <p style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 520, margin: "0 auto 18px", lineHeight: 1.5 }}>
                    ArchitectureModifier will programmatically evolve the architecture graph, adhering to all hard constraints while adding required verification nodes.
                  </p>
                  <button
                    onClick={handleApplyRecommendationAndEvolve}
                    disabled={isEvolving}
                    className="btn btn-primary"
                    style={{ padding: "10px 22px" }}
                  >
                    {isEvolving ? (
                      <><span className="spinner" /> Mutating Architecture…</>
                    ) : (
                      "Apply Recommendation & Mutate Graph →"
                    )}
                  </button>
                </div>
              ) : (
                <div className="card" style={{ padding: "18px 20px", textAlign: "center" }}>
                  <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    No architectural mutation recommended. The current architecture satisfied evaluation criteria.
                  </span>
                </div>
              )
            )}
          </div>

          {/* RIGHT: Real-Time Execution Timeline & Actions */}
          <div
            style={{
              position: "sticky",
              top: 76,
              height: "calc(100vh - 100px)",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div
              className="card"
              style={{
                flex: 1,
                display: "flex",
                flexDirection: "column",
                overflow: "hidden",
                borderRadius: 12,
                border: "1px solid var(--border)",
              }}
            >
              <div
                style={{
                  padding: "14px 18px",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <h3 style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
                  Execution Trace (Run #{execData?.run_number || runNumber})
                </h3>
                <div style={{ fontSize: 12, color: "var(--text-secondary)", marginTop: 2 }}>
                  {isStreaming
                    ? "Streaming live telemetry from LangGraph…"
                    : execData
                    ? `${execData.agent_logs?.length ?? 0} agents · ${events.length} lifecycle events`
                    : "Awaiting execution"}
                </div>
              </div>

              {/* Live Execution Telemetry Header */}
              {execData && (
                <div style={{ padding: "12px 16px 8px" }}>
                  <LiveExecutionStatus
                    executionId={execData.execution_id}
                    status={execData.status}
                    stage={events.length > 0 ? events[events.length - 1].stage : "agent_execution"}
                    eventCount={events.length}
                    connectionStatus={streamState}
                    durationSeconds={execData.duration_seconds}
                    error={execData.error}
                  />
                </div>
              )}

              {/* Scrollable Timeline */}
              <div
                style={{
                  flex: 1,
                  overflowY: "auto",
                  padding: "0 16px 16px",
                }}
              >
                {execData || events.length > 0 ? (
                  <ExecutionTimeline
                    events={events}
                    logs={execData?.agent_logs}
                    isStreaming={isStreaming}
                  />
                ) : (
                  <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 14, color: "var(--text-muted)", padding: 24, textAlign: "center" }}>
                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                      <polygon points="5 3 19 12 5 21 5 3" />
                    </svg>
                    <div>
                      <div style={{ fontWeight: 700, color: "var(--text-primary)", fontSize: 13, marginBottom: 4 }}>
                        Awaiting Execution
                      </div>
                      <p style={{ fontSize: 12, maxWidth: 240, margin: "0 auto 12px" }}>
                        Run this architecture to stream real-time agent steps and tool calls.
                      </p>
                    </div>
                    {activeTab === "run_1" && (
                      <button
                        onClick={handleExecuteV1}
                        disabled={isExecutingV1}
                        className="btn btn-primary btn-sm"
                      >
                        {isExecutingV1 ? <><span className="spinner" /> Executing…</> : "▶ Run Baseline Architecture"}
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Evaluate Button Footer */}
              {execData && !evalData && (
                <div style={{ padding: "14px 18px", borderTop: "1px solid var(--border-soft)", background: "var(--bg-card-subtle)" }}>
                  <button
                    onClick={handleEvaluate}
                    disabled={evaluating}
                    className="btn btn-emerald"
                    style={{ width: "100%", padding: "10px" }}
                  >
                    {evaluating ? (
                      <><span className="spinner" /> Evaluating &amp; Reflecting…</>
                    ) : (
                      "Run Evaluation & Diagnosis →"
                    )}
                  </button>
                </div>
              )}

              {evalData && (
                <div style={{ padding: "12px 18px", borderTop: "1px solid var(--border-soft)", background: "var(--bg-card-subtle)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span className="status-dot live" />
                    <span style={{ fontSize: 12, color: "var(--emerald)", fontWeight: 600 }}>
                      Memory Record Persisted
                    </span>
                  </div>
                  <span style={{ fontSize: 11, fontFamily: "var(--font-mono, monospace)", color: "var(--text-muted)" }}>
                    {evalData.memory_record_id?.slice(0, 12)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
