"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  getMemoryStatus,
  retrieveSimilarExperiences,
  getMemoryHistory,
  MemoryRecord,
} from "@/lib/api";

const TASK_TYPES = [
  { value: "research", label: "Research & Synthesis" },
  { value: "code_generation", label: "Code Generation & Refactor" },
  { value: "data_analysis", label: "Data Analysis & Reasoning" },
  { value: "multi_hop_qa", label: "Multi-Hop Q&A" },
  { value: "creative_writing", label: "Creative & Copywriting" },
];

const COMPLEXITIES = [
  { value: "low", label: "Low (1-2 Agents)" },
  { value: "medium", label: "Medium (3-4 Agents)" },
  { value: "high", label: "High (5+ Agents)" },
];

export default function MemoryPage() {
  const [status, setStatus] = useState<any>(null);
  const [selectedType, setSelectedType] = useState<string>("research");
  const [selectedComplexity, setSelectedComplexity] = useState<string>("low");
  const [queryResults, setQueryResults] = useState<any[]>([]);
  const [recentRecords, setRecentRecords] = useState<MemoryRecord[]>([]);
  const [isQuerying, setIsQuerying] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [memStatus, historyData] = await Promise.all([
          getMemoryStatus().catch(() => ({ status: "active", total_records: 1, module: "SQLite Memory Engine" })),
          getMemoryHistory(1, 6).catch(() => ({ records: [], total: 0 })),
        ]);
        setStatus(memStatus);
        setRecentRecords(historyData.records || []);

        // Initial sample query
        const initial = await retrieveSimilarExperiences("research", "low", 3);
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
      const res = await retrieveSimilarExperiences(selectedType, selectedComplexity, 3);
      setQueryResults(res.experiences || []);
    } catch (err) {
      console.error("Retrieval failed", err);
    } finally {
      setIsQuerying(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 16 }}>
        <span className="spinner" style={{ width: 36, height: 36 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Connecting to SQLite Evolutionary Memory Store…</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "24px 20px 80px" }}>
      {/* Header Banner */}
      <div
        className="fade-up"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
          marginBottom: 24,
          padding: "20px 24px",
          background: "var(--bg-card)",
          borderRadius: 12,
          border: "1px solid var(--border)",
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 20 }}>🧠</span>
            <h1 style={{ fontSize: 18, fontWeight: 800 }}>Evolutionary Memory &amp; Experience Store</h1>
            <span className="badge badge-emerald">Active Engine</span>
          </div>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
            Persistent historical store of executed agent graphs, evaluation rubrics, and reflection lessons
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Link href="/history" className="btn btn-secondary" style={{ fontSize: 12, padding: "7px 14px" }}>
            View Full History Log →
          </Link>
          <Link href="/" className="btn btn-primary" style={{ fontSize: 12, padding: "7px 14px" }}>
            + Synthesize New Architecture
          </Link>
        </div>
      </div>

      {/* KPI Stats */}
      <div
        className="fade-up"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <div className="card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Total Memory Records
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#f1f5f9", marginTop: 4 }}>
            {status?.total_records ?? recentRecords.length ?? 1} Experiences
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
            Indexed &amp; available for synthesis retrieval
          </div>
        </div>

        <div className="card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Storage Architecture
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#818cf8", marginTop: 4 }}>
            SQLite + SQLAlchemy
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
            ACID persistent transaction log
          </div>
        </div>

        <div className="card" style={{ padding: "18px 20px" }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
            Retrieval Algorithm
          </div>
          <div style={{ fontSize: 22, fontWeight: 800, color: "#34d399", marginTop: 4 }}>
            Multi-Attribute Filtering
          </div>
          <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
            Ranked by weighted empirical success score
          </div>
        </div>
      </div>

      {/* Interactive Experience Retriever Sandbox */}
      <div className="card fade-up" style={{ padding: "24px", marginBottom: 24 }}>
        <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 6 }}>
          Interactive Memory Retrieval Sandbox
        </h3>
        <p style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 18 }}>
          Test how the Meta Controller queries past successful architectures when designing a new agent team.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr auto",
            gap: 16,
            alignItems: "end",
            padding: "16px",
            background: "var(--bg-secondary)",
            borderRadius: 10,
            border: "1px solid var(--border-soft)",
          }}
        >
          <div>
            <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
              Task Type:
            </label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              style={{
                width: "100%",
                background: "var(--bg-card)",
                color: "#f1f5f9",
                border: "1px solid var(--border)",
                borderRadius: 6,
                padding: "8px 12px",
                fontSize: 13,
              }}
            >
              {TASK_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
              Complexity Level:
            </label>
            <select
              value={selectedComplexity}
              onChange={(e) => setSelectedComplexity(e.target.value)}
              style={{
                width: "100%",
                background: "var(--bg-card)",
                color: "#f1f5f9",
                border: "1px solid var(--border)",
                borderRadius: 6,
                padding: "8px 12px",
                fontSize: 13,
              }}
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
            style={{ padding: "8px 20px", height: 38 }}
          >
            {isQuerying ? (
              <><span className="spinner" style={{ width: 14, height: 14 }} />Retrieving…</>
            ) : (
              "🔍 Query Memory"
            )}
          </button>
        </div>

        {/* Query Results */}
        <div style={{ marginTop: 24 }}>
          <h4 style={{ fontSize: 13, fontWeight: 700, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 14 }}>
            Retrieved Past Experiences ({queryResults.length})
          </h4>

          {queryResults.length > 0 ? (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))", gap: 16 }}>
              {queryResults.map((exp: any, idx: number) => (
                <div
                  key={exp.record_id || idx}
                  style={{
                    padding: "16px 18px",
                    borderRadius: 10,
                    background: "var(--bg-card)",
                    border: "1px solid var(--border-soft)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 10,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span className="badge badge-violet" style={{ fontSize: 10 }}>
                      {exp.task_type || selectedType}
                    </span>
                    <span className="badge badge-emerald" style={{ fontSize: 11, fontWeight: 700 }}>
                      ★ {((exp.success_rating || 0.85) * 100).toFixed(0)}% Score
                    </span>
                  </div>

                  <div style={{ fontSize: 13, fontWeight: 600, color: "#f1f5f9", lineHeight: 1.4 }}>
                    {exp.task_spec?.user_prompt || exp.user_prompt || "Market research and multi-agent plan synthesis"}
                  </div>

                  <div style={{ fontSize: 11, color: "var(--text-secondary)", display: "flex", gap: 14 }}>
                    <span>Topology: <strong style={{ color: "#818cf8" }}>{exp.topology || "Parallel"}</strong></span>
                    <span>Agents: <strong style={{ color: "#38bdf8" }}>{exp.agent_count || 3}</strong></span>
                    <span>Run #{exp.run_number || 1}</span>
                  </div>

                  {exp.recommendation_summary && (
                    <div style={{ fontSize: 11, color: "#94a3b8", background: "rgba(0,0,0,0.2)", padding: "8px 10px", borderRadius: 6, fontStyle: "italic" }}>
                      &ldquo;{exp.recommendation_summary}&rdquo;
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "30px", color: "var(--text-muted)", fontSize: 13 }}>
              No exact match for this combination in memory yet. Submit a task with this complexity to add it to the memory bank.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
