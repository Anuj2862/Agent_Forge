"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  ArchitectureSpec,
  AgentConfig,
  listTasks,
} from "@/lib/api";
import ArchitectureGraph from "@/components/architecture/ArchitectureGraph";

export default function ArchitecturePage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [taskData, setTaskData] = useState<any>(null);
  const [selectedVersion, setSelectedVersion] = useState<"v1" | "v2">("v1");
  const [selectedAgent, setSelectedAgent] = useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Load available tasks
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

  // When selected task changes, load full task data
  useEffect(() => {
    if (!selectedTaskId) return;
    async function loadTaskDetails() {
      try {
        const res = await api.get(`/tasks/${selectedTaskId}`);
        setTaskData(res.data);
        if (res.data.architecture_versions?.v2) {
          setSelectedVersion("v2");
        } else {
          setSelectedVersion("v1");
        }
      } catch (err) {
        console.error("Failed to load task details", err);
      }
    }
    loadTaskDetails();
  }, [selectedTaskId]);

  const archV1: ArchitectureSpec | null =
    taskData?.architecture_versions?.v1 || taskData?.architecture_spec || null;
  const archV2: ArchitectureSpec | null =
    taskData?.architecture_versions?.v2 || null;

  const currentArch: ArchitectureSpec | null =
    selectedVersion === "v2" && archV2 ? archV2 : archV1;

  const v1AgentIds = new Set((archV1?.agents || []).map((a) => a.agent_id));
  const evolvedAgentIds = (archV2?.agents || [])
    .filter((a) => !v1AgentIds.has(a.agent_id))
    .map((a) => a.agent_id);

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 16 }}>
        <span className="spinner" style={{ width: 36, height: 36 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading architecture repository…</p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1320, margin: "0 auto", padding: "24px 20px 80px" }}>
      {/* Top action / selector bar */}
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
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 12, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase" }}>
              Active Task:
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
                    {t.task_id} ({t.task_type} · {t.complexity})
                  </option>
                ))}
              </select>
            ) : (
              <span style={{ fontSize: 13, color: "var(--text-muted)" }}>No tasks recorded yet</span>
            )}
          </div>

          {archV2 && (
            <div style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--bg-secondary)", padding: "3px 6px", borderRadius: 8, border: "1px solid var(--border-soft)" }}>
              <button
                onClick={() => setSelectedVersion("v1")}
                style={{
                  padding: "5px 12px",
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  border: "none",
                  background: selectedVersion === "v1" ? "var(--bg-card)" : "transparent",
                  color: selectedVersion === "v1" ? "#e2e8f0" : "var(--text-muted)",
                }}
              >
                Architecture v1 (Initial)
              </button>
              <button
                onClick={() => setSelectedVersion("v2")}
                style={{
                  padding: "5px 12px",
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: "pointer",
                  border: "none",
                  background: selectedVersion === "v2" ? "var(--bg-card)" : "transparent",
                  color: selectedVersion === "v2" ? "#34d399" : "var(--text-muted)",
                }}
              >
                Architecture v2 (Evolved ★)
              </button>
            </div>
          )}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          {selectedTaskId && (
            <>
              <Link
                href={`/execution?task_id=${selectedTaskId}`}
                className="btn btn-secondary"
                style={{ fontSize: 12, padding: "7px 14px" }}
              >
                Inspect Execution →
              </Link>
              <Link
                href={`/run/${selectedTaskId}`}
                className="btn btn-primary"
                style={{ fontSize: 12, padding: "7px 14px" }}
              >
                Full Run Dashboard
              </Link>
            </>
          )}
        </div>
      </div>

      {currentArch ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 24, alignItems: "start" }}>
          {/* Main Visualizer Area */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Graph Canvas */}
            <div
              className="card fade-up"
              style={{
                padding: "20px",
                position: "relative",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <h2 style={{ fontSize: 16, fontWeight: 700 }}>
                      Multi-Agent Graph Topology
                    </h2>
                    <span className="badge badge-violet">{currentArch.topology.toUpperCase()}</span>
                    {selectedVersion === "v2" && (
                      <span className="badge badge-emerald">Mutated v2</span>
                    )}
                  </div>
                  <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                    Interactive topological graph · Click on any agent node to inspect instructions and capabilities
                  </p>
                </div>
                <div style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                  {currentArch.agents.length} Agents · {currentArch.connections?.length || 0} Directed Channels
                </div>
              </div>

              {/* ReactFlow Interactive Canvas */}
              <div style={{ height: 420, borderRadius: 10, overflow: "hidden", border: "1px solid var(--border-soft)", background: "rgba(5, 7, 13, 0.7)" }}>
                <ArchitectureGraph
                  architecture={currentArch}
                  evolvedAgentIds={selectedVersion === "v2" ? evolvedAgentIds : []}
                  onSelectAgent={(agent) => setSelectedAgent(agent)}
                />
              </div>

              {/* Meta Reasoning Box */}
              {currentArch.meta_reasoning && (
                <div
                  style={{
                    marginTop: 16,
                    padding: "12px 16px",
                    borderRadius: 8,
                    background: "rgba(99,102,241,0.06)",
                    border: "1px solid rgba(99,102,241,0.2)",
                    fontSize: 12,
                    lineHeight: 1.6,
                    color: "var(--text-secondary)",
                  }}
                >
                  <strong style={{ color: "#a5b4fc", display: "block", marginBottom: 2 }}>
                    Meta Controller Architectural Reasoning:
                  </strong>
                  {currentArch.meta_reasoning}
                </div>
              )}
            </div>

            {/* Agent Team Roster */}
            <div className="card fade-up" style={{ padding: "20px" }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 16 }}>
                Agent Team Specification ({currentArch.agents.length} Specialized Roles)
              </h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
                {currentArch.agents.map((agent) => {
                  const isEvolved = evolvedAgentIds.includes(agent.agent_id);
                  const isSelected = selectedAgent?.agent_id === agent.agent_id;
                  return (
                    <div
                      key={agent.agent_id}
                      onClick={() => setSelectedAgent(agent)}
                      style={{
                        padding: "14px 16px",
                        borderRadius: 10,
                        background: isSelected ? "rgba(99,102,241,0.12)" : "var(--bg-secondary)",
                        border: isSelected
                          ? "1px solid #818cf8"
                          : isEvolved
                          ? "1px solid rgba(16,185,129,0.4)"
                          : "1px solid var(--border-soft)",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: "#f8fafc" }}>
                          {agent.name}
                        </div>
                        {isEvolved && (
                          <span className="badge badge-emerald" style={{ fontSize: 10 }}>★ Added in v2</span>
                        )}
                      </div>
                      <div style={{ fontSize: 11, color: "#818cf8", fontWeight: 600, marginBottom: 8 }}>
                        {agent.role}
                      </div>
                      <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.4, marginBottom: 10 }}>
                        {agent.objective}
                      </p>
                      {agent.tools && agent.tools.length > 0 && (
                        <div style={{ display: "flex", flexWrap: "wrap", gap: 5 }}>
                          {agent.tools.map((t) => (
                            <span key={t} className="badge badge-slate" style={{ fontSize: 10 }}>
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Sidebar: Agent Inspector */}
          <div className="card fade-up" style={{ padding: "20px", position: "sticky", top: 80 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
              <span>Agent Inspector</span>
              {selectedAgent && (
                <span className="badge badge-violet">{selectedAgent.agent_id}</span>
              )}
            </h3>

            {selectedAgent ? (
              <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: 12 }}>
                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", fontWeight: 600 }}>Name & Role</div>
                  <div style={{ fontSize: 14, fontWeight: 700, color: "#f1f5f9", marginTop: 2 }}>{selectedAgent.name}</div>
                  <div style={{ color: "#818cf8", fontWeight: 600 }}>{selectedAgent.role}</div>
                </div>

                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", fontWeight: 600 }}>Objective</div>
                  <div style={{ color: "var(--text-secondary)", lineHeight: 1.5, marginTop: 2 }}>
                    {selectedAgent.objective}
                  </div>
                </div>

                {selectedAgent.system_prompt && (
                  <div>
                    <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", fontWeight: 600 }}>System Prompt</div>
                    <div
                      style={{
                        marginTop: 4,
                        padding: "10px 12px",
                        background: "var(--bg-secondary)",
                        borderRadius: 6,
                        border: "1px solid var(--border-soft)",
                        fontFamily: "monospace",
                        fontSize: 11,
                        lineHeight: 1.5,
                        color: "#94a3b8",
                        maxHeight: 160,
                        overflowY: "auto",
                      }}
                    >
                      {selectedAgent.system_prompt}
                    </div>
                  </div>
                )}

                <div>
                  <div style={{ color: "var(--text-muted)", fontSize: 11, textTransform: "uppercase", fontWeight: 600 }}>Assigned Capabilities</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 6 }}>
                    {selectedAgent.tools?.map((tool) => (
                      <span key={tool} className="badge badge-cyan" style={{ fontSize: 11 }}>
                        ⚡ {tool}
                      </span>
                    )) || <span style={{ color: "var(--text-muted)" }}>None (Pure cognitive LLM)</span>}
                  </div>
                </div>

                {(selectedAgent.inputs || selectedAgent.outputs) && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, paddingTop: 10, borderTop: "1px solid var(--border-soft)" }}>
                    <div>
                      <div style={{ color: "var(--text-muted)", fontSize: 10, textTransform: "uppercase" }}>Inputs</div>
                      <div style={{ fontFamily: "monospace", color: "#38bdf8", fontSize: 11 }}>
                        {selectedAgent.inputs?.join(", ") || "raw_prompt"}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: "var(--text-muted)", fontSize: 10, textTransform: "uppercase" }}>Outputs</div>
                      <div style={{ fontFamily: "monospace", color: "#34d399", fontSize: 11 }}>
                        {selectedAgent.outputs?.join(", ") || "agent_response"}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: "40px 10px", color: "var(--text-muted)", fontSize: 12 }}>
                <p>Click on any agent in the diagram or list to inspect its full prompt, state I/O keys, and assigned tools.</p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="card" style={{ padding: "48px 24px", textAlign: "center" }}>
          <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>No Architectures Found</h3>
          <p style={{ color: "var(--text-muted)", fontSize: 13, marginBottom: 20 }}>
            Submit a task from the home page to synthesize an autonomous multi-agent architecture.
          </p>
          <Link href="/" className="btn btn-primary" style={{ display: "inline-block" }}>
            + Create New Task
          </Link>
        </div>
      )}
    </div>
  );
}
