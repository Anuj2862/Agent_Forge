"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  listTasks,
  evolveArchitecture,
  ReflectionResult,
  TaskDetail,
} from "@/lib/api";
import ReflectionPanel from "@/components/evaluation/ReflectionPanel";
import TaskSelector from "@/components/TaskSelector";

export default function DiagnosisPage() {
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [taskData, setTaskData] = useState<TaskDetail | null>(null);
  const [isEvolving, setIsEvolving] = useState<boolean>(false);
  const [evolutionSuccess, setEvolutionSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

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
    async function loadDetails() {
      try {
        const res = await api.get(`/tasks/${selectedTaskId}`);
        const data = res.data;
        if (!data.latest_evaluation?.reflection_result && data.latest_evaluation_id) {
          try {
            const evalRes = await api.get(`/evaluation/${data.latest_evaluation_id}`);
            if (evalRes.data?.reflection_result) {
              data.latest_evaluation = evalRes.data;
            }
          } catch (e) {
            console.warn("Could not fetch latest evaluation details", e);
          }
        }
        setTaskData(data);
      } catch (err) {
        console.error("Failed to load task details", err);
      }
    }
    loadDetails();
  }, [selectedTaskId]);

  const handleEvolve = async () => {
    if (!selectedTaskId) return;
    setIsEvolving(true);
    setError(null);
    try {
      const res = await evolveArchitecture(selectedTaskId);
      setEvolutionSuccess(
        `Architecture successfully evolved into Version 2! Applied modifications: ${res.modifications_applied.join(", ")}`
      );
      // Reload task data
      const updated = await api.get(`/tasks/${selectedTaskId}`);
      setTaskData(updated.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to evolve architecture");
    } finally {
      setIsEvolving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 14 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading diagnostic reflections &amp; failure analyses…</p>
      </div>
    );
  }

  const reflection: ReflectionResult | null =
    taskData?.latest_evaluation?.reflection_result || null;
  const isEvolved = !!taskData?.architecture_versions?.v2;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Target Task Selector */}
      <TaskSelector
        tasks={tasks}
        selectedTaskId={selectedTaskId}
        onSelectTaskId={setSelectedTaskId}
        label="Diagnosis Target"
        actionRight={
          selectedTaskId ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <Link href={`/evolution?task_id=${selectedTaskId}`} className="btn btn-secondary btn-sm">
                View Comparative Deltas →
              </Link>
              <Link href={`/run/${selectedTaskId}`} className="btn btn-primary btn-sm">
                Run Workbench
              </Link>
            </div>
          ) : undefined
        }
      />

      {evolutionSuccess && (
        <div
          className="fade-up"
          style={{
            padding: "12px 18px",
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
          <span>✓ {evolutionSuccess}</span>
          <Link href={`/run/${selectedTaskId}?exec=run_2`} className="btn btn-primary btn-sm" style={{ fontSize: 11 }}>
            Execute V2 →
          </Link>
        </div>
      )}

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

      {reflection ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* Header Summary Banner */}
          <div
            className="card fade-up"
            style={{
              padding: "20px 24px",
              background: "linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%)",
              borderColor: "rgba(99, 102, 241, 0.25)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 10, marginBottom: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 18 }}>🔍</span>
                <h2 style={{ fontSize: 16, fontWeight: 800, color: "var(--text-primary)" }}>
                  Failure Diagnosis &amp; Root-Cause Reflection
                </h2>
              </div>
              {isEvolved && (
                <span className="badge badge-emerald">
                  ★ Evolved into Architecture V2
                </span>
              )}
            </div>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, maxWidth: 880 }}>
              The Reflection Engine critiques execution performance against verification and quality criteria, diagnoses architectural deficiencies, and formulates precise graph mutations.
            </p>
          </div>

          {/* Reflection Panel */}
          <div className="card fade-up" style={{ padding: "20px 24px" }}>
            <ReflectionPanel reflection={reflection} />
          </div>

          {/* Mutation Action CTA */}
          {!isEvolved ? (
            <div
              className="card fade-up"
              style={{
                padding: "24px",
                textAlign: "center",
                background: "linear-gradient(135deg, rgba(99, 102, 241, 0.08) 0%, rgba(16, 185, 129, 0.08) 100%)",
                borderColor: "rgba(99, 102, 241, 0.3)",
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 700, color: "#818cf8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6 }}>
                Autonomous Evolution
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 8, color: "var(--text-primary)" }}>
                Apply Recommendations &amp; Mutate Architecture into V2
              </h3>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 520, margin: "0 auto 18px", lineHeight: 1.5 }}>
                Programmatically update the multi-agent graph by adding the recommended specialist agents and rewiring connections to fix identified vulnerabilities.
              </p>
              <button
                onClick={handleEvolve}
                disabled={isEvolving}
                className="btn btn-primary"
                style={{ padding: "10px 24px" }}
              >
                {isEvolving ? (
                  <><span className="spinner" /> Mutating Architecture…</>
                ) : (
                  "Apply Recommendations & Mutate V2 →"
                )}
              </button>
            </div>
          ) : (
            <div
              className="card fade-up"
              style={{
                padding: "16px 20px",
                background: "rgba(16, 185, 129, 0.06)",
                border: "1px solid rgba(16, 185, 129, 0.25)",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: 12,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span className="status-dot live" />
                <span style={{ fontSize: 13, color: "#34d399", fontWeight: 700 }}>
                  Candidate Architecture V2 is actively synthesized and ready for execution.
                </span>
              </div>
              <Link href={`/run/${selectedTaskId}`} className="btn btn-emerald btn-sm">
                Execute Architecture V2 →
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-title">No Evaluation or Diagnostic Data Available</div>
          <div className="empty-state-desc">
            The selected task has not been evaluated yet. Run the evaluation pipeline to perform root-cause failure analysis.
          </div>
          <Link href={`/run/${selectedTaskId}`} className="btn btn-primary btn-sm">
            Go to Run Workbench →
          </Link>
        </div>
      )}
    </div>
  );
}
