import EvolutionHistoryTable from "@/components/evaluation/EvolutionHistoryTable";

export default function HistoryPage() {
  return (
    <div className="max-w-6xl mx-auto px-4 py-12 slide-up">
      <div className="mb-10">
        <h1 className="text-3xl md:text-4xl font-bold mb-4 flex items-center gap-3">
          <span className="text-accent-secondary">
            <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20v-6M6 20V10M18 20V4"/></svg>
          </span>
          Evolution Memory <span className="text-text-secondary font-light">History</span>
        </h1>
        <p className="text-text-secondary max-w-3xl">
          View the persistent record of all executed architectures, their evaluation metrics, 
          and the reflection recommendations generated to improve them. This memory store 
          is used by the Meta Controller to retrieve similar past experiences.
        </p>
      </div>

      <EvolutionHistoryTable />
      
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-card p-6 border-accent-primary/20">
          <h3 className="text-lg font-bold mb-2">Memory Retriever Subsystem</h3>
          <p className="text-sm text-text-secondary">
            The retrieval engine searches this database based on task characteristics (type, complexity).
            When you submit a new task, it automatically retrieves the highest-rated architectures from
            similar past tasks to inform the new synthesis, avoiding previous mistakes.
          </p>
        </div>
        <div className="glass-card p-6 border-accent-emerald/20">
          <h3 className="text-lg font-bold mb-2">Run Iterations</h3>
          <p className="text-sm text-text-secondary">
            Clicking <span className="font-semibold text-text-primary">Evolve Architecture</span> on the Run page increments 
            the Run Number for a task. You can observe the success rating improving over successive iterations as
            structural recommendations are applied to the generated agent network.
          </p>
        </div>
      </div>
    </div>
  );
}
