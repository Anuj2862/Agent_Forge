import TaskSubmitForm from "@/components/TaskSubmitForm";
import Link from "next/link";

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-12">
      <div className="text-center mb-16 slide-up">
        <h1 className="text-5xl md:text-6xl font-extrabold mb-6 tracking-tight">
          Evolutionary <span className="gradient-text">Multi-Agent</span> Architecture
        </h1>
        <p className="text-lg md:text-xl text-text-secondary max-w-3xl mx-auto leading-relaxed">
          Agent Forge dynamically synthesizes specialized agent teams for your tasks.
          It evaluates execution, reflects on failures, and evolves the graph topology 
          over time to maximize task success.
        </p>
      </div>

      <div className="flex justify-center mb-16 slide-up" style={{ animationDelay: "0.1s" }}>
        <TaskSubmitForm />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 slide-up" style={{ animationDelay: "0.2s" }}>
        <div className="glass-card p-6 border-t-2 border-t-accent-primary">
          <div className="w-12 h-12 rounded-xl bg-accent-primary/20 flex items-center justify-center mb-4 text-accent-primary border border-accent-primary/30">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/><path d="M2 12h20"/></svg>
          </div>
          <h3 className="text-lg font-bold mb-2">Dynamic Synthesis</h3>
          <p className="text-sm text-text-secondary">
            Meta Controller converts natural language into structured subtasks and synthesizes 
            specialized agents and connections on the fly.
          </p>
        </div>

        <div className="glass-card p-6 border-t-2 border-t-accent-cyan">
          <div className="w-12 h-12 rounded-xl bg-accent-cyan/20 flex items-center justify-center mb-4 text-accent-cyan border border-accent-cyan/30">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
          </div>
          <h3 className="text-lg font-bold mb-2">Graph Execution</h3>
          <p className="text-sm text-text-secondary">
            Executes the dynamically generated architecture using LangGraph, handling state 
            passing, tool invocation, and parallel processing.
          </p>
        </div>

        <div className="glass-card p-6 border-t-2 border-t-accent-emerald">
          <div className="w-12 h-12 rounded-xl bg-accent-emerald/20 flex items-center justify-center mb-4 text-accent-emerald border border-accent-emerald/30">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <h3 className="text-lg font-bold mb-2">Evolution Memory</h3>
          <p className="text-sm text-text-secondary">
            Evaluates outputs, diagnoses architectural gaps, and persists experience to 
            improve future synthesis for similar task profiles.
          </p>
        </div>
      </div>
    </div>
  );
}
