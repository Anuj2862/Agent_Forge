import EvolutionHistoryTable from "@/components/evaluation/EvolutionHistoryTable";

export default function HistoryPage() {
  return (
    <div style={{ maxWidth: 1100, margin: "0 auto", padding: "48px 24px 80px" }}>

      {/* Header */}
      <div className="fade-up" style={{ marginBottom: 40 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <div
            style={{
              width: 38,
              height: 38,
              borderRadius: 10,
              background: "rgba(139,92,246,0.12)",
              border: "1px solid rgba(139,92,246,0.25)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#c4b5fd",
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 20v-6M6 20V10M18 20V4"/>
            </svg>
          </div>
          <div>
            <h1 style={{ fontSize: 20, fontWeight: 800, letterSpacing: "-0.02em" }}>
              Evolution Memory <span className="gradient-text">History</span>
            </h1>
            <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
              Persistent record of all executed architectures and their evaluation outcomes
            </p>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="fade-up delay-1">
        <EvolutionHistoryTable />
      </div>

      {/* Info cards */}
      <div
        className="fade-up delay-2"
        style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 32 }}
      >
        <div
          className="card"
          style={{ padding: "20px 22px" }}
        >
          <h3 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: "#818cf8" }}>Memory Retriever</h3>
          <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.65 }}>
            On every new task submission, the retrieval engine searches this database by task type and complexity to surface the highest-rated past architectures, preventing the Meta Controller from repeating known mistakes.
          </p>
        </div>
        <div
          className="card"
          style={{ padding: "20px 22px" }}
        >
          <h3 style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: "#34d399" }}>Run Iterations</h3>
          <p style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.65 }}>
            Each time you click <strong style={{ color: "var(--text-primary)" }}>Evolve & Re-Run</strong> on the run page, the system increments the run number and applies reflection recommendations to the newly generated architecture, visibly improving over time.
          </p>
        </div>
      </div>
    </div>
  );
}
