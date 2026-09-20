"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { submitTask, runExecution } from "@/lib/api";

export default function TaskSubmitForm() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [statusText, setStatusText] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setLoading(true);
    setStatusText("Analyzing task & synthesizing architecture...");

    try {
      // 1. Submit task
      const { task_id, architecture_spec } = await submitTask(prompt);
      
      setStatusText(`Synthesized ${architecture_spec.agents.length}-agent ${architecture_spec.topology} architecture. Starting execution...`);

      // 2. Start execution
      const execution = await runExecution(task_id, 1);
      
      // 3. Navigate to run page
      router.push(`/run/${task_id}?exec=${execution.execution_id}`);
    } catch (error) {
      console.error(error);
      setStatusText("Error submitting task. Check console.");
      setLoading(false);
    }
  };

  return (
    <div className="glass-card p-6 md:p-8 max-w-3xl mx-auto w-full slide-up">
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">Submit New Task</h2>
        <p className="text-text-secondary">
          Describe the problem. The Meta Controller will dynamically synthesize a multi-agent architecture to solve it.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="e.g. Research the impact of Generative AI on cybersecurity and produce a verified report..."
            className="w-full bg-[#0f1628] border border-border rounded-lg p-4 text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-primary focus:ring-1 focus:ring-accent-primary transition-all resize-y min-h-[120px]"
            disabled={loading}
          />
        </div>

        <div className="flex items-center justify-between mt-2">
          <div className="text-sm text-text-secondary h-6">
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }}></span>
                {statusText}
              </span>
            ) : (
              "Press Enter to submit or click Forge."
            )}
          </div>
          
          <button 
            type="submit" 
            className="btn-primary flex items-center gap-2 px-6"
            disabled={loading || !prompt.trim()}
          >
            {loading ? "Forging..." : "Forge Architecture"}
          </button>
        </div>
      </form>
    </div>
  );
}
