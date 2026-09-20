"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { evaluateExecution, runExecution, api } from "@/lib/api";
import ArchitectureGraph from "@/components/architecture/ArchitectureGraph";
import ExecutionTimeline from "@/components/execution/ExecutionTimeline";
import MetricsPanel from "@/components/evaluation/MetricsPanel";
import ReflectionPanel from "@/components/evaluation/ReflectionPanel";

export default function RunPage({ params }: { params: { task_id: string } }) {
  const taskId = params.task_id;
  const searchParams = useSearchParams();
  const execParam = searchParams.get("exec");

  const [taskData, setTaskData] = useState<any>(null);
  const [execData, setExecData] = useState<any>(null);
  const [evalData, setEvalData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [reRunning, setReRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const tResp = await api.get(`/tasks/${taskId}`);
        setTaskData(tResp.data);

        if (execParam) {
          try {
            const eResp = await api.get(`/execution/${execParam}`);
            setExecData(eResp.data);
            if (tResp.data.latest_evaluation_id) {
              const evResp = await api.get(`/evaluation/${tResp.data.latest_evaluation_id}`);
              setEvalData(evResp.data);
            }
          } catch (_) {}
        }
      } catch (err: any) {
        setError(err.message || "Failed to load run data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [taskId, execParam]);

  const handleEvaluate = async () => {
    if (!execData) return;
    setEvaluating(true);
    try {
      const result = await evaluateExecution(execData.execution_id, taskId);
      setEvalData(result);
      setTaskData((p: any) => ({ ...p, latest_evaluation_id: result.evaluation_result.evaluation_id }));
    } catch (err: any) {
      setError(err.message || "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  };

  const handleEvolve = async () => {
    setReRunning(true);
    try {
      const currentRun = execData?.run_number || 1;
      const submitResp = await api.post("/tasks/submit", {
        user_prompt: taskData.task_spec.user_prompt,
        run_number: currentRun + 1,
      });
      const execution = await runExecution(submitResp.data.task_id, currentRun + 1);
      window.location.href = `/run/${submitResp.data.task_id}?exec=${execution.execution_id}`;
    } catch (err: any) {
      setError(err.message || "Evolution run failed");
      setReRunning(false);
    }
  };

  /* ── Loading ─────────────────────────────────────────────────────── */
  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "60vh", gap: 16 }}>
        <span className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 14 }}>Loading run data…</p>
      </div>
    );
  }

  if (error || !taskData) {
    return (
      <div style={{ maxWidth: 560, margin: "60px auto", padding: "24px", background: "rgba(244,63,94,0.06)", border: "1px solid rgba(244,63,94,0.2)", borderRadius: 12, color: "#fb7185", textAlign: "center", fontSize: 14 }}>
        {error || "Task not found"}
      </div>
    );
  }

  const taskSpec = taskData.task_spec;
  const archSpec = taskData.architecture_spec;
  const runNumber = execData?.run_number || 1;
  const status = evalData ? "evaluated" : execData ? "executed" : "running";

  const statusConfig = {
    evaluated: { label: "Evaluated & Stored", color: "var(--emerald)", bg: "rgba(16,185,129,0.08)", border: "rgba(16,185,129,0.2)" },
    executed:  { label: "Execution Complete", color: "var(--amber)", bg: "rgba(245,158,11,0.08)", border: "rgba(245,158,11,0.2)" },
    running:   { label: "Running…", color: "var(--cyan)", bg: "rgba(6,182,212,0.08)", border: "rgba(6,182,212,0.2)" },
  }[status];

  return (
    <div style={{ maxWidth: 1280, margin: "0 auto", padding: "36px 24px 80px" }}>

      {/* ── Page Header ──────────────────────────────────────────── */}
      <div
        className="fade-up"
        style={{
          display: "flex",
          flexWrap: "wrap",
          alignItems: "flex-start",
          justifyContent: "space-between",
          gap: 16,
          marginBottom: 36,
          paddingBottom: 28,
          borderBottom: "1px solid var(--border-soft)",
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10, flexWrap: "wrap" }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, letterSpacing: "-0.02em" }}>
              Run{" "}
              <span className="gradient-text">#{runNumber}</span>
            </h1>
            <span className="badge badge-violet">{taskSpec.task_type.replace(/_/g, " ")}</span>
            <span className="badge badge-cyan">{taskSpec.complexity}</span>
          </div>
          <p
            style={{
              fontSize: 13,
              color: "var(--text-secondary)",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              maxWidth: 640,
            }}
            title={taskSpec.user_prompt}
          >
            <span style={{ color: "var(--text-muted)", fontWeight: 600 }}>Prompt — </span>
            {taskSpec.user_prompt}
          </p>
        </div>

        {/* Status pill */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "8px 16px",
            borderRadius: 99,
            background: statusConfig.bg,
            border: `1px solid ${statusConfig.border}`,
            fontSize: 12,
            fontWeight: 700,
            color: statusConfig.color,
            whiteSpace: "nowrap",
            flexShrink: 0,
          }}
        >
          <div
            className={status === "running" ? "pulse-glow" : ""}
            style={{ width: 7, height: 7, borderRadius: "50%", background: statusConfig.color }}
          />
          {statusConfig.label}
        </div>
      </div>

      {/* ── Two-column body ───────────────────────────────────────── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 360px",
          gap: 20,
          alignItems: "start",
        }}
      >
        {/* LEFT ── scrollable content column */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Architecture section */}
          <section className="card fade-up" style={{ padding: "22px 22px 20px" }}>
            <SectionHeader
              icon={
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
              }
              color="#818cf8"
              title="Synthesized Architecture"
              meta={`${archSpec.agents.length} agents · ${archSpec.topology} topology`}
            />

            {archSpec.meta_reasoning && (
              <p
                style={{
                  fontSize: 12,
                  color: "var(--text-secondary)",
                  lineHeight: 1.6,
                  margin: "12px 0 16px",
                  padding: "10px 14px",
                  background: "var(--bg-secondary)",
                  borderRadius: 8,
                  border: "1px solid var(--border-soft)",
                  fontStyle: "italic",
                }}
              >
                {archSpec.meta_reasoning}
              </p>
            )}

            <div style={{ height: 380, borderRadius: 10, overflow: "hidden" }}>
              <ArchitectureGraph architecture={archSpec} />
            </div>
          </section>

          {/* Evaluation & Reflection */}
          {evalData && (
            <>
              <section className="card fade-up" style={{ padding: "22px" }}>
                <SectionHeader
                  icon={
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
                  }
                  color="#34d399"
                  title="Evaluation Metrics"
                  meta={`Success: ${(evalData.evaluation_result.metrics.task_success * 100).toFixed(0)}%`}
                />
                <div style={{ marginTop: 16 }}>
                  <MetricsPanel metrics={evalData.evaluation_result.metrics} />
                </div>
              </section>

              <section className="card fade-up" style={{ padding: "22px" }}>
                <SectionHeader
                  icon={
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                  }
                  color="#c4b5fd"
                  title="Reflection & Recommendations"
                  meta={`${evalData.reflection_result.identified_issues.length} issues · ${evalData.reflection_result.recommendations.length} recommendations`}
                />
                <div style={{ marginTop: 16 }}>
                  <ReflectionPanel reflection={evalData.reflection_result} />
                </div>
              </section>

              {/* Evolve CTA */}
              <div
                className="card fade-up"
                style={{
                  padding: "24px",
                  textAlign: "center",
                  background: "linear-gradient(135deg, rgba(99,102,241,0.06) 0%, rgba(139,92,246,0.06) 100%)",
                  borderColor: "rgba(99,102,241,0.2)",
                }}
              >
                <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>Evolve & Re-Run</h3>
                <p style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 480, margin: "0 auto 20px" }}>
                  Apply reflection recommendations to synthesize an improved architecture and start a new run.
                </p>
                <button
                  onClick={handleEvolve}
                  disabled={reRunning}
                  className="btn btn-primary"
                >
                  {reRunning ? (
                    <><span className="spinner" style={{ width: 16, height: 16 }} />Evolving…</>
                  ) : (
                    <>
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12A10 10 0 0 0 15 21.5M2 12A10 10 0 0 1 15 2.5"/><path d="M15 2.5V8h5.5M15 21.5V16h5.5"/></svg>
                      Apply Recommendations &amp; Re-Run
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>

        {/* RIGHT ── sticky execution log */}
        <div
          style={{
            position: "sticky",
            top: 80,
            height: "calc(100vh - 110px)",
            display: "flex",
            flexDirection: "column",
          }}
        >
          <div
            className="card"
            style={{ padding: "18px 18px 0", flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}
          >
            <SectionHeader
              icon={
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
              }
              color="#38bdf8"
              title="Agent Execution Log"
              meta={execData ? `${execData.agent_logs?.length ?? 0} agents` : "Running…"}
            />

            {/* Scrollable log */}
            <div
              style={{
                flex: 1,
                overflowY: "auto",
                marginTop: 14,
                paddingRight: 4,
                paddingBottom: 18,
              }}
            >
              {execData ? (
                <ExecutionTimeline logs={execData.agent_logs} />
              ) : (
                <div style={{ height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 12, color: "var(--text-muted)" }}>
                  <span className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
                  <p style={{ fontSize: 13 }}>Executing agent network…</p>
                </div>
              )}
            </div>

            {/* Evaluate button */}
            {execData && !evalData && (
              <div
                style={{
                  padding: "14px 0 18px",
                  borderTop: "1px solid var(--border-soft)",
                  flexShrink: 0,
                }}
              >
                <button
                  onClick={handleEvaluate}
                  disabled={evaluating}
                  className="btn btn-emerald"
                  style={{ width: "100%" }}
                >
                  {evaluating ? (
                    <><span className="spinner" style={{ width: 15, height: 15, borderTopColor: "#07140e" }} />Evaluating…</>
                  ) : (
                    "Run Evaluation & Reflection"
                  )}
                </button>
              </div>
            )}

            {evalData && (
              <div style={{ padding: "12px 0 18px", borderTop: "1px solid var(--border-soft)", display: "flex", alignItems: "center", gap: 7, flexShrink: 0 }}>
                <div className="status-dot live" />
                <span style={{ fontSize: 12, color: "var(--emerald)", fontWeight: 600 }}>Stored to Evolution Memory</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── Section header helper ───────────────────────────────────────── */
function SectionHeader({
  icon, color, title, meta,
}: {
  icon: React.ReactNode;
  color: string;
  title: string;
  meta?: string;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div
        style={{
          width: 30,
          height: 30,
          borderRadius: 8,
          background: `${color}18`,
          border: `1px solid ${color}30`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color,
          flexShrink: 0,
        }}
      >
        {icon}
      </div>
      <div>
        <h2 style={{ fontSize: 14, fontWeight: 700, lineHeight: 1.2 }}>{title}</h2>
        {meta && <p style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{meta}</p>}
      </div>
    </div>
  );
}
