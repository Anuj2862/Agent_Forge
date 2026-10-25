"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  listEvaluations,
  listTasks,
  EvaluationDetail,
  EvaluationMetrics,
  TaskDetail,
} from "@/lib/api";
import MetricsPanel from "@/components/evaluation/MetricsPanel";
import TaskSelector from "@/components/TaskSelector";
import KPICard from "@/components/KPICard";

export default function EvaluationPage() {
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [evaluations, setEvaluations] = useState<EvaluationDetail[]>([]);
  const [selectedEvalId, setSelectedEvalId] = useState<string>("");
  const [evalData, setEvalData] = useState<EvaluationDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [tasksRes, evalsRes] = await Promise.all([
          listTasks().catch(() => ({ tasks: [], total: 0 })),
          listEvaluations().catch(() => ({ evaluations: [], total: 0 })),
        ]);

        if (tasksRes.tasks && tasksRes.tasks.length > 0) {
          setTasks(tasksRes.tasks);
          setSelectedTaskId(tasksRes.tasks[0].task_id);
        }

        if (evalsRes.evaluations && evalsRes.evaluations.length > 0) {
          setEvaluations(evalsRes.evaluations);
          setSelectedEvalId(evalsRes.evaluations[0].evaluation_id || "");
          setEvalData(evalsRes.evaluations[0]);
        }
      } catch (err) {
        console.error("Failed to load evaluations", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // When selected task changes, attempt to load task's latest evaluation
  useEffect(() => {
    if (!selectedTaskId) return;
    async function loadTaskEval() {
      try {
        const res = await api.get(`/tasks/${selectedTaskId}`);
        if (res.data.latest_evaluation) {
          setEvalData(res.data.latest_evaluation);
          if (res.data.latest_evaluation.evaluation_id) {
            setSelectedEvalId(res.data.latest_evaluation.evaluation_id);
          }
        } else if (res.data.latest_evaluation_id) {
          const evRes = await api.get(`/evaluation/${res.data.latest_evaluation_id}`);
          setEvalData(evRes.data);
          setSelectedEvalId(res.data.latest_evaluation_id);
        }
      } catch (err) {
        console.error("Failed to load task evaluation", err);
      }
    }
    loadTaskEval();
  }, [selectedTaskId]);

  // When evaluation ID changes directly
  useEffect(() => {
    if (!selectedEvalId) return;
    async function loadDetails() {
      try {
        const res = await api.get(`/evaluation/${selectedEvalId}`);
        setEvalData(res.data);
      } catch (err) {
        console.error("Failed to load evaluation details", err);
      }
    }
    loadDetails();
  }, [selectedEvalId]);

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 14 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading evaluation metrics and benchmarks…</p>
      </div>
    );
  }

  const result = evalData?.evaluation_result || evalData;
  const metrics: EvaluationMetrics & { verification_status?: string } = result?.metrics || {
    task_success: 0,
    quality: 0,
    completeness: 0,
    execution_time_seconds: 0,
    agent_count: 0,
    tool_call_count: 0,
    accuracy: 0,
    verification_status: "Unverified",
  };

  const hasRating = evalData?.success_rating !== undefined || metrics.overall_score !== undefined;
  const ratingValue = evalData?.success_rating ?? metrics.overall_score ?? 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Target Task Selector */}
      <TaskSelector
        tasks={tasks}
        selectedTaskId={selectedTaskId}
        onSelectTaskId={setSelectedTaskId}
        label="Evaluation Target"
        actionRight={
          evalData?.task_id ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {evaluations.length > 1 && (
                <select
                  value={selectedEvalId}
                  onChange={(e) => setSelectedEvalId(e.target.value)}
                  className="form-control"
                  style={{ fontSize: 11, fontFamily: "var(--font-mono, monospace)", padding: "4px 24px 4px 8px" }}
                  aria-label="Select evaluation ID"
                >
                  {evaluations.map((ev) => (
                    <option key={ev.evaluation_id} value={ev.evaluation_id}>
                      Eval: {ev.evaluation_id} (Run #{ev.run_number || 1})
                    </option>
                  ))}
                </select>
              )}
              <Link href={`/diagnosis?task_id=${evalData.task_id}`} className="btn btn-secondary btn-sm">
                Inspect Diagnosis →
              </Link>
              <Link href={`/run/${evalData.task_id}`} className="btn btn-primary btn-sm">
                Run Workbench
              </Link>
            </div>
          ) : undefined
        }
      />

      {evalData && result ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Top Translucent Score Cards */}
          <div className="kpi-grid fade-up">
            <KPICard
              label="Overall Composite Rating"
              value={hasRating ? `${(ratingValue * 100).toFixed(1)}%` : "N/A"}
              subtext="Multi-metric weighted objective"
              accentColor="#34D399"
              icon={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              }
            />

            <KPICard
              label="Task Success Rate"
              value={metrics.task_success !== undefined ? `${(metrics.task_success * 100).toFixed(0)}%` : "N/A"}
              subtext="Subtask fulfillment & goal completion"
              accentColor="#22D3EE"
              icon={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              }
            />

            <KPICard
              label="Output Coherence"
              value={metrics.quality !== undefined ? `${(metrics.quality * 100).toFixed(0)}%` : "N/A"}
              subtext="Structural clarity & relevance"
              accentColor="#A78BFA"
              icon={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="3" width="18" height="18" rx="2" />
                </svg>
              }
            />

            <KPICard
              label="Factual Accuracy"
              value={metrics.accuracy !== undefined ? `${(metrics.accuracy * 100).toFixed(0)}%` : "N/A"}
              subtext={metrics.verification_status || "Standard Verification"}
              accentColor={metrics.accuracy !== undefined && metrics.accuracy >= 0.8 ? "#34D399" : "#FBBF24"}
              icon={
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                </svg>
              }
            />
          </div>

          {/* Metric Dimensions Panel */}
          <div className="card fade-up">
            <div className="card-header">
              <div className="card-title">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
                Multi-Dimensional Objective Rubric
              </div>
              <span className="badge badge-indigo">
                Run #{evalData.run_number || 1}
              </span>
            </div>

            <div style={{ padding: "20px" }}>
              <MetricsPanel metrics={metrics} />
            </div>
          </div>

          {/* Evaluation Feedback and Memory Attribution */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {/* Feedback Summary */}
            <div className="card fade-up" style={{ padding: "18px 20px" }}>
              <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, color: "#818cf8" }}>
                Evaluator Feedback Summary
              </h4>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                {(result as { feedback_summary?: string })?.feedback_summary ||
                  "Detailed subtask coverage and goal fulfillment recorded. Review diagnostic reflections to inspect architectural opportunities."}
              </p>
            </div>

            {/* Verification & Memory Status */}
            <div className="card fade-up" style={{ padding: "18px 20px" }}>
              <h4 style={{ fontSize: 13, fontWeight: 700, marginBottom: 10, color: "#34d399" }}>
                Evolutionary Memory Attribution
              </h4>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                {evalData.memory_record_id ? (
                  <>
                    Indexed into SQLite memory store under Record ID:{" "}
                    <code style={{ color: "#34d399" }}>{evalData.memory_record_id}</code>. Accessible by the Meta Controller to bias future synthesis toward proven topologies.
                  </>
                ) : (
                  "Evaluation outcome registered in session state. Persisted upon full run completion."
                )}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-title">No Evaluation Benchmark Found</div>
          <div className="empty-state-desc">
            The selected task has not been evaluated yet. Run an execution and evaluate to generate performance ratings.
          </div>
          <Link href={`/run/${selectedTaskId}`} className="btn btn-primary btn-sm">
            Launch Run Workbench →
          </Link>
        </div>
      )}
    </div>
  );
}
