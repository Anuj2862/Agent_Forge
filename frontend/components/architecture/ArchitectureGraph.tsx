"use client";

import { useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { ArchitectureSpec, AgentConfig, Connection } from "@/lib/api";
import { useTheme } from "@/lib/theme";

const defaultNodeTypes = {};
const defaultEdgeTypes = {};

export function getAgentIdentity(agent: AgentConfig, isLight = false) {
  const text = `${agent.agent_id} ${agent.name} ${agent.role}`.toLowerCase();
  if (text.includes("plan") || text.includes("decompos")) {
    return {
      name: "Planner",
      color: isLight ? "#0D9488" : "#2DD4BF",
      lightColor: isLight ? "rgba(13, 148, 136, 0.12)" : "rgba(45, 212, 191, 0.12)",
      border: "rgba(45, 212, 191, 0.35)",
      borderLight: "rgba(13, 148, 136, 0.45)",
    };
  }
  if (text.includes("verif") || text.includes("fact") || text.includes("audit") || text.includes("check")) {
    return {
      name: "Verifier",
      color: isLight ? "#0891B2" : "#22D3EE",
      lightColor: isLight ? "rgba(8, 145, 178, 0.12)" : "rgba(34, 211, 238, 0.12)",
      border: "rgba(34, 211, 238, 0.40)",
      borderLight: "rgba(8, 145, 178, 0.45)",
    };
  }
  if (text.includes("research") || text.includes("retriev") || text.includes("search") || text.includes("gather")) {
    return {
      name: "Researcher",
      color: isLight ? "#2563EB" : "#3B82F6",
      lightColor: isLight ? "rgba(37, 99, 235, 0.12)" : "rgba(59, 130, 246, 0.12)",
      border: "rgba(59, 130, 246, 0.35)",
      borderLight: "rgba(37, 99, 235, 0.45)",
    };
  }
  if (text.includes("analy") || text.includes("reason") || text.includes("eval")) {
    return {
      name: "Analyst",
      color: isLight ? "#7C3AED" : "#A78BFA",
      lightColor: isLight ? "rgba(124, 58, 237, 0.12)" : "rgba(167, 139, 250, 0.12)",
      border: "rgba(167, 139, 250, 0.35)",
      borderLight: "rgba(124, 58, 237, 0.45)",
    };
  }
  if (text.includes("critic") || text.includes("review") || text.includes("reflec")) {
    return {
      name: "Critic",
      color: isLight ? "#DC2626" : "#F87171",
      lightColor: isLight ? "rgba(220, 38, 38, 0.12)" : "rgba(248, 113, 113, 0.12)",
      border: "rgba(248, 113, 113, 0.35)",
      borderLight: "rgba(220, 38, 38, 0.45)",
    };
  }
  return {
    name: "Executor",
    color: isLight ? "#B77900" : "#FBBF24",
    lightColor: isLight ? "rgba(183, 121, 0, 0.12)" : "rgba(251, 191, 36, 0.12)",
    border: "rgba(251, 191, 36, 0.35)",
    borderLight: "rgba(183, 121, 0, 0.45)",
  };
}

interface Props {
  architecture: ArchitectureSpec;
  agentStatuses?: Record<string, "waiting" | "active" | "completed" | "failed">;
  evolvedAgentIds?: string[];
  onSelectAgent?: (agent: AgentConfig) => void;
}

export default function ArchitectureGraph({
  architecture,
  agentStatuses = {},
  evolvedAgentIds = [],
  onSelectAgent,
}: Props) {
  const [inspectedAgent, setInspectedAgent] = useState<AgentConfig | null>(null);
  const [viewMode, setViewMode] = useState<"graph" | "accessible">("graph");
  const theme = useTheme();
  const isLight = theme === "light";

  const { nodes, edges } = useMemo(() => {
    const agents = architecture.agents || [];
    const connections = architecture.connections || [];
    const topology = architecture.topology || "pipeline";

    // Adaptive positioning computation to prevent node overlap across all topologies
    const stepX = 330;
    const stepY = 240;

    // Detect graph dependencies and in-degrees
    const inDegrees: Record<string, number> = {};
    agents.forEach((a) => {
      inDegrees[a.agent_id] = 0;
    });
    connections.forEach((c) => {
      if (inDegrees[c.target] !== undefined) {
        inDegrees[c.target]++;
      }
    });

    const hasEdges = connections.length > 0;
    const positions: Record<string, { x: number; y: number }> = {};

    if (topology === "parallel") {
      // In parallel topology, worker nodes execute concurrently side-by-side
      if (!hasEdges || agents.every((a) => inDegrees[a.agent_id] === 0)) {
        if (agents.length <= 3) {
          // Place parallel workers horizontally side by side
          agents.forEach((agent, i) => {
            positions[agent.agent_id] = {
              x: 60 + i * stepX,
              y: 120,
            };
          });
        } else {
          // Multi-row grid with ample horizontal and vertical clearance
          const cols = Math.ceil(Math.sqrt(agents.length));
          agents.forEach((agent, i) => {
            const col = i % cols;
            const row = Math.floor(i / cols);
            positions[agent.agent_id] = {
              x: 60 + col * stepX,
              y: 50 + row * stepY,
            };
          });
        }
      } else {
        // Evolved parallel topology with downstream verifier/synthesis node
        const rootNodes = agents.filter((a) => inDegrees[a.agent_id] === 0);
        const downstreamNodes = agents.filter((a) => inDegrees[a.agent_id] > 0);

        rootNodes.forEach((a, i) => {
          positions[a.agent_id] = {
            x: 60 + i * stepX,
            y: 40,
          };
        });

        const totalRootWidth = Math.max(1, rootNodes.length - 1) * stepX;
        downstreamNodes.forEach((a, j) => {
          const startX = Math.max(60, 60 + (totalRootWidth - (downstreamNodes.length - 1) * stepX) / 2);
          positions[a.agent_id] = {
            x: startX + j * stepX,
            y: 40 + stepY,
          };
        });
      }
    } else if (topology === "hierarchical") {
      // Supervisor at top, worker nodes below
      if (agents.length > 0) {
        const subCount = Math.max(1, agents.length - 1);
        positions[agents[0].agent_id] = {
          x: 60 + ((subCount - 1) * stepX) / 2,
          y: 35,
        };
        for (let i = 1; i < agents.length; i++) {
          positions[agents[i].agent_id] = {
            x: 60 + (i - 1) * stepX,
            y: 35 + stepY,
          };
        }
      }
    } else {
      // Pipeline / sequential workflow
      agents.forEach((agent, i) => {
        positions[agent.agent_id] = {
          x: 60 + i * stepX,
          y: 130,
        };
      });
    }

    const computedNodes = agents.map((agent: AgentConfig, index: number) => {
      const identity = getAgentIdentity(agent, isLight);
      const isEvolved = evolvedAgentIds.includes(agent.agent_id);
      const status = agentStatuses[agent.agent_id] || "waiting";
      const pos = positions[agent.agent_id] || { x: 60 + index * stepX, y: 130 };

      const borderColor = isEvolved
        ? (isLight ? "#059669" : "rgba(16, 185, 129, 0.6)")
        : (isLight ? identity.borderLight : identity.border);

      return {
        id: agent.agent_id,
        position: pos,
        data: {
          label: (
            <div
              className="flex flex-col text-left cursor-pointer"
              onClick={() => {
                setInspectedAgent(agent);
                if (onSelectAgent) onSelectAgent(agent);
              }}
              role="button"
              tabIndex={0}
              aria-label={`Inspect agent ${agent.name}`}
              style={{ padding: "10px 14px", position: "relative" }}
            >
              {/* Top Accent Line */}
              <div
                style={{
                  position: "absolute",
                  top: 0,
                  left: 0,
                  right: 0,
                  height: 3,
                  background: isEvolved ? "#10b981" : identity.color,
                  borderTopLeftRadius: 8,
                  borderTopRightRadius: 8,
                }}
              />

              {/* Row 1: Monospace ID + Role / Evolution Badge */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 6, gap: 8 }}>
                <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.02em" }}>
                  {agent.agent_id}
                </span>
                {isEvolved ? (
                  <span
                    style={{
                      fontSize: 10,
                      fontWeight: 600,
                      color: isLight ? "#047857" : "#10b981",
                      background: isLight ? "#DCFCE7" : "rgba(16, 185, 129, 0.15)",
                      padding: "1px 6px",
                      borderRadius: 4,
                      border: isLight ? "1px solid #86EFAC" : "1px solid rgba(16, 185, 129, 0.3)",
                    }}
                  >
                    ★ V2 Mutated
                  </span>
                ) : (
                  <span
                    style={{
                      fontSize: 10.5,
                      fontWeight: 600,
                      color: identity.color,
                    }}
                  >
                    {identity.name}
                  </span>
                )}
              </div>

              {/* Row 2: Agent Name */}
              <div style={{ fontSize: 13.5, fontWeight: 700, color: "var(--text-primary)", lineHeight: 1.3, marginBottom: 2 }}>
                {agent.name}
              </div>

              {/* Row 3: Role Definition */}
              <div style={{ fontSize: 12, color: "var(--text-secondary)", marginBottom: 6, lineHeight: 1.3 }}>
                {agent.role}
              </div>

              {/* Row 4: Tools Summary or Execution Status */}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 6, fontSize: 11, borderTop: "1px solid var(--border-soft)", paddingTop: 6, marginTop: 2 }}>
                <span style={{ color: "var(--text-muted)", fontSize: 10.5 }}>
                  {agent.tools && agent.tools.length > 0 ? (
                    <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                      {agent.tools.slice(0, 2).join(", ")}
                      {agent.tools.length > 2 ? ` +${agent.tools.length - 2}` : ""}
                    </span>
                  ) : (
                    "Cognitive reasoning"
                  )}
                </span>

                {status !== "waiting" && (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 4,
                      fontSize: 10.5,
                      color: status === "active" ? "#38bdf8" : status === "completed" ? "#34d399" : "#f87171",
                      textTransform: "capitalize",
                    }}
                  >
                    <span
                      style={{
                        width: 5,
                        height: 5,
                        borderRadius: "50%",
                        background: status === "active" ? "#38bdf8" : status === "completed" ? "#34d399" : "#f87171",
                      }}
                    />
                    {status}
                  </span>
                )}
              </div>
            </div>
          ),
        },
        style: {
          background: isLight ? "#FFFFFF" : "var(--bg-card)",
          border: `1.5px solid ${borderColor}`,
          borderRadius: 8,
          width: 275,
          boxShadow: isLight
            ? (isEvolved
                ? "0 4px 16px rgba(16, 185, 129, 0.22), 0 1px 3px rgba(0,0,0,0.06)"
                : "0 4px 16px rgba(15, 23, 42, 0.08), 0 1px 3px rgba(15, 23, 42, 0.04)")
            : (isEvolved
                ? "0 4px 16px rgba(16, 185, 129, 0.18)"
                : "0 4px 16px rgba(0, 0, 0, 0.25)"),
          backdropFilter: "blur(12px)",
          WebkitBackdropFilter: "blur(12px)",
        },
      };
    });

    const computedEdges = connections.map((conn: Connection, idx: number) => ({
      id: `e-${conn.source}-${conn.target}-${idx}`,
      source: conn.source,
      target: conn.target,
      animated: true,
      style: {
        stroke: isLight ? "#2563EB" : "#38BDF8",
        strokeWidth: 1.5,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isLight ? "#2563EB" : "#38BDF8",
        width: 14,
        height: 14,
      },
    }));

    return { nodes: computedNodes, edges: computedEdges };
  }, [
    architecture.agents,
    architecture.connections,
    architecture.topology,
    agentStatuses,
    evolvedAgentIds,
    isLight,
    onSelectAgent,
  ]);

  const allAgents = architecture.agents || [];
  const allConnections = architecture.connections || [];

  return (
    <div
      className="relative w-full h-full rounded-xl overflow-hidden"
      style={{
        display: "flex",
        flexDirection: "column",
        minHeight: "100%",
        height: "100%",
        background: "var(--bg-surface)",
      }}
    >
      {/* Top Controls Toolbar Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "8px 16px",
          borderBottom: "1px solid var(--border)",
          background: "var(--bg-card-subtle)",
          flexShrink: 0,
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
          <span style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)" }}>
            Topology:
          </span>
          <span className="badge badge-indigo" style={{ textTransform: "capitalize", fontSize: 11 }}>
            {architecture.topology}
          </span>
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            • {allAgents.length} Agents • {allConnections.length} Channels
          </span>
        </div>

        {/* View Mode Toggle Button Group */}
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            background: "var(--bg-card)",
            padding: "2px",
            borderRadius: 6,
            border: "1px solid var(--border)",
          }}
        >
          <button
            onClick={() => setViewMode("graph")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              padding: "4px 10px",
              borderRadius: 4,
              fontSize: 11.5,
              fontWeight: viewMode === "graph" ? 600 : 500,
              background: viewMode === "graph" ? "var(--accent-blue)" : "transparent",
              color: viewMode === "graph" ? "#ffffff" : "var(--text-secondary)",
              border: "none",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="6" cy="6" r="3" />
              <circle cx="18" cy="18" r="3" />
              <line x1="8.5" y1="8.5" x2="15.5" y2="15.5" />
            </svg>
            Graph Canvas
          </button>
          <button
            onClick={() => setViewMode("accessible")}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 5,
              padding: "4px 10px",
              borderRadius: 4,
              fontSize: 11.5,
              fontWeight: viewMode === "accessible" ? 600 : 500,
              background: viewMode === "accessible" ? "var(--accent-blue)" : "transparent",
              color: viewMode === "accessible" ? "#ffffff" : "var(--text-secondary)",
              border: "none",
              cursor: "pointer",
              transition: "all 0.15s ease",
            }}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="8" y1="6" x2="21" y2="6" />
              <line x1="8" y1="12" x2="21" y2="12" />
              <line x1="8" y1="18" x2="21" y2="18" />
              <line x1="3" y1="6" x2="3.01" y2="6" />
              <line x1="3" y1="12" x2="3.01" y2="12" />
              <line x1="3" y1="18" x2="3.01" y2="18" />
            </svg>
            Structured List
          </button>
        </div>
      </div>

      {viewMode === "graph" ? (
        <div style={{ flex: 1, position: "relative", width: "100%", height: "100%" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={defaultNodeTypes}
            edgeTypes={defaultEdgeTypes}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            attributionPosition="bottom-left"
          >
            <Background color={isLight ? "#CBD5E1" : "rgba(148, 163, 184, 0.2)"} gap={24} size={1} />
            <Controls />
          </ReactFlow>
        </div>
      ) : (
        /* Accessible Structured Representation */
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {allAgents.map((agent, i) => {
              const identity = getAgentIdentity(agent, isLight);
              const isEvolved = evolvedAgentIds.includes(agent.agent_id);
              const inbounds = allConnections.filter((c) => c.target === agent.agent_id);
              const outbounds = allConnections.filter((c) => c.source === agent.agent_id);

              return (
                <div
                  key={agent.agent_id}
                  onClick={() => {
                    setInspectedAgent(agent);
                    if (onSelectAgent) onSelectAgent(agent);
                  }}
                  style={{
                    padding: "14px 18px",
                    borderRadius: 10,
                    border: isEvolved ? "1.5px solid var(--emerald)" : "1px solid var(--border)",
                    background: "var(--bg-card)",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.borderColor = "var(--border-strong)";
                    e.currentTarget.style.transform = "translateY(-1px)";
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.borderColor = isEvolved ? "var(--emerald)" : "var(--border)";
                    e.currentTarget.style.transform = "none";
                  }}
                >
                  {/* Top Bar: #num, Role Tag, Agent Name, ID */}
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8, flexWrap: "wrap", gap: 8 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          fontFamily: "'JetBrains Mono', monospace",
                          color: "var(--text-muted)",
                          background: "var(--bg-card-subtle)",
                          padding: "2px 6px",
                          borderRadius: 4,
                          border: "1px solid var(--border-soft)",
                        }}
                      >
                        #{i + 1}
                      </span>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          color: identity.color,
                          background: identity.lightColor,
                          padding: "2px 8px",
                          borderRadius: 4,
                          border: `1px solid ${identity.border}`,
                        }}
                      >
                        {identity.name}
                      </span>
                      <strong style={{ fontSize: 13.5, fontWeight: 700, color: "var(--text-primary)" }}>
                        {agent.name}
                      </strong>
                      {isEvolved && (
                        <span className="badge badge-emerald">★ Mutated V2</span>
                      )}
                    </div>

                    <code
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 11.5,
                        color: "var(--accent-blue)",
                        background: "var(--accent-blue-subtle)",
                        padding: "2px 8px",
                        borderRadius: 4,
                        border: "1px solid var(--border-soft)",
                      }}
                    >
                      {agent.agent_id}
                    </code>
                  </div>

                  {/* Role & Objective */}
                  <p style={{ fontSize: 12.5, color: "var(--text-secondary)", lineHeight: 1.5, margin: "0 0 10px" }}>
                    {agent.role}
                    {agent.objective && agent.objective !== agent.role && (
                      <span style={{ display: "block", color: "var(--text-muted)", fontSize: 12, marginTop: 4 }}>
                        Objective: {agent.objective}
                      </span>
                    )}
                  </p>

                  {/* Metadata Footer: Tools, Flow Dependencies */}
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      paddingTop: 10,
                      borderTop: "1px solid var(--border-soft)",
                      flexWrap: "wrap",
                      gap: 12,
                      fontSize: 11.5,
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap" }}>
                      <span style={{ color: "var(--text-muted)", fontWeight: 600 }}>Tools:</span>
                      {agent.tools && agent.tools.length > 0 ? (
                        agent.tools.map((t) => (
                          <span
                            key={t}
                            style={{
                              fontFamily: "'JetBrains Mono', monospace",
                              fontSize: 11,
                              color: "var(--text-secondary)",
                              background: "var(--bg-card-subtle)",
                              border: "1px solid var(--border)",
                              padding: "1px 6px",
                              borderRadius: 4,
                            }}
                          >
                            {t}
                          </span>
                        ))
                      ) : (
                        <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Cognitive Reasoning (No Tools)</span>
                      )}
                    </div>

                    <div style={{ display: "flex", alignItems: "center", gap: 14, color: "var(--text-muted)", fontSize: 11 }}>
                      <span>
                        Depends on: <strong style={{ color: "var(--text-primary)" }}>{inbounds.length ? inbounds.map((c) => c.source).join(", ") : "Root"}</strong>
                      </span>
                      <span>
                        Feeds into: <strong style={{ color: "var(--text-primary)" }}>{outbounds.length ? outbounds.map((c) => c.target).join(", ") : "Terminal"}</strong>
                      </span>
                      <span style={{ color: "var(--accent-blue)", fontWeight: 600, display: "inline-flex", alignItems: "center", gap: 3 }}>
                        Inspect ↗
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Agent Inspector Drawer */}
      {inspectedAgent && (
        <div
          className="absolute top-3 right-3 bottom-3 w-80 rounded-lg p-4 text-xs overflow-y-auto z-20"
          style={{
            background: "var(--bg-card)",
            backdropFilter: "blur(16px)",
            border: "1px solid var(--border-strong)",
            boxShadow: "0 12px 32px rgba(0, 0, 0, 0.15)",
          }}
        >
          <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", borderBottom: "1px solid var(--border-soft)", paddingBottom: 10 }}>
            <div>
              <span style={{ fontSize: 10.5, color: "var(--blue-primary)", fontWeight: 600 }}>
                Agent Inspector
              </span>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", marginTop: 2 }}>{inspectedAgent.name}</h4>
              <p style={{ fontSize: 12, color: "var(--text-muted)" }}>{inspectedAgent.role}</p>
            </div>
            <button
              onClick={() => setInspectedAgent(null)}
              style={{
                color: "var(--text-muted)",
                background: "none",
                border: "none",
                fontSize: 14,
                cursor: "pointer",
                padding: "2px 6px",
              }}
              aria-label="Close inspector"
            >
              ✕
            </button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
            <div>
              <span style={{ fontSize: 10.5, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", display: "block", marginBottom: 4 }}>
                Objective
              </span>
              <p style={{ color: "var(--text-primary)", lineHeight: 1.5, background: "var(--bg-card-subtle)", padding: 8, borderRadius: 6, border: "1px solid var(--border-soft)" }}>
                {inspectedAgent.objective || "Standard task execution"}
              </p>
            </div>

            {inspectedAgent.system_prompt && (
              <div>
                <span style={{ fontSize: 10.5, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", display: "block", marginBottom: 4 }}>
                  System Prompt
                </span>
                <p style={{ color: "var(--text-secondary)", lineHeight: 1.5, background: "var(--bg-card-subtle)", padding: 8, borderRadius: 6, border: "1px solid var(--border-soft)", fontStyle: "italic", maxHeight: 130, overflowY: "auto" }}>
                  &ldquo;{inspectedAgent.system_prompt}&rdquo;
                </p>
              </div>
            )}

            <div>
              <span style={{ fontSize: 10.5, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", display: "block", marginBottom: 4 }}>
                Assigned Tools ({inspectedAgent.tools?.length || 0})
              </span>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                {inspectedAgent.tools && inspectedAgent.tools.length > 0 ? (
                  inspectedAgent.tools.map((t) => (
                    <span
                      key={t}
                      style={{
                        fontFamily: "'JetBrains Mono', monospace",
                        fontSize: 10.5,
                        color: "var(--blue-primary)",
                        background: "rgba(37, 99, 235, 0.10)",
                        padding: "2px 6px",
                        borderRadius: 4,
                        border: "1px solid var(--border)",
                      }}
                    >
                      {t}
                    </span>
                  ))
                ) : (
                  <span style={{ color: "var(--text-muted)", fontStyle: "italic" }}>Pure cognitive reasoning (no external tools)</span>
                )}
              </div>
            </div>

            {(inspectedAgent.inputs || inspectedAgent.outputs) && (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, paddingTop: 8, borderTop: "1px solid var(--border-soft)" }}>
                <div>
                  <span style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", display: "block", marginBottom: 2 }}>
                    Inputs
                  </span>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--text-primary)" }}>
                    {inspectedAgent.inputs?.length ? inspectedAgent.inputs.join(", ") : "upstream"}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: 10, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase", display: "block", marginBottom: 2 }}>
                    Outputs
                  </span>
                  <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11, color: "var(--text-primary)" }}>
                    {inspectedAgent.outputs?.length ? inspectedAgent.outputs.join(", ") : "state"}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
