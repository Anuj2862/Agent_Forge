"use client";

import { useMemo } from "react";
import ReactFlow, { Background, Controls, MarkerType } from "reactflow";
import "reactflow/dist/style.css";
import { ArchitectureSpec } from "@/lib/api";

interface Props {
  architecture: ArchitectureSpec;
}

export default function ArchitectureGraph({ architecture }: Props) {
  const { nodes, edges } = useMemo(() => {
    const isParallel = architecture.topology === "parallel";
    
    const nodes = architecture.agents.map((agent, index) => {
      // Auto-layout nodes in a line for pipeline, or side-by-side for parallel
      const x = isParallel ? (index % 3) * 250 : index * 250;
      const y = isParallel ? Math.floor(index / 3) * 150 : 50;
      
      return {
        id: agent.agent_id,
        position: { x, y },
        data: { 
          label: (
            <div className="flex flex-col gap-1 p-1">
              <div className="font-bold text-sm" style={{ color: "#e2e8f0" }}>{agent.name}</div>
              <div className="text-xs" style={{ color: "#94a3b8" }}>{agent.role}</div>
              {agent.tools.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1 justify-center">
                  {agent.tools.map(t => (
                    <span key={t} className="text-[9px] bg-accent-primary/20 text-accent-primary px-1.5 py-0.5 rounded-full border border-accent-primary/30">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ) 
        },
        style: {
          background: "rgba(19, 25, 41, 0.9)",
          border: "1px solid #1e2d45",
          borderRadius: "8px",
          padding: "8px",
          width: 180,
          boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
        },
      };
    });

    const edges = architecture.connections.map((conn, idx) => ({
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
  }, [architecture]);

  return (
    <div className="w-full h-full rounded-xl overflow-hidden border border-border" style={{ minHeight: "350px", background: "#0a0e1a" }}>
      <ReactFlow 
        nodes={nodes} 
        edges={edges} 
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#1e2d45" gap={16} />
        <Controls />
      </ReactFlow>
    </div>
  );
}
