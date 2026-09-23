"use client";

import { useEffect, useState } from "react";
import { getHealth, API_BASE_URL } from "@/lib/api";

export default function SettingsPage() {
  const [health, setHealth] = useState<any>(null);
  const [checkingHealth, setCheckingHealth] = useState<boolean>(true);
  const [selectedProvider, setSelectedProvider] = useState<string>("gemini");
  const [selectedModel, setSelectedModel] = useState<string>("gemini-2.5-flash");
  const [maxCycles, setMaxCycles] = useState<number>(3);
  const [qualityThreshold, setQualityThreshold] = useState<number>(0.8);
  const [autoEvolve, setAutoEvolve] = useState<boolean>(true);
  const [savedBanner, setSavedBanner] = useState<boolean>(false);

  useEffect(() => {
    async function checkBackend() {
      try {
        setCheckingHealth(true);
        const data = await getHealth();
        setHealth(data);
      } catch (err) {
        setHealth({ status: "offline", error: "Could not connect to FastAPI server" });
      } finally {
        setCheckingHealth(false);
      }
    }
    checkBackend();
  }, []);

  const handleSave = () => {
    setSavedBanner(true);
    setTimeout(() => setSavedBanner(false), 3000);
  };

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "24px 20px 80px" }}>
      {/* Header */}
      <div className="fade-up" style={{ marginBottom: 28 }}>
        <h1 style={{ fontSize: 20, fontWeight: 800, letterSpacing: "-0.02em" }}>
          Laboratory <span className="gradient-text">Settings</span>
        </h1>
        <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
          Manage your Agent Forge environment, LLM providers, and evolution hyperparameters
        </p>
      </div>

      {savedBanner && (
        <div
          className="fade-up"
          style={{
            padding: "12px 18px",
            marginBottom: 20,
            borderRadius: 8,
            background: "rgba(16,185,129,0.12)",
            border: "1px solid rgba(16,185,129,0.3)",
            color: "#34d399",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          ✓ Laboratory configuration updated successfully.
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {/* Backend Connection */}
        <section className="card fade-up" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14 }}>
            Backend API Connection
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr auto", gap: 16, alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>API Base URL:</div>
              <input
                type="text"
                readOnly
                value={API_BASE_URL}
                style={{
                  width: "100%",
                  background: "var(--bg-secondary)",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: "8px 12px",
                  fontSize: 13,
                  fontFamily: "monospace",
                  color: "#94a3b8",
                }}
              />
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: 10, alignSelf: "end", height: 38 }}>
              {checkingHealth ? (
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Checking…</span>
              ) : health?.status === "healthy" ? (
                <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#34d399", fontSize: 12, fontWeight: 600 }}>
                  <div className="status-dot live" />
                  FastAPI Server Operational ({health.version})
                </div>
              ) : (
                <div style={{ display: "flex", alignItems: "center", gap: 6, color: "#fb7185", fontSize: 12, fontWeight: 600 }}>
                  <div className="status-dot failed" />
                  Server Offline
                </div>
              )}
            </div>
          </div>
        </section>

        {/* LLM Provider Configuration */}
        <section className="card fade-up" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>
            LLM Provider &amp; Model Selection
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 18 }}>
            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
                Primary Provider:
              </label>
              <select
                value={selectedProvider}
                onChange={(e) => setSelectedProvider(e.target.value)}
                style={{
                  width: "100%",
                  background: "var(--bg-secondary)",
                  color: "#f1f5f9",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: "8px 12px",
                  fontSize: 13,
                }}
              >
                <option value="gemini">Google Gemini (Recommended)</option>
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic Claude</option>
                <option value="ollama">Local Ollama</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
                Default Model:
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                style={{
                  width: "100%",
                  background: "var(--bg-secondary)",
                  color: "#f1f5f9",
                  border: "1px solid var(--border)",
                  borderRadius: 6,
                  padding: "8px 12px",
                  fontSize: 13,
                }}
              >
                <option value="gemini-2.5-flash">Gemini 2.5 Flash (Ultra Fast)</option>
                <option value="gemini-2.5-pro">Gemini 2.5 Pro (Deep Reasoning)</option>
                <option value="gpt-4o">GPT-4o</option>
                <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
              </select>
            </div>
          </div>
        </section>

        {/* Evolution Hyperparameters */}
        <section className="card fade-up" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 16 }}>
            Autonomous Evolution Hyperparameters
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
                Max Evolution Cycles: {maxCycles}
              </label>
              <input
                type="range"
                min="1"
                max="5"
                value={maxCycles}
                onChange={(e) => setMaxCycles(Number(e.target.value))}
                style={{ width: "100%", cursor: "pointer" }}
              />
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                Maximum number of self-mutation cycles before stabilizing
              </div>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", marginBottom: 6 }}>
                Quality Target Threshold: {(qualityThreshold * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0.6"
                max="0.95"
                step="0.05"
                value={qualityThreshold}
                onChange={(e) => setQualityThreshold(Number(e.target.value))}
                style={{ width: "100%", cursor: "pointer" }}
              />
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                Minimum evaluation score required to halt evolution
              </div>
            </div>
          </div>

          <div style={{ marginTop: 18, paddingTop: 16, borderTop: "1px solid var(--border-soft)", display: "flex", alignItems: "center", gap: 10 }}>
            <input
              type="checkbox"
              id="auto-evolve"
              checked={autoEvolve}
              onChange={(e) => setAutoEvolve(e.target.checked)}
              style={{ width: 16, height: 16, cursor: "pointer" }}
            />
            <label htmlFor="auto-evolve" style={{ fontSize: 13, color: "#e2e8f0", cursor: "pointer" }}>
              Automatically suggest architecture mutations when reflection identifies factual vulnerabilities
            </label>
          </div>
        </section>

        {/* Team Architecture Roster */}
        <section className="card fade-up" style={{ padding: "24px" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, marginBottom: 14 }}>
            Agent Forge Project Architecture
          </h3>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <div style={{ padding: "12px 14px", borderRadius: 8, background: "var(--bg-secondary)", border: "1px solid var(--border-soft)" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#818cf8" }}>Member 1: Meta Controller</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                Task classification, topology selection, and dynamic prompt synthesis
              </div>
            </div>
            <div style={{ padding: "12px 14px", borderRadius: 8, background: "var(--bg-secondary)", border: "1px solid var(--border-soft)" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#38bdf8" }}>Member 2: Execution Engine</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                LangGraph multi-agent execution pipeline &amp; tool execution harnesses
              </div>
            </div>
            <div style={{ padding: "12px 14px", borderRadius: 8, background: "var(--bg-secondary)", border: "1px solid var(--border-soft)" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#c084fc" }}>Member 3: Evaluator &amp; Reflection</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                Multi-metric rubric, root-cause reflection, and graph mutation engine
              </div>
            </div>
            <div style={{ padding: "12px 14px", borderRadius: 8, background: "var(--bg-secondary)", border: "1px solid var(--border-soft)" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "#34d399" }}>Member 4: Evolutionary Memory &amp; UI</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                SQLite memory bank, FastAPI REST backend, and Next.js laboratory UI
              </div>
            </div>
          </div>
        </section>

        {/* Save button */}
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <button onClick={handleSave} className="btn btn-primary" style={{ padding: "10px 24px" }}>
            Save Preferences
          </button>
        </div>
      </div>
    </div>
  );
}
