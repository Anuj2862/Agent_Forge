"use client";

import { useMemo, useState } from "react";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { ArchitectureSpec, AgentConfig } from "@/lib/api";

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

  const { nodes, edges } = useMemo(() => {
    const isParallel = architecture.topology === "parallel";

    const nodes = architecture.agents.map((agent: AgentConfig, index: number) => {
      const x = isParallel ? (index % 3) * 260 : index * 260;
      const y = isParallel ? Math.floor(index / 3) * 160 + 40 : 60;

      const status = agentStatuses[agent.agent_id] || "waiting";
      const isEvolved = evolvedAgentIds.includes(agent.agent_id);

      const statusBorderColor =
        status === "active"
          ? "#38bdf8"
          : status === "completed"
          ? "#34d399"
          : status === "failed"
          ? "#f43f5e"
          : isEvolved
          ? "#10b981"
          : "#334155";

      const statusGlow =
        status === "active"
          ? "0 0 16px rgba(56, 189, 248, 0.4)"
          : isEvolved
          ? "0 0 16px rgba(16, 185, 129, 0.35)"
          : "0 4px 10px rgba(0, 0, 0, 0.4)";

      return {
        id: agent.agent_id,
        position: { x, y },
        data: {
          label: (
            <div
              className="flex flex-col gap-1 p-2 cursor-pointer transition-all"
              onClick={() => {
                setInspectedAgent(agent);
                if (onSelectAgent) onSelectAgent(agent);
              }}
            >
              {/* Header row: Status & Evolution Tag */}
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                  {agent.agent_id}
                </span>
                {isEvolved && (
                  <span className="text-[9px] font-bold uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 px-1.5 py-0.5 rounded-full">
                    ★ Evolved
                  </span>
                )}
              </div>

              {/* Agent Title & Role */}
              <div className="font-bold text-sm text-slate-100 leading-tight">
                {agent.name}
              </div>
              <div className="text-xs text-indigo-300 font-medium">
                {agent.role}
              </div>

              {/* Tools chips */}
              {agent.tools && agent.tools.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1.5">
                  {agent.tools.map((t: string) => (
                    <span
                      key={t}
                      className="text-[9px] font-mono bg-indigo-950/80 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-500/30"
                    >
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ),
        },
        style: {
          background: isEvolved
            ? "linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(15, 23, 42, 0.95) 100%)"
            : "rgba(15, 23, 42, 0.94)",
          border: `1.5px solid ${statusBorderColor}`,
          borderRadius: "10px",
          width: 210,
          boxShadow: statusGlow,
          transition: "all 0.2s ease",
        },
      };
    });

    const edges = (architecture.connections || []).map((conn: any, idx: number) => ({
      id: `e-${conn.source}-${conn.target}-${idx}`,
      source: conn.source,
      target: conn.target,
      animated: true,
      style: { stroke: "#6366f1", strokeWidth: 2 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: "#6366f1",
      },
    }));

    return { nodes, edges };
  }, [architecture, agentStatuses, evolvedAgentIds, onSelectAgent]);

  return (
    <div className="relative w-full h-full rounded-xl overflow-hidden border border-slate-800" style={{ minHeight: "360px", background: "#070b14" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#1e293b" gap={18} size={1} />
        <Controls />
      </ReactFlow>

      {/* Agent Inspector Modal Drawer */}
      {inspectedAgent && (
        <div
          className="absolute top-3 right-3 bottom-3 w-80 rounded-lg p-4 text-xs overflow-y-auto z-20"
          style={{
            background: "rgba(15, 23, 42, 0.95)",
            backdropFilter: "blur(12px)",
            border: "1px solid rgba(99, 102, 241, 0.35)",
            boxShadow: "0 10px 25px rgba(0,0,0,0.6)",
          }}
        >
          <div className="flex items-start justify-between gap-2 pb-2 border-b border-slate-700">
            <div>
              <span className="text-[10px] uppercase font-mono text-indigo-400">
                Agent Inspector
              </span>
              <h4 className="text-sm font-bold text-slate-100">{inspectedAgent.name}</h4>
              <p className="text-xs text-indigo-300">{inspectedAgent.role}</p>
            </div>
            <button
              onClick={() => setInspectedAgent(null)}
              className="text-slate-400 hover:text-slate-200 text-sm font-bold p-1"
            >
              ✕
            </button>
          </div>

          <div className="flex flex-col gap-3 mt-3">
            <div>
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Objective
              </span>
              <p className="text-slate-300 leading-relaxed bg-slate-900/60 p-2 rounded border border-slate-800">
                {inspectedAgent.objective || "Standard task execution"}
              </p>
            </div>

            {inspectedAgent.system_prompt && (
              <div>
                <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  System Prompt
                </span>
                <p className="text-slate-400 leading-relaxed bg-slate-900/60 p-2 rounded border border-slate-800 italic max-h-32 overflow-y-auto">
                  "{inspectedAgent.system_prompt}"
                </p>
              </div>
            )}

            <div>
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                Assigned Tools ({inspectedAgent.tools?.length || 0})
              </span>
              <div className="flex flex-wrap gap-1">
                {inspectedAgent.tools && inspectedAgent.tools.length > 0 ? (
                  inspectedAgent.tools.map((t) => (
                    <span
                      key={t}
                      className="text-[10px] font-mono bg-indigo-500/15 text-indigo-300 px-2 py-0.5 rounded border border-indigo-500/30"
                    >
                      {t}
                    </span>
                  ))
                ) : (
                  <span className="text-slate-500 italic">No external tools (Pure Cognitive Reasoning)</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
