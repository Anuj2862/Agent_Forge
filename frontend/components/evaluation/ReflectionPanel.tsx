"use client";

import { ReflectionResult } from "@/lib/api";

interface Props {
  reflection: ReflectionResult;
}

export default function ReflectionPanel({ reflection }: Props) {
  return (
    <div className="flex flex-col gap-6">
      <div className="glass-card p-5 border-accent-secondary/40 relative overflow-hidden">
        <div className="absolute top-0 right-0 p-4 opacity-10">
          <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        </div>
        <h3 className="text-lg font-bold mb-2 text-accent-secondary flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
          Reflection Summary
        </h3>
        <p className="text-text-primary leading-relaxed">{reflection.reflection_summary}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 className="text-md font-bold mb-3 flex items-center gap-2 text-text-secondary border-b border-border pb-2">
            Identified Issues
            <span className="badge badge-error ml-auto">{reflection.identified_issues.length}</span>
          </h3>
          {reflection.identified_issues.length === 0 ? (
            <p className="text-sm text-text-muted italic p-4 text-center bg-bg-secondary rounded-lg border border-border">No critical issues detected.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {reflection.identified_issues.map((issue, idx) => (
                <li key={idx} className="bg-bg-secondary border border-border rounded-lg p-3 flex gap-3 items-start">
                  <div className="mt-0.5 text-accent-rose">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                  </div>
                  <div>
                    <div className="text-xs font-mono text-accent-rose/80 mb-1">{issue.category.replace(/_/g, ' ')}</div>
                    <p className="text-sm text-text-primary/90">{issue.description}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <h3 className="text-md font-bold mb-3 flex items-center gap-2 text-text-secondary border-b border-border pb-2">
            Evolution Recommendations
            <span className="badge badge-info ml-auto">{reflection.recommendations.length}</span>
          </h3>
          {reflection.recommendations.length === 0 ? (
            <p className="text-sm text-text-muted italic p-4 text-center bg-bg-secondary rounded-lg border border-border">No recommendations.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {reflection.recommendations.map((rec, idx) => (
                <li key={idx} className="bg-bg-secondary border border-border rounded-lg p-3 flex gap-3 items-start relative overflow-hidden group hover:border-accent-cyan/50 transition-colors">
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-accent-cyan/80"></div>
                  <div className="mt-0.5 text-accent-cyan pl-1">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="text-xs font-mono text-accent-cyan/90 font-bold">{rec.action}</div>
                      <span className={`text-[9px] px-1.5 py-0.5 rounded uppercase ${rec.priority === 'high' ? 'bg-accent-rose/20 text-accent-rose' : 'bg-text-muted/30 text-text-secondary'}`}>
                        {rec.priority}
                      </span>
                    </div>
                    <p className="text-sm text-text-primary/90">{rec.details.rationale || Object.values(rec.details)[0]}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
