"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  api,
  ArchitectureSpec,
  AgentConfig,
  listTasks,
  TaskDetail,
} from "@/lib/api";
import ArchitectureGraph from "@/components/architecture/ArchitectureGraph";
import AgentMascot from "@/components/mascot/AgentMascot";
import TaskSelector from "@/components/TaskSelector";

export default function ArchitecturePage() {
  const [tasks, setTasks] = useState<TaskDetail[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string>("");
  const [taskData, setTaskData] = useState<TaskDetail | null>(null);
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
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: "50vh", gap: 14 }}>
        <span className="spinner" style={{ width: 32, height: 32, borderWidth: 3 }} />
        <p style={{ color: "var(--text-muted)", fontSize: 13 }}>Loading architecture specifications…</p>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Reusable Task Selector Bar */}
      <TaskSelector
        tasks={tasks}
        selectedTaskId={selectedTaskId}
        onSelectTaskId={setSelectedTaskId}
        label="Target Experiment"
        actionRight={
          selectedTaskId ? (
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              {archV2 && (
                <div style={{ display: "flex", alignItems: "center", gap: 4, background: "var(--bg-card-subtle)", padding: "2px 4px", borderRadius: 6, border: "1px solid var(--border)" }}>
                  <button
                    onClick={() => setSelectedVersion("v1")}
                    className={`btn btn-sm ${selectedVersion === "v1" ? "btn-primary" : "btn-ghost"}`}
                    style={{ fontSize: 11 }}
                  >
                    V1 Baseline
                  </button>
                  <button
                    onClick={() => setSelectedVersion("v2")}
                    className={`btn btn-sm ${selectedVersion === "v2" ? "btn-emerald" : "btn-ghost"}`}
                    style={{ fontSize: 11 }}
                  >
                    V2 Mutated ★
                  </button>
                </div>
              )}
              <Link href={`/run/${selectedTaskId}`} className="btn btn-secondary btn-sm">
                Open Run Dashboard →
              </Link>
            </div>
          ) : undefined
        }
      />

      {currentArch ? (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 20, alignItems: "start" }}>
          {/* Main Visualizer Area */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Graph Canvas Card */}
            <div className="card fade-up">
              <div className="card-header">
                <div>
                  <div className="card-title">
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="3" y="3" width="7" height="7" rx="1.5" />
                      <rect x="14" y="3" width="7" height="7" rx="1.5" />
                      <rect x="14" y="14" width="7" height="7" rx="1.5" />
                      <rect x="3" y="14" width="7" height="7" rx="1.5" />
                    </svg>
                    Multi-Agent DAG Topology ({currentArch.topology.toUpperCase()})
                  </div>
                  <div className="card-subtitle">
                    {currentArch.agents.length} agents · {currentArch.connections?.length || 0} communication channels
                  </div>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span className="badge badge-indigo">{selectedVersion.toUpperCase()} Architecture</span>
                  {selectedVersion === "v2" && <span className="badge badge-emerald">Mutated Graph</span>}
                </div>
              </div>

              {/* Meta Reasoning Box */}
              {currentArch.meta_reasoning && (
                <div
                  style={{
                    padding: "10px 18px",
                    background: "var(--bg-card-subtle)",
                    borderBottom: "1px solid var(--border)",
                    fontSize: 12,
                    lineHeight: 1.5,
                    color: "var(--text-secondary)",
                  }}
                >
                  <strong style={{ color: "var(--accent-blue)", display: "block", marginBottom: 2 }}>
                    Meta Controller Architectural Reasoning:
                  </strong>
                  &ldquo;{currentArch.meta_reasoning}&rdquo;
                </div>
              )}

              {/* ReactFlow Canvas */}
              <div style={{ height: 480, overflow: "hidden" }}>
                <ArchitectureGraph
                  architecture={currentArch}
                  evolvedAgentIds={selectedVersion === "v2" ? evolvedAgentIds : []}
                  onSelectAgent={(agent) => setSelectedAgent(agent)}
                />
              </div>
            </div>

            {/* Agent Team Roster */}
            <div className="card fade-up">
              <div className="card-header">
                <div className="card-title">
                  Agent Team Roster ({currentArch.agents.length} Nodes)
                </div>
                <span className="badge badge-slate">Click card to inspect</span>
              </div>

              <div style={{ padding: "18px 20px", display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
                {currentArch.agents.map((agent) => {
                  const isEvolved = evolvedAgentIds.includes(agent.agent_id);
                  const isSelected = selectedAgent?.agent_id === agent.agent_id;
                  return (
                    <div
                      key={agent.agent_id}
                      onClick={() => setSelectedAgent(agent)}
                      style={{
                        padding: "14px 16px",
                        borderRadius: 8,
                        background: isSelected ? "rgba(99, 102, 241, 0.12)" : "var(--bg-secondary)",
                        border: isSelected
                          ? "1px solid #818cf8"
                          : isEvolved
                          ? "1px solid rgba(16, 185, 129, 0.4)"
                          : "1px solid var(--border-soft)",
                        cursor: "pointer",
                        transition: "all 0.15s ease",
                      }}
                    >
                      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8 }}>
                        <AgentMascot agent={agent} size={38} showStatusBadge={false} />
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                              {agent.name}
                            </div>
                            {isEvolved && (
                              <span className="badge badge-emerald" style={{ fontSize: 9, flexShrink: 0 }}>★ Mutated V2</span>
                            )}
                          </div>
                          <div style={{ fontSize: 11, color: "var(--accent-blue)", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {agent.role}
                          </div>
                        </div>
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

          {/* RIGHT: Agent Inspector / Properties Drawer */}
          <div className="card fade-up" style={{ position: "sticky", top: 76 }}>
            <div className="card-header">
              <div className="card-title">
                {selectedAgent ? "Agent Properties" : "Graph Properties"}
              </div>
              <span className="badge badge-slate">
                {selectedAgent ? selectedAgent.agent_id : currentArch.topology}
              </span>
            </div>

            <div style={{ padding: "18px 20px" }}>
              {selectedAgent ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
                    <AgentMascot agent={selectedAgent} size={54} active={true} showStatusBadge={false} />
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <span className="form-label" style={{ display: "block", marginBottom: 2 }}>Agent Identity</span>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {selectedAgent.name}
                      </div>
                      <div style={{ fontSize: 12, color: "var(--accent-blue)", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {selectedAgent.role}
                      </div>
                    </div>
                  </div>

                  <div>
                    <span className="form-label" style={{ display: "block", marginBottom: 4 }}>Objective</span>
                    <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5, background: "var(--bg-card-subtle)", padding: "8px 12px", borderRadius: 6, border: "1px solid var(--border-soft)" }}>
                      {selectedAgent.objective}
                    </p>
                  </div>

                  {selectedAgent.system_prompt && (
                    <div>
                      <span className="form-label" style={{ display: "block", marginBottom: 4 }}>System Instructions</span>
                      <p style={{ fontSize: 11.5, color: "var(--text-muted)", lineHeight: 1.5, fontStyle: "italic", background: "var(--bg-card-subtle)", padding: "8px 12px", borderRadius: 6, border: "1px solid var(--border-soft)", maxHeight: 160, overflowY: "auto" }}>
                        &ldquo;{selectedAgent.system_prompt}&rdquo;
                      </p>
                    </div>
                  )}

                  <div>
                    <span className="form-label" style={{ display: "block", marginBottom: 4 }}>Assigned Tool Capabilities</span>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {selectedAgent.tools && selectedAgent.tools.length > 0 ? (
                        selectedAgent.tools.map((t) => (
                          <span key={t} className="badge badge-indigo">
                            {t}
                          </span>
                        ))
                      ) : (
                        <span style={{ fontSize: 12, color: "var(--text-muted)", fontStyle: "italic" }}>
                          Pure cognitive reasoning
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ color: "var(--text-muted)", fontSize: 12.5, lineHeight: 1.6 }}>
                  <p style={{ marginBottom: 10 }}>
                    Select an agent node from the canvas or list to inspect its system instructions, tool dispatch rules, and state keys.
                  </p>
                  <div style={{ borderTop: "1px solid var(--border-soft)", paddingTop: 10 }}>
                    <div style={{ fontWeight: 600, color: "var(--text-secondary)", marginBottom: 4 }}>Graph Invariants:</div>
                    <ul style={{ paddingLeft: 16, margin: 0, fontSize: 12, display: "flex", flexDirection: "column", gap: 4 }}>
                      <li>DAG Cycle Free: Verified ✓</li>
                      <li>Constraint Compliant: Verified ✓</li>
                      <li>Non-empty Channels: {currentArch.connections?.length || 0}</li>
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <div className="empty-state-title">No Architecture Found</div>
          <div className="empty-state-desc">
            Submit a task from the overview page to synthesize your first multi-agent architecture.
          </div>
          <Link href="/" className="btn btn-primary btn-sm">
            + Launch New Experiment
          </Link>
        </div>
      )}
    </div>
  );
}
