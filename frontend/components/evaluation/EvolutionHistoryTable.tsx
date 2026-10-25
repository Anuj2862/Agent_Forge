"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { getMemoryHistory, MemoryRecord } from "@/lib/api";

export default function EvolutionHistoryTable() {
  const [records, setRecords] = useState<MemoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    getMemoryHistory(1, 50)
      .then((d) => {
        setRecords(d.records || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const filteredRecords = useMemo(() => {
    return records.filter((rec) => {
      const matchType = filterType === "all" || rec.task_type === filterType;
      const prompt = rec.task_spec?.user_prompt || rec.user_prompt || "";
      const matchSearch =
        !searchTerm.trim() ||
        rec.task_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
        prompt.toLowerCase().includes(searchTerm.toLowerCase());
      return matchType && matchSearch;
    });
  }, [records, filterType, searchTerm]);

  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "48px 0" }}>
        <span className="spinner" style={{ width: 28, height: 28, borderWidth: 3 }} />
      </div>
    );
  }

  if (records.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-state-title">No Evolution Memory Logs Found</div>
        <div className="empty-state-desc">
          Executed architectures and their evaluated ratings will be recorded here automatically.
        </div>
        <Link href="/" className="btn btn-primary btn-sm">
          + Launch Initial Experiment
        </Link>
      </div>
    );
  }

  return (
    <div className="card fade-up">
      {/* Table Toolbar */}
      <div
        style={{
          padding: "14px 18px",
          background: "var(--bg-card-subtle)",
          borderBottom: "1px solid var(--border-soft)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <input
            type="text"
            placeholder="Search experiments by prompt or task ID…"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="form-control"
            style={{ width: 280, fontSize: 12, padding: "6px 10px" }}
          />

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="form-control"
            style={{ width: 170, fontSize: 12, padding: "6px 26px 6px 10px" }}
            aria-label="Filter by task domain"
          >
            <option value="all">All Domains</option>
            <option value="research">Research</option>
            <option value="data_analysis">Data Analysis</option>
            <option value="code_generation">Code Generation</option>
            <option value="general">General</option>
          </select>
        </div>

        <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
          Showing <strong>{filteredRecords.length}</strong> of {records.length} experiences
        </span>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table className="research-table">
          <thead>
            <tr>
              <th>Task Domain &amp; ID</th>
              <th>Task Specification</th>
              <th>Architecture</th>
              <th style={{ textAlign: "center" }}>Run</th>
              <th style={{ textAlign: "center" }}>Composite Rating</th>
              <th>Recommendation Summary</th>
              <th style={{ textAlign: "right" }}>Inspect</th>
            </tr>
          </thead>
          <tbody>
            {filteredRecords.map((rec) => {
              const rating = rec.success_rating;
              const prompt = rec.task_spec?.user_prompt || rec.user_prompt || "Multi-agent research task";
              const targetTaskId = rec.task_spec?.task_id || rec.task_id;

              return (
                <tr key={rec.record_id}>
                  <td>
                    <div style={{ fontWeight: 600, color: "var(--text-primary)", marginBottom: 2 }}>
                      {rec.task_type.replace(/_/g, " ")}
                    </div>
                    <code style={{ fontSize: 11, color: "var(--text-muted)" }}>
                      {targetTaskId}
                    </code>
                  </td>

                  <td style={{ maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    &ldquo;{prompt}&rdquo;
                  </td>

                  <td>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span className="badge badge-indigo">{rec.topology}</span>
                      <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{rec.agent_count} agents</span>
                    </div>
                  </td>

                  <td style={{ textAlign: "center", fontFamily: "var(--font-mono, monospace)" }}>
                    <span className={rec.run_number > 1 ? "badge badge-emerald" : "badge badge-slate"}>
                      #{rec.run_number}
                    </span>
                  </td>

                  <td style={{ textAlign: "center" }}>
                    <span
                      style={{
                        fontSize: 13,
                        fontWeight: 800,
                        fontFamily: "var(--font-mono, monospace)",
                        color: rating >= 0.8 ? "#34d399" : rating >= 0.6 ? "#fbbf24" : "#fb7185",
                      }}
                    >
                      {rating !== undefined ? `${(rating * 100).toFixed(0)}%` : "N/A"}
                    </span>
                  </td>

                  <td style={{ maxWidth: 240, fontSize: 12, color: "var(--text-muted)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {rec.recommendation_summary || "—"}
                  </td>

                  <td style={{ textAlign: "right" }}>
                    <Link href={`/run/${targetTaskId}`} className="btn btn-secondary btn-sm" style={{ fontSize: 11 }}>
                      Workbench →
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
