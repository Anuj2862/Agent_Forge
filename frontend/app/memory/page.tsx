"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getMemoryStatus,
  retrieveSimilarExperiences,
  getMemoryHistory,
  MemoryRecord,
} from "@/lib/api";
import KPICard from "@/components/KPICard";

const TASK_TYPES = [
  { value: "research", label: "Research & Synthesis" },
  { value: "data_analysis", label: "Data Analysis & Reasoning" },
  { value: "code_generation", label: "Code Generation & Refactor" },
  { value: "content_creation", label: "Content Creation" },
  { value: "problem_solving", label: "Problem Solving" },
  { value: "general", label: "General Multi-Agent Task" },
];

const COMPLEXITIES = [
  { value: "low", label: "Low (1-2 Agents)" },
  { value: "medium", label: "Medium (3-4 Agents)" },
  { value: "high", label: "High (5+ Agents)" },
];

export default function MemoryPage() {
  const [status, setStatus] = useState<{ status: string; module: string; total_records: number } | null>(null);
  const [selectedType, setSelectedType] = useState<string>("research");
  const [selectedComplexity, setSelectedComplexity] = useState<string>("low");
  const [queryResults, setQueryResults] = useState<MemoryRecord[]>([]);
  const [recentRecords, setRecentRecords] = useState<MemoryRecord[]>([]);
  const [isQuerying, setIsQuerying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [memStatus, historyData] = await Promise.all([
          getMemoryStatus().catch(() => ({ status: "active", total_records: 0, module: "SQLite Memory Engine" })),
          getMemoryHistory(1, 10).catch(() => ({ records: [], total: 0 })),
        ]);
        setStatus(memStatus);
        setRecentRecords(historyData.records || []);

        // Initial sample query
        const initial = await retrieveSimilarExperiences("research", "low", 4);
        setQueryResults(initial.experiences || []);
      } catch (err) {
        console.error("Failed to load memory data", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleRetrieve = async () => {
    setIsQuerying(true);
    try {
      const res = await retrieveSimilarExperiences(selectedType, selectedComplexity, 4);
      setQueryResults(res.experiences || []);
    } catch (err) {
      console.error("Retrieval failed", err);
    } finally {
      setIsQuerying(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 14 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Connecting to SQLite Evolutionary Memory Store…</p>
      </div>
    );
  }

  const totalCount = status?.total_records ?? recentRecords.length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header Banner */}
      <div
        className="card fade-up"
        style={{
          padding: "20px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 20 }}>🧠</span>
            <h1 style={{ fontSize: 18, fontWeight: 800 }}>Evolutionary Memory &amp; Experience Store</h1>
            <span className="badge badge-emerald">SQLite Engine Active</span>
          </div>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
            Persistent historical repository of executed agent graphs, evaluation rubrics, and diagnostic reflection lessons
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link href="/history" className="btn btn-secondary btn-sm">
            View All Experiments ({totalCount}) →
          </Link>
          <Link href="/" className="btn btn-primary btn-sm">
            + New Task
          </Link>
        </div>
      </div>

      {/* Translucent KPI Cards Row */}
      <div className="fade-up delay-1">
        <div className="kpi-grid">
          <KPICard
            label="Indexed Memory Records"
            value={totalCount}
            subtext="Available for synthesis retrieval"
            accentColor="#10B981"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <ellipse cx="12" cy="5" rx="9" ry="3" />
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
              </svg>
            }
          />

          <KPICard
            label="Database Persistence"
            value="SQLite ACID"
            subtext="Survives restart & power loss"
            accentColor="#3B82F6"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="3" width="18" height="18" rx="2" />
                <line x1="3" y1="9" x2="21" y2="9" />
              </svg>
            }
          />

          <KPICard
            label="Retrieval Engine"
            value="Tiered Match"
            subtext="Type + Complexity heuristic"
            accentColor="#22D3EE"
            icon={
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            }
          />
        </div>
      </div>

      {/* Interactive Experience Retriever Sandbox */}
      <div className="card fade-up">
        <div className="card-header">
          <div>
            <div className="card-title">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              Memory Retrieval Simulator
            </div>
            <div className="card-subtitle">
              Query historical experiences by task type and complexity to see what past architectures the Meta Controller surfaces
            </div>
          </div>
        </div>

        <div style={{ padding: "20px" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr auto",
              gap: 16,
              alignItems: "end",
              padding: "16px",
              background: "var(--bg-card-subtle)",
              borderRadius: 8,
              border: "1px solid var(--border-soft)",
              marginBottom: 20,
            }}
          >
            <div className="form-group">
              <label className="form-label" htmlFor="mem-type-select">
                Task Domain Type
              </label>
              <select
                id="mem-type-select"
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="form-control"
              >
                {TASK_TYPES.map((t) => (
                  <option key={t.value} value={t.value}>
                    {t.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="mem-complexity-select">
                Target Complexity
              </label>
              <select
                id="mem-complexity-select"
                value={selectedComplexity}
                onChange={(e) => setSelectedComplexity(e.target.value)}
                className="form-control"
              >
                {COMPLEXITIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={handleRetrieve}
              disabled={isQuerying}
              className="btn btn-primary"
              style={{ height: 38 }}
            >
              {isQuerying ? (
                <><span className="spinner" /> Querying…</>
              ) : (
                "Query Memory Store"
              )}
            </button>
          </div>

          {/* Query Results */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.06em", marginBottom: 12 }}>
              Retrieved Architecture Experiences ({queryResults.length})
            </div>

            {queryResults.length > 0 ? (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 14 }}>
                {queryResults.map((exp: MemoryRecord, idx: number) => {
                  const rating = exp.success_rating !== undefined ? (exp.success_rating * 100).toFixed(0) : "N/A";
                  const prompt = exp.task_spec?.user_prompt || exp.user_prompt || "Multi-agent research task";

                  return (
                    <div
                      key={exp.record_id || idx}
                      style={{
                        padding: "16px 18px",
                        borderRadius: 8,
                        background: "var(--bg-card-subtle)",
                        border: "1px solid var(--border-soft)",
                        display: "flex",
                        flexDirection: "column",
                        gap: 10,
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span className="badge badge-indigo">
                          {exp.task_type || selectedType}
                        </span>
                        <span className="badge badge-emerald">
                          ★ {rating}% Success
                        </span>
                      </div>

                      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", lineHeight: 1.4 }}>
                        &ldquo;{prompt}&rdquo;
                      </div>

                      <div style={{ fontSize: 11, color: "var(--text-secondary)", display: "flex", gap: 12 }}>
                        <span>Topology: <strong style={{ color: "#818cf8" }}>{exp.topology || "Pipeline"}</strong></span>
                        <span>Agents: <strong style={{ color: "#38bdf8" }}>{exp.agent_count || 1}</strong></span>
                        <span>Run #{exp.run_number || 1}</span>
                      </div>

                      {exp.recommendation_summary && (
                        <div style={{ fontSize: 11, color: "var(--text-muted)", background: "rgba(0,0,0,0.3)", padding: "8px 10px", borderRadius: 6, fontStyle: "italic" }}>
                          &ldquo;{exp.recommendation_summary}&rdquo;
                        </div>
                      )}

                      <div style={{ marginTop: "auto", paddingTop: 8, borderTop: "1px solid var(--border-soft)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <code style={{ fontSize: 10, color: "var(--text-muted)" }}>
                          {exp.record_id}
                        </code>
                        {exp.task_id && (
                          <Link href={`/run/${exp.task_id}`} style={{ fontSize: 11, color: "var(--indigo)", textDecoration: "none", fontWeight: 600 }}>
                            Inspect Run →
                          </Link>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "36px", color: "var(--text-muted)", fontSize: 13 }}>
                No prior experiences indexed for domain &ldquo;{selectedType}&rdquo; with &ldquo;{selectedComplexity}&rdquo; complexity. New syntheses will bootstrap from base templates.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
