"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { TaskDetail } from "@/lib/api";

interface TaskSelectorProps {
  tasks: TaskDetail[];
  selectedTaskId: string;
  onSelectTaskId: (taskId: string) => void;
  label?: string;
  actionRight?: React.ReactNode;
}

export default function TaskSelector({
  tasks,
  selectedTaskId,
  onSelectTaskId,
  label = "Active Experiment",
  actionRight,
}: TaskSelectorProps) {
  const [search, setSearch] = useState("");

  const filteredTasks = useMemo(() => {
    if (!search.trim()) return tasks;
    const q = search.toLowerCase();
    return tasks.filter(
      (t) =>
        t.task_id.toLowerCase().includes(q) ||
        (t.user_prompt && t.user_prompt.toLowerCase().includes(q)) ||
        (t.task_type && t.task_type.toLowerCase().includes(q))
    );
  }, [tasks, search]);

  if (tasks.length === 0) {
    return (
      <div
        className="card"
        style={{
          padding: "16px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 16 }}>🧪</span>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              No Experiments Recorded Yet
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Submit a task with constraints to generate your initial multi-agent architecture.
            </div>
          </div>
        </div>
        <Link href="/" className="btn btn-primary btn-sm">
          + Launch Initial Experiment
        </Link>
      </div>
    );
  }

  return (
    <div
      className="card fade-up"
      style={{
        padding: "14px 18px",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        flexWrap: "wrap",
        gap: 14,
        marginBottom: 20,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--text-muted)" }}>
            {label}:
          </span>
        </div>

        {/* Task dropdown */}
        <select
          value={selectedTaskId}
          onChange={(e) => onSelectTaskId(e.target.value)}
          className="form-control"
          style={{
            maxWidth: 360,
            fontSize: 12,
            fontFamily: "var(--font-mono, monospace)",
            padding: "6px 28px 6px 10px",
          }}
          aria-label="Select active task"
        >
          {filteredTasks.map((t) => (
            <option key={t.task_id} value={t.task_id}>
              {t.task_id} ({t.task_type || "general"} · Run #{t.run_number || 1})
            </option>
          ))}
        </select>

        {tasks.length > 6 && (
          <input
            type="text"
            placeholder="Filter list…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="form-control"
            style={{ width: 110, fontSize: 11, padding: "5px 8px" }}
            aria-label="Filter tasks list"
          />
        )}

        {/* Selected Task Details snippet */}
        {(() => {
          const activeTask = tasks.find((t) => t.task_id === selectedTaskId);
          if (!activeTask) return null;
          return (
            <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
              <span className="badge badge-indigo">
                {activeTask.task_type?.replace(/_/g, " ") || "general"}
              </span>
              <span className="badge badge-cyan">
                {activeTask.complexity || "low"} complexity
              </span>
              <span className="badge badge-slate">
                Run #{activeTask.run_number || 1}
              </span>
              {activeTask.user_prompt && (
                <span
                  title={activeTask.user_prompt}
                  style={{
                    fontSize: 12,
                    color: "var(--text-muted)",
                    maxWidth: 320,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  &ldquo;{activeTask.user_prompt}&rdquo;
                </span>
              )}
            </div>
          );
        })()}
      </div>

      {actionRight && (
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {actionRight}
        </div>
      )}
    </div>
  );
}
