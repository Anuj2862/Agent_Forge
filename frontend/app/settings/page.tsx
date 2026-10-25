"use client";

import { useEffect, useState } from "react";
import { getHealth, API_BASE_URL } from "@/lib/api";
import { applyTheme, useTheme } from "@/lib/theme";

interface ExtendedHealth {
  status: string;
  version?: string;
  app?: string;
  environment?: string;
  database?: { status: string; type: string; url: string | null };
  model_provider?: { status: string; provider: string; live_key_configured: boolean };
  tools?: { status: string; registered_count: number; available: string[] };
  error?: string;
}

export default function SettingsPage() {
  const [health, setHealth] = useState<ExtendedHealth | null>(null);
  const [checkingHealth, setCheckingHealth] = useState<boolean>(true);
  const currentTheme = useTheme();
  const [selectedProvider, setSelectedProvider] = useState<string>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("agentforge_prefs");
        if (stored) return JSON.parse(stored).selectedProvider || "gemini";
      } catch { /* ignored */ }
    }
    return "gemini";
  });
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("agentforge_prefs");
        if (stored) return JSON.parse(stored).selectedModel || "gemini-2.5-flash";
      } catch { /* ignored */ }
    }
    return "gemini-2.5-flash";
  });
  const [maxCycles, setMaxCycles] = useState<number>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("agentforge_prefs");
        if (stored && typeof JSON.parse(stored).maxCycles === "number") {
          return JSON.parse(stored).maxCycles;
        }
      } catch { /* ignored */ }
    }
    return 3;
  });
  const [qualityThreshold, setQualityThreshold] = useState<number>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("agentforge_prefs");
        if (stored && typeof JSON.parse(stored).qualityThreshold === "number") {
          return JSON.parse(stored).qualityThreshold;
        }
      } catch { /* ignored */ }
    }
    return 0.8;
  });
  const [autoEvolve, setAutoEvolve] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      try {
        const stored = localStorage.getItem("agentforge_prefs");
        if (stored && JSON.parse(stored).autoEvolve !== undefined) {
          return JSON.parse(stored).autoEvolve;
        }
      } catch { /* ignored */ }
    }
    return true;
  });
  const [savedBanner, setSavedBanner] = useState<boolean>(false);

  useEffect(() => {
    async function checkBackend() {
      try {
        setCheckingHealth(true);
        const data = await getHealth();
        setHealth(data as ExtendedHealth);
      } catch {
        setHealth({ status: "offline", error: "Could not connect to FastAPI server at " + API_BASE_URL });
      } finally {
        setCheckingHealth(false);
      }
    }
    checkBackend();
  }, []);

  const handleSave = () => {
    if (typeof window !== "undefined") {
      try {
        localStorage.setItem(
          "agentforge_prefs",
          JSON.stringify({
            selectedProvider,
            selectedModel,
            maxCycles,
            qualityThreshold,
            autoEvolve,
          })
        );
      } catch (e) {
        console.warn("Could not save to localStorage", e);
      }
    }
    setSavedBanner(true);
    setTimeout(() => setSavedBanner(false), 3500);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Header Banner */}
      <div
        className="card fade-up"
        style={{
          padding: "20px 24px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <span style={{ fontSize: 20 }}>⚙️</span>
            <h1 style={{ fontSize: 18, fontWeight: 800 }}>Platform Settings &amp; Diagnostics</h1>
            <span className="badge badge-indigo">Runtime Config</span>
          </div>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
            Environment telemetry, FastAPI database connection, registered tool policies, and evolution hyperparameters
          </p>
        </div>

        <button onClick={handleSave} className="btn btn-primary btn-sm">
          Save Preferences
        </button>
      </div>

      {savedBanner && (
        <div
          className="fade-up"
          style={{
            padding: "12px 18px",
            borderRadius: 8,
            background: "rgba(16, 185, 129, 0.12)",
            border: "1px solid rgba(16, 185, 129, 0.3)",
            color: "#34d399",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          ✓ Preferences saved to local storage. Backend keys remain securely configured in backend `.env`.
        </div>
      )}

      {/* Backend API Diagnostics Card */}
      <div className="card fade-up">
        <div className="card-header">
          <div className="card-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
              <line x1="6" y1="6" x2="6.01" y2="6" />
              <line x1="6" y1="18" x2="6.01" y2="18" />
            </svg>
            FastAPI Server Telemetry
          </div>
          {checkingHealth ? (
            <span className="badge badge-slate">Checking Telemetry…</span>
          ) : health?.status === "healthy" ? (
            <span className="badge badge-emerald">Operational</span>
          ) : (
            <span className="badge badge-rose">Server Offline</span>
          )}
        </div>

        <div style={{ padding: "20px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 16 }}>
          <div style={{ background: "var(--bg-card-subtle)", padding: "14px", borderRadius: 8, border: "1px solid var(--border-soft)" }}>
            <span className="form-label" style={{ display: "block", marginBottom: 4 }}>API Base URL</span>
            <code style={{ fontSize: 13, color: "#818cf8" }}>{API_BASE_URL}</code>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              Next.js client proxy targeting backend
            </div>
          </div>

          <div style={{ background: "var(--bg-card-subtle)", padding: "14px", borderRadius: 8, border: "1px solid var(--border-soft)" }}>
            <span className="form-label" style={{ display: "block", marginBottom: 4 }}>Database Engine</span>
            <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>
              SQLite + SQLAlchemy Async Engine
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              Persistent storage for tasks, DAGs, and runs
            </div>
          </div>

          <div style={{ background: "var(--bg-card-subtle)", padding: "14px", borderRadius: 8, border: "1px solid var(--border-soft)" }}>
            <span className="form-label" style={{ display: "block", marginBottom: 4 }}>Execution Tools Status</span>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#34d399" }}>
              3 Tools Registered &amp; Sandboxed
            </div>
            <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
              <code>python_tool</code> (isolated), <code>web_search</code>, <code>document_retriever</code>
            </div>
          </div>
        </div>
      </div>

      {/* Evolution Hyperparameters Card */}
      <div className="card fade-up">
        <div className="card-header">
          <div className="card-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            Evolution Hyperparameters &amp; Thresholds
          </div>
          <span className="badge badge-indigo">Policy v1.0.0</span>
        </div>

        <div style={{ padding: "20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div className="form-group">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <label className="form-label">Max Evolution Cycles</label>
              <span style={{ fontSize: 12, fontWeight: 700, fontFamily: "var(--font-mono, monospace)", color: "#818cf8" }}>
                {maxCycles} cycles
              </span>
            </div>
            <input
              type="range"
              min="1"
              max="5"
              value={maxCycles}
              onChange={(e) => setMaxCycles(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#6366f1", cursor: "pointer" }}
            />
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Maximum mutation iterations before stabilizing architecture
            </span>
          </div>

          <div className="form-group">
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <label className="form-label">Quality Target Threshold</label>
              <span style={{ fontSize: 12, fontWeight: 700, fontFamily: "var(--font-mono, monospace)", color: "#34d399" }}>
                {(qualityThreshold * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0.6"
              max="0.95"
              step="0.05"
              value={qualityThreshold}
              onChange={(e) => setQualityThreshold(Number(e.target.value))}
              style={{ width: "100%", accentColor: "#10b981", cursor: "pointer" }}
            />
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
              Minimum overall evaluation score required for acceptance
            </span>
          </div>
        </div>

        <div style={{ padding: "14px 20px", background: "var(--bg-card-subtle)", borderTop: "1px solid var(--border-soft)", display: "flex", alignItems: "center", gap: 10 }}>
          <input
            type="checkbox"
            id="auto-evolve"
            checked={autoEvolve}
            onChange={(e) => setAutoEvolve(e.target.checked)}
            style={{ width: 16, height: 16, accentColor: "#6366f1", cursor: "pointer" }}
          />
          <label htmlFor="auto-evolve" style={{ fontSize: 13, color: "var(--text-primary)", cursor: "pointer" }}>
            Enable automated mutation recommendations when reflection diagnoses verification or completeness gaps
          </label>
        </div>
      </div>

      {/* Interface & Theme Configuration Card */}
      <div className="card fade-up">
        <div className="card-header">
          <div className="card-title">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
            Interface Theme &amp; Visual Mode
          </div>
          <span className="badge badge-cyan">Visual System</span>
        </div>

        <div style={{ padding: "20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div
            onClick={() => {
              applyTheme("dark");
            }}
            style={{
              padding: "16px",
              borderRadius: 8,
              background: "rgba(5, 11, 22, 0.8)",
              border: currentTheme === "dark" ? "2px solid #38bdf8" : "2px solid var(--border)",
              boxShadow: currentTheme === "dark" ? "0 0 12px rgba(56, 189, 248, 0.25)" : "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              transition: "all 0.15s ease",
            }}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#EAF2FF" }}>
                Dark Mode {currentTheme === "dark" && <span style={{ fontSize: 11, color: "#38bdf8", marginLeft: 6 }}>● Active</span>}
              </div>
              <div style={{ fontSize: 11, color: "#9BAEC8", marginTop: 2 }}>High-contrast midnight cyber aesthetic</div>
            </div>
            <span style={{ fontSize: 18 }}>🌙</span>
          </div>

          <div
            onClick={() => {
              applyTheme("light");
            }}
            style={{
              padding: "16px",
              borderRadius: 8,
              background: "#FFFFFF",
              border: currentTheme === "light" ? "2px solid #2563EB" : "2px solid var(--border)",
              boxShadow: currentTheme === "light" ? "0 0 12px rgba(37, 99, 235, 0.2)" : "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              transition: "all 0.15s ease",
            }}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: "#0F172A" }}>
                Light Mode {currentTheme === "light" && <span style={{ fontSize: 11, color: "#2563EB", marginLeft: 6 }}>● Active</span>}
              </div>
              <div style={{ fontSize: 11, color: "#64748B", marginTop: 2 }}>Crisp, high-contrast clean day aesthetic</div>
            </div>
            <span style={{ fontSize: 18 }}>☀️</span>
          </div>
        </div>
      </div>

      {/* Model Provider Configuration Card */}
      <div className="card fade-up">
        <div className="card-header">
          <div className="card-title">
            LLM Provider &amp; Model Selection
          </div>
          <span className="badge badge-slate">Inference Engine</span>
        </div>

        <div style={{ padding: "20px", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          <div className="form-group">
            <label className="form-label" htmlFor="provider-select">Primary Provider</label>
            <select
              id="provider-select"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="form-control"
            >
              <option value="gemini">Google Gemini (Recommended)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic Claude</option>
              <option value="ollama">Local Ollama</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="model-select">Target Model</label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="form-control"
            >
              <option value="gemini-2.5-flash">Gemini 2.5 Flash (Ultra Fast)</option>
              <option value="gemini-2.5-pro">Gemini 2.5 Pro (Deep Reasoning)</option>
              <option value="gpt-4o">GPT-4o</option>
              <option value="claude-3-5-sonnet">Claude 3.5 Sonnet</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
