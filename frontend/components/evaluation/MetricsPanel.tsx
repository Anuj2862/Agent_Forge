"use client";

import { EvaluationMetrics } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface Props {
  metrics: EvaluationMetrics;
}

export default function MetricsPanel({ metrics }: Props) {
  const data = [
    { name: "Task Success", value: Math.round(metrics.task_success * 100), color: metrics.task_success >= 0.8 ? "#10b981" : metrics.task_success >= 0.6 ? "#f59e0b" : "#f43f5e" },
    { name: "Quality", value: Math.round(metrics.quality * 100), color: metrics.quality >= 0.8 ? "#10b981" : metrics.quality >= 0.6 ? "#f59e0b" : "#f43f5e" },
    { name: "Completeness", value: Math.round(metrics.completeness * 100), color: metrics.completeness >= 0.8 ? "#10b981" : metrics.completeness >= 0.6 ? "#f59e0b" : "#f43f5e" },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div className="glass-card p-5">
        <h3 className="text-lg font-bold mb-4 border-b border-border pb-2">Quantitative Metrics</h3>
        <div className="h-[200px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <XAxis type="number" domain={[0, 100]} hide />
              <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: "#94a3b8", fontSize: 12 }} width={90} />
              <Tooltip 
                cursor={{ fill: "rgba(30, 45, 69, 0.5)" }} 
                contentStyle={{ background: "#131929", border: "1px solid #1e2d45", borderRadius: "8px", color: "#e2e8f0" }}
                formatter={(value: number) => [`${value}%`, "Score"]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} barSize={24}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      
      <div className="glass-card p-5 flex flex-col gap-4">
        <h3 className="text-lg font-bold mb-1 border-b border-border pb-2">Resource Utilization</h3>
        
        <div className="flex items-center justify-between p-3 bg-bg-secondary rounded-lg border border-border">
          <div className="flex flex-col">
            <span className="text-xs text-text-secondary uppercase font-bold tracking-wider">Execution Time</span>
            <span className="text-2xl font-mono mt-1">{metrics.execution_time_seconds.toFixed(1)}s</span>
          </div>
          <div className="w-10 h-10 rounded-full bg-accent-cyan/20 flex items-center justify-center border border-accent-cyan/30">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4">
          <div className="flex items-center justify-between p-3 bg-bg-secondary rounded-lg border border-border">
            <div className="flex flex-col">
              <span className="text-xs text-text-secondary uppercase font-bold tracking-wider">Agents</span>
              <span className="text-2xl font-mono mt-1">{metrics.agent_count}</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between p-3 bg-bg-secondary rounded-lg border border-border">
            <div className="flex flex-col">
              <span className="text-xs text-text-secondary uppercase font-bold tracking-wider">Tool Calls</span>
              <span className="text-2xl font-mono mt-1">{metrics.tool_call_count}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
