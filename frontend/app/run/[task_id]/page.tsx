"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { 
  getTaskEvolutionHistory, 
  evaluateExecution, 
  runExecution,
  api
} from "@/lib/api";
import ArchitectureGraph from "@/components/architecture/ArchitectureGraph";
import ExecutionTimeline from "@/components/execution/ExecutionTimeline";
import MetricsPanel from "@/components/evaluation/MetricsPanel";
import ReflectionPanel from "@/components/evaluation/ReflectionPanel";

export default function RunPage({ params }: { params: { task_id: string } }) {
  const taskId = params.task_id;
  const searchParams = useSearchParams();
  const execParam = searchParams.get("exec");
  
  const [taskData, setTaskData] = useState<any>(null);
  const [execData, setExecData] = useState<any>(null);
  const [evalData, setEvalData] = useState<any>(null);
  
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [reRunning, setReRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const router = useRouter();

  // Load state
  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        // 1. Get task data
        const tResp = await api.get(`/tasks/${taskId}`);
        setTaskData(tResp.data);

        // 2. Get execution data
        if (execParam) {
          try {
            const eResp = await api.get(`/execution/${execParam}`);
            setExecData(eResp.data);
            
            // 3. Try to get evaluation if it exists for this task
            if (tResp.data.latest_evaluation_id) {
              const evResp = await api.get(`/evaluation/${tResp.data.latest_evaluation_id}`);
              setEvalData(evResp.data);
            }
          } catch (e) {
            console.error("Execution not found yet or error loading");
          }
        }
      } catch (err: any) {
        setError(err.message || "Failed to load run data");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [taskId, execParam]);

  const handleEvaluate = async () => {
    if (!execData) return;
    setEvaluating(true);
    try {
      const result = await evaluateExecution(execData.execution_id, taskId);
      setEvalData(result);
      
      // Update local task state
      setTaskData(prev => ({
        ...prev,
        latest_evaluation_id: result.evaluation_result.evaluation_id,
        status: "evaluated"
      }));
    } catch (err: any) {
      setError(err.message || "Evaluation failed");
    } finally {
      setEvaluating(false);
    }
  };

  const handleEvolveAndReRun = async () => {
    setReRunning(true);
    try {
      // In a real system, this would trigger MetaController with reflection context.
      // For the demo, we'll increment the run number and re-execute.
      const currentRun = execData?.run_number || 1;
      
      // Resubmit task (simulating evolution)
      const submitResp = await api.post("/tasks/submit", { 
        user_prompt: taskData.task_spec.user_prompt,
        run_number: currentRun + 1
      });
      
      // Run execution
      const execution = await runExecution(submitResp.data.task_id, currentRun + 1);
      
      // Navigate to new execution
      window.location.href = `/run/${submitResp.data.task_id}?exec=${execution.execution_id}`;
    } catch (err: any) {
      setError(err.message || "Evolution run failed");
      setReRunning(false);
    }
  };

  if (loading) {
    return <div className="p-12 flex justify-center"><span className="spinner w-8 h-8"></span></div>;
  }

  if (error || !taskData) {
    return <div className="p-8 text-accent-rose text-center bg-accent-rose/10 border border-accent-rose/20 rounded-lg max-w-2xl mx-auto mt-12">{error || "Task not found"}</div>;
  }

  const taskSpec = taskData.task_spec;
  const archSpec = taskData.architecture_spec;
  const runNumber = execData?.run_number || taskData.run_number || 1;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl md:text-3xl font-bold">Execution Run <span className="text-accent-primary">#{runNumber}</span></h1>
            <span className="badge badge-purple">{taskSpec.task_type.replace(/_/g, ' ')}</span>
            <span className="badge badge-info">{taskSpec.complexity} complexity</span>
          </div>
          <p className="text-text-secondary max-w-3xl truncate" title={taskSpec.user_prompt}>
            <span className="font-semibold text-text-primary">Prompt:</span> "{taskSpec.user_prompt}"
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className={`px-4 py-2 rounded-lg border flex items-center gap-2 text-sm font-bold ${
            evalData ? 'bg-accent-emerald/10 border-accent-emerald/30 text-accent-emerald' : 
            execData ? 'bg-accent-amber/10 border-accent-amber/30 text-accent-amber' : 
            'bg-accent-cyan/10 border-accent-cyan/30 text-accent-cyan pulse-glow'
          }`}>
            <div className={`w-2 h-2 rounded-full ${evalData ? 'bg-accent-emerald' : execData ? 'bg-accent-amber' : 'bg-accent-cyan'}`} />
            {evalData ? 'Evaluated & Stored' : execData ? 'Execution Completed' : 'Running...'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Architecture & Evaluation */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          
          <div className="glass-card p-5">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-accent-primary"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>
              Synthesized Architecture
            </h2>
            <p className="text-sm text-text-secondary mb-4 bg-bg-secondary p-3 rounded-lg border border-border">
              {archSpec.meta_reasoning}
            </p>
            <div className="h-[400px]">
              <ArchitectureGraph architecture={archSpec} />
            </div>
          </div>

          {evalData && (
            <div className="slide-up">
              <h2 className="text-xl font-bold mb-4 mt-4 text-[#e2e8f0] border-b border-border pb-2">Evaluation & Reflection</h2>
              <MetricsPanel metrics={evalData.evaluation_result.metrics} />
              
              <div className="mt-6">
                <ReflectionPanel reflection={evalData.reflection_result} />
              </div>
              
              <div className="mt-6 glass-card p-6 border-accent-primary/40 text-center flex flex-col items-center justify-center">
                <h3 className="text-lg font-bold mb-2">Evolve Architecture</h3>
                <p className="text-sm text-text-secondary mb-4 max-w-lg">
                  Apply the reflection recommendations to synthesize an improved architecture and re-run the task.
                </p>
                <button 
                  onClick={handleEvolveAndReRun} 
                  disabled={reRunning}
                  className="btn-primary flex items-center gap-2 px-8 py-3 text-lg"
                >
                  {reRunning ? (
                    <><span className="spinner"></span> Evolving...</>
                  ) : (
                    <>
                      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12A10 10 0 0 0 15 21.5M2 12A10 10 0 0 1 15 2.5"/><path d="M15 2.5V8h5.5M15 21.5V16h5.5"/></svg>
                      Apply Recommendations & Re-Run
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

        </div>

        {/* Right Column: Execution Log & Evaluation Action */}
        <div className="lg:col-span-1 flex flex-col gap-6">
          
          <div className="glass-card p-5 h-full flex flex-col max-h-[800px]">
            <div className="flex items-center justify-between mb-4 border-b border-border pb-2">
              <h2 className="text-lg font-bold flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-accent-cyan"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
                Agent Execution Log
              </h2>
            </div>
            
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar">
              {execData ? (
                <ExecutionTimeline logs={execData.agent_logs} />
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-text-muted">
                  <span className="spinner mb-4 w-8 h-8 border-accent-cyan"></span>
                  <p>Executing agent network...</p>
                </div>
              )}
            </div>
            
            {execData && !evalData && (
              <div className="pt-4 mt-4 border-t border-border">
                <button 
                  onClick={handleEvaluate}
                  disabled={evaluating}
                  className="w-full bg-accent-emerald hover:bg-accent-emerald/90 text-[#0a0e1a] font-bold py-3 px-4 rounded-lg transition-colors flex justify-center items-center gap-2"
                >
                  {evaluating ? (
                    <><span className="spinner border-[#0a0e1a] border-t-white"></span> Evaluating...</>
                  ) : (
                    <>Run Evaluation & Reflection</>
                  )}
                </button>
              </div>
            )}
          </div>
          
        </div>
      </div>
    </div>
  );
}
