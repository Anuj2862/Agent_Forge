"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getMemoryHistory, MemoryRecord } from "@/lib/api";

export default function EvolutionHistoryTable() {
  const [records, setRecords] = useState<MemoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMemoryHistory(1, 20).then((data) => {
      setRecords(data.records);
      setLoading(false);
    }).catch(console.error);
  }, []);

  if (loading) {
    return <div className="p-8 text-center text-text-muted flex justify-center"><span className="spinner"></span></div>;
  }

  if (records.length === 0) {
    return (
      <div className="glass-card p-12 text-center text-text-muted border-dashed">
        <p>No evolutionary history available yet.</p>
        <p className="text-sm mt-2">Submit tasks to generate and evolve architectures.</p>
      </div>
    );
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-bg-secondary border-b border-border text-text-secondary">
            <tr>
              <th className="p-4 font-semibold uppercase tracking-wider text-xs">Task Type & ID</th>
              <th className="p-4 font-semibold uppercase tracking-wider text-xs">Architecture</th>
              <th className="p-4 font-semibold uppercase tracking-wider text-xs text-center">Run</th>
              <th className="p-4 font-semibold uppercase tracking-wider text-xs text-center">Success</th>
              <th className="p-4 font-semibold uppercase tracking-wider text-xs">Top Recommendation</th>
              <th className="p-4 font-semibold uppercase tracking-wider text-xs text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/50">
            {records.map((record) => (
              <tr key={record.record_id} className="hover:bg-bg-card-hover transition-colors">
                <td className="p-4">
                  <div className="font-medium text-[#e2e8f0]">{record.task_type}</div>
                  <div className="text-xs text-text-muted font-mono mt-1">{record.task_spec.task_id.slice(0, 10)}...</div>
                </td>
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <span className="badge badge-purple">{record.topology}</span>
                    <span className="text-text-secondary text-xs">{record.agent_count} agents</span>
                  </div>
                </td>
                <td className="p-4 text-center">
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold ${record.run_number > 1 ? 'bg-accent-emerald/20 text-accent-emerald' : 'bg-bg-secondary text-text-secondary border border-border'}`}>
                    {record.run_number}
                  </span>
                </td>
                <td className="p-4 text-center">
                  <span className={`font-mono font-bold ${record.success_rating >= 0.8 ? 'text-accent-emerald' : record.success_rating >= 0.6 ? 'text-accent-amber' : 'text-accent-rose'}`}>
                    {(record.success_rating * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="p-4">
                  <div className="text-xs text-text-secondary truncate max-w-[250px]">
                    {record.recommendation_summary || "None (Optimal)"}
                  </div>
                </td>
                <td className="p-4 text-right">
                  <Link href={`/run/${record.task_spec.task_id}?exec=${record.evaluation_result.evaluation_id.replace('eval', 'exec')}`} className="text-accent-primary hover:text-accent-cyan text-sm font-semibold transition-colors">
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
