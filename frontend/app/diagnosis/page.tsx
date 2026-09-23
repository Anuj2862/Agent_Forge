"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  listEvaluations,
  listTasks,
  evolveArchitecture,
  ReflectionResult,
} from "@/lib/api";
import ReflectionPanel from "@/components/evaluation/ReflectionPanel";

export default function DiagnosisPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [taskData, setTaskData] = useState<any>(null);
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
        setTaskData(res.data);
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
    } catch (err: any) {
      setError(err.message || "Failed to evolve architecture");
    } finally {
      setIsEvolving(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 16 }}>
        <span className="spinner" style={{ width: 36, height: 36 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading diagnostic reflections…</p>
      </div>
    );
  }

  const reflection: ReflectionResult | null =
    taskData?.latest_evaluation?.reflection_result || null;
  const isEvolved = !!taskData?.architecture_versions?.v2;

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
            Target Task:
          </span>
          {tasks.length > 0 ? (
            <select
              value={selectedTaskId}
              onChange={(e) => setSelectedTaskId(e.target.value)}
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
              {tasks.map((t) => (
                <option key={t.task_id} value={t.task_id}>
                  {t.task_id} ({t.task_type} · {t.status})
                </option>
              ))}
            </select>
          ) : (
            <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No tasks logged</span>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {selectedTaskId && (
            <>
              <Link
                href={`/evolution?task_id=${selectedTaskId}`}
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: "7px 14px" }}
              >
                View Evolution Comparison →
              </Link>
              <Link
                href={`/run/${selectedTaskId}`}
                className="btn btn-primary"
                style={{ fontSize: 12, padding: "7px 14px" }}
              >
                Run Dashboard
              </Link>
            </>
          )}
        </div>
      </div>

      {evolutionSuccess && (
        <div
          className="fade-up"
          style={{
            padding: "14px 18px",
            marginBottom: 20,
            borderRadius: 8,
            background: "rgba(16,185,129,0.1)",
            border: "1px solid rgba(16,185,129,0.3)",
            color: "#34d399",
            fontSize: 13,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <span>✓ {evolutionSuccess}</span>
          <Link href="/evolution" className="btn btn-primary" style={{ fontSize: 11, padding: "4px 10px" }}>
            Inspect Deltas →
          </Link>
        </div>
      )}

      {error && (
        <div
          className="fade-up"
          style={{
            padding: "14px 18px",
            marginBottom: 20,
            borderRadius: 8,
            background: "rgba(244,63,94,0.1)",
            border: "1px solid rgba(244,63,94,0.3)",
            color: "#fb7185",
            fontSize: 13,
          }}
        >
          ⚠ {error}
        </div>
      )}

      {reflection ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* Header Summary Banner */}
          <div
            className="card fade-up"
            style={{
              padding: "24px",
              background: "linear-gradient(135deg, rgba(139,92,246,0.08) 0%, rgba(99,102,241,0.08) 100%)",
              borderColor: "rgba(139,92,246,0.25)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: 20 }}>🧠</span>
              <h2 style={{ fontSize: 18, fontWeight: 800 }}>Reflection &amp; Root-Cause Analysis</h2>
              {isEvolved && (
                <span className="badge badge-emerald" style={{ marginLeft: "auto" }}>
                  ★ Evolved into Architecture v2
                </span>
              )}
            </div>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, maxWidth: 900 }}>
              The Reflection Engine critiques execution performance against verification and quality criteria, diagnoses architectural deficiencies, and formulates precise graph mutations.
            </p>
          </div>

          {/* Reflection Panel Component */}
          <div className="card fade-up" style={{ padding: "24px" }}>
            <ReflectionPanel reflection={reflection} />
          </div>

          {/* Mutation Action CTA */}
          {!isEvolved ? (
            <div
              className="card fade-up"
              style={{
                padding: "24px",
                textAlign: "center",
                background: "linear-gradient(135deg, rgba(99,102,241,0.08) 0%, rgba(16,185,129,0.08) 100%)",
                borderColor: "rgba(99,102,241,0.3)",
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 700, color: "#818cf8", textTransform: "uppercase", letterSpacing: ".08em", marginBottom: 6 }}>
                Autonomous Evolution
              </div>
              <h3 style={{ fontSize: 16, fontWeight: 800, marginBottom: 8 }}>
                Apply Recommendations &amp; Mutate Architecture
              </h3>
              <p style={{ fontSize: 13, color: "var(--text-secondary)", maxWidth: 520, margin: "0 auto 18px" }}>
                Programmatically update the multi-agent graph by adding the recommended specialist agents and rewiring connections to fix identified vulnerabilities.
              </p>
              <button
                onClick={handleEvolve}
                disabled={isEvolving}
                className="btn btn-primary"
                style={{ padding: "10px 24px" }}
              >
                {isEvolving ? (
                  <><span className="spinner" style={{ width: 16, height: 16 }} />Mutating Architecture Graph…</>
                ) : (
                  "Apply Recommendations & Evolve Graph →"
                )}
              </button>
            </div>
          ) : (
            <div
              className="card fade-up"
              style={{
                padding: "20px",
                background: "rgba(16,185,129,0.05)",
                border: "1px solid rgba(16,185,129,0.25)",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 12,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <span style={{ fontSize: 20 }}>✓</span>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "#34d399" }}>
                    Mutated Architecture v2 Already Active
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                    Recommendations applied. Architecture v2 is ready for verification execution and side-by-side comparison.
                  </div>
                </div>
              </div>
              <Link href="/evolution" className="btn btn-primary" style={{ fontSize: 12, padding: "7px 14px" }}>
                View Evolution Comparison →
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="card" style={{ padding: "48px 24px", textAlign: "center" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>No Diagnostic Reflections Found</h3>
          <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>
            Run an evaluation on an executed task to trigger automated reflection and recommendations.
          </p>
          <Link href="/" className="btn btn-primary" style={{ display: "inline-block" }}>
            + Create New Task
          </Link>
        </div>
      )}
    </div>
  );
}
