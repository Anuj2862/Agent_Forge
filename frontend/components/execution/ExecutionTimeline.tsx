"use client";

import { AgentLog } from "@/lib/api";

interface Props {
  logs: AgentLog[];
}

export default function ExecutionTimeline({ logs }: Props) {
  return (
    <div className="flex flex-col gap-4">
      {logs.map((log, idx) => {
        const isSuccess = log.status === "success";
        return (
          <div key={`${log.agent_id}-${idx}`} className="relative pl-6 pb-2 border-l-2 border-border last:border-0 last:pb-0">
            <div 
              className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full border-2 border-bg-primary ${isSuccess ? 'bg-accent-emerald' : 'bg-accent-amber'}`}
            />
            <div className="glass-card p-4 -mt-1.5 ml-2">
              <div className="flex items-start justify-between mb-2 border-b border-border/50 pb-2">
                <div>
                  <h4 className="font-bold text-[#e2e8f0] flex items-center gap-2">
                    {log.agent_name}
                    <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider ${isSuccess ? 'bg-accent-emerald/20 text-accent-emerald border border-accent-emerald/30' : 'bg-accent-amber/20 text-accent-amber border border-accent-amber/30'}`}>
                      {log.status}
                    </span>
                  </h4>
                  <p className="text-xs text-text-secondary mt-0.5">{log.role}</p>
                </div>
                <div className="text-xs font-mono bg-bg-primary px-2 py-1 rounded border border-border">
                  {log.execution_time_seconds}s
                </div>
              </div>
              
              <div className="text-sm text-text-primary/90 mt-3 whitespace-pre-wrap leading-relaxed">
                {log.output_preview}
              </div>
              
              {log.tool_calls.length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {log.tool_calls.map((tc, tIdx) => (
                    <div key={tIdx} className="flex items-center gap-1.5 text-xs bg-bg-secondary px-2 py-1 rounded-md border border-border">
                      <span className="text-accent-primary opacity-80">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
                      </span>
                      {tc.tool} <span className="text-text-muted">({tc.latency_ms}ms)</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
