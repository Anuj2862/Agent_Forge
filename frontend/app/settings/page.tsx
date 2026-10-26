"use client";

import { useEffect, useState } from "react";
import AgentMascot from "@/components/mascot/AgentMascot";
import {
  getSettingsSummary,
  toggleTool,
  testRegisteredTool,
  updateModelMatrix,
  updateExecutionPolicies,
  getRuntimeHealth,
  ToolMetadata,
  ToolTestResponse,
  ModelMatrixConfig,
  ExecutionPolicyConfig,
  SystemHealthResponse,
  RoleModelConfig,
  API_BASE_URL,
} from "@/lib/api";

type ActiveTab = "tools" | "models" | "policies" | "health";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("tools");
  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  // Core settings state from backend
  const [tools, setTools] = useState<ToolMetadata[]>([]);
  const [, setModelMatrix] = useState<ModelMatrixConfig | null>(null);
  const [, setPolicies] = useState<ExecutionPolicyConfig | null>(null);
  const [health, setHealth] = useState<SystemHealthResponse | null>(null);

  // Tool testing & inspection state
  const [testingTool, setTestingTool] = useState<string | null>(null);
  const [toolTestResults, setToolTestResults] = useState<Record<string, ToolTestResponse>>({});
  const [inspectingTool, setInspectingTool] = useState<ToolMetadata | null>(null);
  const [togglingTool, setTogglingTool] = useState<string | null>(null);

  // Model matrix editing state
  const [editingMatrix, setEditingMatrix] = useState<Record<string, RoleModelConfig>>({});
  const [savingMatrix, setSavingMatrix] = useState<boolean>(false);

  // Execution policies editing state
  const [policyForm, setPolicyForm] = useState<Partial<ExecutionPolicyConfig>>({});
  const [savingPolicies, setSavingPolicies] = useState<boolean>(false);

  const fetchSettings = async (showRefresh = false) => {
    try {
      if (showRefresh) setRefreshing(true);
      setErrorMessage(null);

      const summary = await getSettingsSummary();
      setTools(summary.tools);
      setModelMatrix(summary.model_matrix);
      setEditingMatrix(summary.model_matrix.roles);
      setPolicies(summary.execution_policies);
      setPolicyForm(summary.execution_policies);
      setHealth(summary.health_summary);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load platform settings from FastAPI backend.";
      setErrorMessage(`${msg} (Backend: ${API_BASE_URL})`);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function init() {
      try {
        const summary = await getSettingsSummary();
        if (isMounted) {
          setTools(summary.tools);
          setModelMatrix(summary.model_matrix);
          setEditingMatrix(summary.model_matrix.roles);
          setPolicies(summary.execution_policies);
          setPolicyForm(summary.execution_policies);
          setHealth(summary.health_summary);
        }
      } catch (err: unknown) {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : "Failed to load platform settings from FastAPI backend.";
          setErrorMessage(`${msg} (Backend: ${API_BASE_URL})`);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }
    init();
    return () => {
      isMounted = false;
    };
  }, []);

  const showNotification = (msg: string) => {
    setSuccessBanner(msg);
    setTimeout(() => setSuccessBanner(null), 4000);
  };

  // ---------------------------------------------------------------------------
  // Tool Handlers
  // ---------------------------------------------------------------------------

  const handleToggleTool = async (toolName: string, currentEnabled: boolean) => {
    try {
      setTogglingTool(toolName);
      const updated = await toggleTool(toolName, !currentEnabled);
      setTools((prev) => prev.map((t) => (t.name === toolName ? updated : t)));
      showNotification(`Tool '${toolName}' is now ${updated.enabled ? "enabled" : "disabled"}.`);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : `Failed to toggle tool ${toolName}`);
    } finally {
      setTogglingTool(null);
    }
  };

  const handleTestTool = async (toolName: string) => {
    try {
      setTestingTool(toolName);
      const result = await testRegisteredTool(toolName);
      setToolTestResults((prev) => ({ ...prev, [toolName]: result }));
      setTools((prev) =>
        prev.map((t) =>
          t.name === toolName
            ? {
                ...t,
                last_test_status: result.status,
                last_test_latency_ms: result.duration_ms,
                last_tested_at: result.tested_at,
              }
            : t
        )
      );
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : `Failed to execute safe test for ${toolName}`);
    } finally {
      setTestingTool(null);
    }
  };

  // ---------------------------------------------------------------------------
  // Model Matrix Handlers
  // ---------------------------------------------------------------------------

  const handleRoleModelChange = (role: string, field: keyof RoleModelConfig, value: unknown) => {
    setEditingMatrix((prev) => ({
      ...prev,
      [role]: {
        ...prev[role],
        [field]: value,
      },
    }));
  };

  const handleSaveModelMatrix = async () => {
    try {
      setSavingMatrix(true);
      setErrorMessage(null);
      const updated = await updateModelMatrix(editingMatrix);
      setModelMatrix(updated);
      setEditingMatrix(updated.roles);
      showNotification("Model Matrix assignments updated & persisted successfully.");
    } catch (err: unknown) {
      // Look for axios response error message
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const detail = axiosErr.response?.data?.detail;
      setErrorMessage(detail || (err instanceof Error ? err.message : "Failed to update Model Matrix."));
    } finally {
      setSavingMatrix(false);
    }
  };

  // ---------------------------------------------------------------------------
  // Policy Handlers
  // ---------------------------------------------------------------------------

  const handleSavePolicies = async () => {
    try {
      setSavingPolicies(true);
      setErrorMessage(null);
      const updated = await updateExecutionPolicies(policyForm);
      setPolicies(updated);
      setPolicyForm(updated);
      showNotification("Platform execution policies verified & persisted.");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      const detail = axiosErr.response?.data?.detail;
      setErrorMessage(detail || (err instanceof Error ? err.message : "Policy validation failed."));
    } finally {
      setSavingPolicies(false);
    }
  };

  const handleRefreshHealth = async () => {
    try {
      setRefreshing(true);
      const liveHealth = await getRuntimeHealth();
      setHealth(liveHealth);
      showNotification("Live diagnostic telemetry refreshed.");
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : "Could not refresh diagnostics.");
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 20, padding: "20px 0" }}>
        <div className="card" style={{ padding: "32px", textAlign: "center" }}>
          <div style={{ fontSize: 28, marginBottom: 12 }}>⚙️</div>
          <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Loading Platform Settings &amp; Telemetry…</div>
          <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
            Synchronizing Tool Registry, Model Matrix, and Subsystem Diagnostics from FastAPI
          </p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
      {/* Top Banner */}
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
            <span style={{ fontSize: 22 }}>⚙️</span>
            <h1 style={{ fontSize: 20, fontWeight: 800 }}>Platform Settings &amp; Runtime Hub</h1>
            <span className="badge badge-indigo">Runtime Config v{health?.version || "0.2.0"}</span>
            {health?.overall_status === "healthy" ? (
              <span className="badge badge-emerald">Operational</span>
            ) : (
              <span className="badge badge-amber">Telemetry Degraded</span>
            )}
          </div>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginTop: 4 }}>
            Manage executable tool dispatches, model provider matrix, hard execution policies, and subsystem health
          </p>
        </div>

        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <button
            onClick={() => fetchSettings(true)}
            disabled={refreshing}
            className="btn btn-secondary btn-sm"
            style={{ display: "flex", alignItems: "center", gap: 6 }}
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              style={{ animation: refreshing ? "spin 1s linear infinite" : "none" }}
            >
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67" />
            </svg>
            {refreshing ? "Refreshing…" : "Refresh Diagnostics"}
          </button>
        </div>
      </div>

      {/* Notifications */}
      {successBanner && (
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
          ✓ {successBanner}
        </div>
      )}

      {errorMessage && (
        <div
          className="fade-up"
          style={{
            padding: "12px 18px",
            borderRadius: 8,
            background: "rgba(239, 68, 68, 0.12)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "#f87171",
            fontSize: 13,
            fontWeight: 600,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span>⚠️ {errorMessage}</span>
          <button
            onClick={() => setErrorMessage(null)}
            style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer", fontSize: 16 }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Navigation Tabs */}
      <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--border-soft)", paddingBottom: 8 }}>
        <button
          onClick={() => setActiveTab("tools")}
          className={`btn btn-sm ${activeTab === "tools" ? "btn-primary" : "btn-secondary"}`}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <span>🔧</span> Tool Registry ({tools.length})
        </button>
        <button
          onClick={() => setActiveTab("models")}
          className={`btn btn-sm ${activeTab === "models" ? "btn-primary" : "btn-secondary"}`}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <span>🤖</span> Model Matrix ({Object.keys(editingMatrix).length} Roles)
        </button>
        <button
          onClick={() => setActiveTab("policies")}
          className={`btn btn-sm ${activeTab === "policies" ? "btn-primary" : "btn-secondary"}`}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <span>🛡️</span> Execution Policies
        </button>
        <button
          onClick={() => setActiveTab("health")}
          className={`btn btn-sm ${activeTab === "health" ? "btn-primary" : "btn-secondary"}`}
          style={{ display: "flex", alignItems: "center", gap: 6 }}
        >
          <span>🩺</span> Runtime Health ({health?.overall_status || "Checking"})
        </button>
      </div>

      {/* ===================================================================== */}
      {/* SECTION A: TOOL REGISTRY */}
      {/* ===================================================================== */}
      {activeTab === "tools" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700 }}>Executable Tool Registry &amp; Sandboxes</h2>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                Dynamically registered tool callables. Disabling a tool prevents agents from dispatching it during execution.
              </p>
            </div>
            <span className="badge badge-slate" style={{ fontSize: 12 }}>
              {tools.filter((t) => t.enabled).length} of {tools.length} Tools Active
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 16 }}>
            {tools.map((tool) => {
              const testRes = toolTestResults[tool.name];
              const isToggling = togglingTool === tool.name;
              const isTesting = testingTool === tool.name;

              return (
                <div
                  key={tool.name}
                  className="card fade-up"
                  style={{
                    padding: "18px 20px",
                    display: "flex",
                    flexDirection: "column",
                    justifyContent: "space-between",
                    border: tool.enabled
                      ? "1px solid var(--border-soft)"
                      : "1px dashed rgba(148, 163, 184, 0.3)",
                    opacity: tool.enabled ? 1 : 0.75,
                    transition: "all 0.2s ease",
                  }}
                >
                  <div>
                    {/* Header: Name & Status */}
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 10 }}>
                      <div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <span style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>
                            {tool.display_name}
                          </span>
                          <code style={{ fontSize: 11, color: "var(--text-muted)" }}>{tool.name}</code>
                        </div>
                        <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 6, lineHeight: 1.4 }}>
                          {tool.description}
                        </p>
                      </div>

                      {/* Enable/Disable Toggle */}
                      <button
                        onClick={() => handleToggleTool(tool.name, tool.enabled)}
                        disabled={isToggling}
                        className={`btn btn-sm ${tool.enabled ? "btn-emerald" : "btn-secondary"}`}
                        style={{ minWidth: 74, fontSize: 11, padding: "4px 8px" }}
                        title={tool.enabled ? "Click to disable tool" : "Click to enable tool"}
                      >
                        {isToggling ? "…" : tool.enabled ? "✓ Enabled" : "Disabled"}
                      </button>
                    </div>

                    {/* Metadata Badges */}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 12 }}>
                      <span className="badge badge-indigo" style={{ fontSize: 10 }}>
                        {tool.category.toUpperCase()}
                      </span>

                      {tool.safety_classification === "sandboxed_execution" && (
                        <span className="badge badge-emerald" style={{ fontSize: 10 }}>
                          🛡️ Sandboxed Subprocess
                        </span>
                      )}
                      {tool.safety_classification === "network_egress" && (
                        <span className="badge badge-amber" style={{ fontSize: 10 }}>
                          🌐 Network Egress
                        </span>
                      )}
                      {tool.safety_classification === "safe_read_only" && (
                        <span className="badge badge-cyan" style={{ fontSize: 10 }}>
                          📖 Read-Only
                        </span>
                      )}

                      {tool.required_credentials.length > 0 && (
                        <span
                          className={`badge ${tool.credentials_configured ? "badge-emerald" : "badge-slate"}`}
                          style={{ fontSize: 10 }}
                        >
                          🔑 {tool.required_credentials.join(", ")}: {tool.credentials_configured ? "Configured" : "Offline"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions & Test Status Footer */}
                  <div style={{ marginTop: 16, borderTop: "1px solid var(--border-soft)", paddingTop: 12 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <button
                        onClick={() => setInspectingTool(tool)}
                        className="btn btn-secondary btn-sm"
                        style={{ fontSize: 11, padding: "4px 10px" }}
                      >
                        Inspect Schema
                      </button>

                      <button
                        onClick={() => handleTestTool(tool.name)}
                        disabled={isTesting}
                        className="btn btn-primary btn-sm"
                        style={{ fontSize: 11, padding: "4px 10px", display: "flex", alignItems: "center", gap: 6 }}
                      >
                        {isTesting ? "Executing Test…" : "Test Tool (Safe)"}
                      </button>
                    </div>

                    {/* Test result display */}
                    {(testRes || tool.last_test_status) && (
                      <div
                        style={{
                          marginTop: 10,
                          padding: "8px 12px",
                          borderRadius: 6,
                          fontSize: 11,
                          background:
                            (testRes?.status || tool.last_test_status) === "success"
                              ? "rgba(16, 185, 129, 0.08)"
                              : (testRes?.status || tool.last_test_status) === "no_credentials"
                              ? "rgba(245, 158, 11, 0.08)"
                              : "rgba(239, 68, 68, 0.08)",
                          border:
                            (testRes?.status || tool.last_test_status) === "success"
                              ? "1px solid rgba(16, 185, 129, 0.25)"
                              : (testRes?.status || tool.last_test_status) === "no_credentials"
                              ? "1px solid rgba(245, 158, 11, 0.25)"
                              : "1px solid rgba(239, 68, 68, 0.25)",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600 }}>
                          <span>
                            Last Test:{" "}
                            {(testRes?.status || tool.last_test_status) === "success"
                              ? "✓ Success"
                              : (testRes?.status || tool.last_test_status) === "no_credentials"
                              ? "⚡ Offline (No API Key)"
                              : "❌ Failed"}
                          </span>
                          <span>
                            {(testRes?.duration_ms || tool.last_test_latency_ms)?.toFixed(1)} ms
                          </span>
                        </div>
                        {testRes && (
                          <div style={{ marginTop: 4, color: "var(--text-muted)", wordBreak: "break-all" }}>
                            {testRes.output_preview || testRes.error}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Schema Inspection Modal / Drawer */}
          {inspectingTool && (
            <div
              style={{
                position: "fixed",
                top: 0,
                left: 0,
                right: 0,
                bottom: 0,
                background: "rgba(0,0,0,0.6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 1000,
                padding: 20,
              }}
              onClick={() => setInspectingTool(null)}
            >
              <div
                className="card fade-up"
                style={{
                  maxWidth: 600,
                  width: "100%",
                  maxHeight: "85vh",
                  overflowY: "auto",
                  padding: 24,
                }}
                onClick={(e) => e.stopPropagation()}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                  <div>
                    <h3 style={{ fontSize: 16, fontWeight: 700 }}>
                      Schema Specification: {inspectingTool.display_name}
                    </h3>
                    <code style={{ fontSize: 12, color: "#818cf8" }}>{inspectingTool.name}</code>
                  </div>
                  <button
                    onClick={() => setInspectingTool(null)}
                    className="btn btn-secondary btn-sm"
                    style={{ fontSize: 14 }}
                  >
                    ✕
                  </button>
                </div>

                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                  <div>
                    <span className="form-label">Description</span>
                    <p style={{ fontSize: 13, color: "var(--text-primary)", marginTop: 2 }}>
                      {inspectingTool.description}
                    </p>
                  </div>

                  <div>
                    <span className="form-label">Safety &amp; Isolation</span>
                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                      Classification: <code>{inspectingTool.safety_classification}</code>
                      {inspectingTool.safety_classification === "sandboxed_execution" &&
                        " — Subprocess execution stripped of environment variables with AST call restrictions."}
                    </p>
                  </div>

                  <div>
                    <span className="form-label">Required Credentials (Protected Server-Side)</span>
                    <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                      {inspectingTool.required_credentials.length > 0
                        ? inspectingTool.required_credentials.map((c) => (
                            <span key={c} className="badge badge-slate" style={{ marginRight: 6 }}>
                              {c}: {inspectingTool.credentials_configured ? "Present in .env" : "Not Set"}
                            </span>
                          ))
                        : "No external credentials required. Self-contained execution."}
                    </p>
                  </div>

                  <div>
                    <span className="form-label">JSON Input Schema</span>
                    <pre
                      style={{
                        background: "var(--bg-card-subtle)",
                        padding: 12,
                        borderRadius: 6,
                        fontSize: 11,
                        overflowX: "auto",
                        border: "1px solid var(--border-soft)",
                      }}
                    >
                      {JSON.stringify(inspectingTool.input_schema, null, 2)}
                    </pre>
                  </div>
                </div>

                <div style={{ marginTop: 20, textAlign: "right" }}>
                  <button onClick={() => setInspectingTool(null)} className="btn btn-secondary btn-sm">
                    Close
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ===================================================================== */}
      {/* SECTION B: MODEL MATRIX */}
      {/* ===================================================================== */}
      {activeTab === "models" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700 }}>Agent Role to Model Provider Matrix</h2>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                Configure model assignments per agent role. Supported providers are validated against the actual repository integration.
              </p>
            </div>

            <button
              onClick={handleSaveModelMatrix}
              disabled={savingMatrix}
              className="btn btn-primary btn-sm"
              style={{ display: "flex", alignItems: "center", gap: 6 }}
            >
              {savingMatrix ? "Validating & Saving…" : "Save Model Matrix"}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 16 }}>
            {Object.entries(editingMatrix).map(([roleKey, cfg]) => {
              return (
                <div
                  key={roleKey}
                  className="card fade-up"
                  style={{
                    padding: "18px 20px",
                    display: "flex",
                    flexDirection: "column",
                    gap: 12,
                  }}
                >
                  {/* Role Header with Mascot */}
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <AgentMascot role={roleKey} size={36} />
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>
                        {roleKey.replace("_", " ").toUpperCase()}
                      </div>
                      <span className="badge badge-indigo" style={{ fontSize: 10 }}>
                        {cfg.is_supported ? "Active Provider" : "Planned Provider"}
                      </span>
                    </div>
                  </div>

                  {/* Provider selection */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: 11 }}>Provider</label>
                    <select
                      value={cfg.provider}
                      onChange={(e) => handleRoleModelChange(roleKey, "provider", e.target.value)}
                      className="form-input"
                      style={{ fontSize: 12, padding: "6px 10px" }}
                    >
                      <optgroup label="Supported Providers">
                        <option value="gemini">Google Gemini (Active)</option>
                        <option value="mock_deterministic">Deterministic Mock (Offline Runner)</option>
                      </optgroup>
                      <optgroup label="Planned Future Integrations (Unsupported)">
                        <option value="openai" disabled>OpenAI (Coming Soon)</option>
                        <option value="anthropic" disabled>Anthropic Claude (Coming Soon)</option>
                        <option value="ollama" disabled>Ollama Local (Coming Soon)</option>
                      </optgroup>
                    </select>
                  </div>

                  {/* Model identifier */}
                  <div className="form-group" style={{ margin: 0 }}>
                    <label className="form-label" style={{ fontSize: 11 }}>Model Identifier</label>
                    {cfg.provider === "gemini" ? (
                      <select
                        value={cfg.model_identifier}
                        onChange={(e) => handleRoleModelChange(roleKey, "model_identifier", e.target.value)}
                        className="form-input"
                        style={{ fontSize: 12, padding: "6px 10px" }}
                      >
                        <option value="gemini-1.5-pro">gemini-1.5-pro (High Reasoning)</option>
                        <option value="gemini-1.5-flash">gemini-1.5-flash (Fast &amp; Efficient)</option>
                        <option value="gemini-2.0-flash">gemini-2.0-flash (Next-Gen)</option>
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={cfg.model_identifier}
                        onChange={(e) => handleRoleModelChange(roleKey, "model_identifier", e.target.value)}
                        className="form-input"
                        style={{ fontSize: 12, padding: "6px 10px" }}
                      />
                    )}
                  </div>

                  {/* Temperature slider */}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 11, color: "var(--text-muted)" }}>Temperature: {cfg.temperature}</span>
                    <input
                      type="range"
                      min="0.0"
                      max="1.0"
                      step="0.05"
                      value={cfg.temperature}
                      onChange={(e) => handleRoleModelChange(roleKey, "temperature", parseFloat(e.target.value))}
                      style={{ width: "60%", accentColor: "#6366f1" }}
                    />
                  </div>

                  {/* Status indicator */}
                  <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", justifyContent: "space-between" }}>
                    <span>Credential:</span>
                    <span
                      style={{
                        fontWeight: 600,
                        color: cfg.credential_status === "configured" ? "#34d399" : "#fbbf24",
                      }}
                    >
                      {cfg.credential_status === "configured" ? "✓ Key Set in .env" : "Offline Fallback"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SECTION C: EXECUTION POLICIES */}
      {/* ===================================================================== */}
      {activeTab === "policies" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700 }}>Platform Execution Policies &amp; Budgets</h2>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                Global operational limits enforced server-side. Task constraints override broader settings where stricter.
              </p>
            </div>

            <button
              onClick={handleSavePolicies}
              disabled={savingPolicies}
              className="btn btn-primary btn-sm"
            >
              {savingPolicies ? "Applying Policies…" : "Apply Execution Policies"}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
            {/* Max Agents Budget */}
            <div className="card fade-up" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <span className="form-label" style={{ margin: 0 }}>Max Multi-Agent Nodes</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: "#818cf8" }}>{policyForm.max_agents} agents</span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={policyForm.max_agents ?? 8}
                onChange={(e) => setPolicyForm({ ...policyForm, max_agents: parseInt(e.target.value) })}
                style={{ width: "100%", accentColor: "#6366f1" }}
              />
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                Upper bound on synthesized agent count per DAG. Architectures exceeding this are rejected.
              </span>
            </div>

            {/* Max Execution Duration */}
            <div className="card fade-up" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <span className="form-label" style={{ margin: 0 }}>Max Execution Timeout</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: "#34d399" }}>
                  {policyForm.max_execution_duration_seconds}s
                </span>
              </div>
              <input
                type="range"
                min="5"
                max="300"
                step="5"
                value={policyForm.max_execution_duration_seconds ?? 60}
                onChange={(e) =>
                  setPolicyForm({
                    ...policyForm,
                    max_execution_duration_seconds: parseFloat(e.target.value),
                  })
                }
                style={{ width: "100%", accentColor: "#10b981" }}
              />
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                Hard timeout before halting agent execution graphs.
              </span>
            </div>

            {/* Max Tool Calls Per Agent */}
            <div className="card fade-up" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <span className="form-label" style={{ margin: 0 }}>Max Tool Calls Per Agent</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: "#f59e0b" }}>
                  {policyForm.max_tool_calls_per_agent} calls
                </span>
              </div>
              <input
                type="range"
                min="1"
                max="20"
                value={policyForm.max_tool_calls_per_agent ?? 5}
                onChange={(e) =>
                  setPolicyForm({ ...policyForm, max_tool_calls_per_agent: parseInt(e.target.value) })
                }
                style={{ width: "100%", accentColor: "#f59e0b" }}
              />
              <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
                Prevents infinite invocation loops in agent step execution.
              </span>
            </div>

            {/* Verification by default */}
            <div className="card fade-up" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 700 }}>Mandatory Independent Verification</div>
                  <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                    Requires a dedicated Verifier / Critic agent in every synthesized DAG
                  </div>
                </div>
                <input
                  type="checkbox"
                  checked={policyForm.require_verification_by_default ?? false}
                  onChange={(e) =>
                    setPolicyForm({ ...policyForm, require_verification_by_default: e.target.checked })
                  }
                  style={{ width: 18, height: 18, accentColor: "#6366f1", cursor: "pointer" }}
                />
              </div>
            </div>
          </div>

          {/* Sandbox & Isolation Status Card */}
          <div className="card fade-up" style={{ padding: 20, display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ fontSize: 32 }}>🛡️</div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 14, fontWeight: 700 }}>Python Subprocess AST Sandbox Isolation</span>
                <span className="badge badge-emerald">Enforced Server-Side</span>
              </div>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                All Python code interpreter calls run in an isolated subprocess with stripped environment variables,
                disallowed dangerous modules (<code>os</code>, <code>sys</code>, <code>subprocess</code>, <code>socket</code>),
                and AST call tree validation. Arbitrary file access and shell execution are strictly blocked.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ===================================================================== */}
      {/* SECTION D: RUNTIME HEALTH */}
      {/* ===================================================================== */}
      {activeTab === "health" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <h2 style={{ fontSize: 16, fontWeight: 700 }}>Subsystem Health &amp; Diagnostics</h2>
              <p style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                Real backend checks against database engine, tool sandboxes, model connectivity, and event streaming.
              </p>
            </div>
            <button
              onClick={handleRefreshHealth}
              disabled={refreshing}
              className="btn btn-secondary btn-sm"
            >
              {refreshing ? "Checking…" : "Run Full Health Check"}
            </button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 16 }}>
            {health?.subsystems &&
              Object.entries(health.subsystems).map(([subsystemKey, sub]) => {
                const isHealthy = sub.status === "healthy";
                const isDegraded = sub.status === "degraded";

                return (
                  <div
                    key={subsystemKey}
                    className="card fade-up"
                    style={{
                      padding: "18px 20px",
                      display: "flex",
                      flexDirection: "column",
                      justifyContent: "space-between",
                    }}
                  >
                    <div>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: 14, fontWeight: 700 }}>{sub.name}</span>
                        <span
                          className={`badge ${
                            isHealthy ? "badge-emerald" : isDegraded ? "badge-amber" : "badge-rose"
                          }`}
                        >
                          {sub.status.toUpperCase()}
                        </span>
                      </div>

                      {sub.latency_ms !== undefined && (
                        <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 4 }}>
                          Latency: <code>{sub.latency_ms.toFixed(2)} ms</code>
                        </div>
                      )}

                      <div style={{ marginTop: 12, fontSize: 12, display: "flex", flexDirection: "column", gap: 4 }}>
                        {Object.entries(sub.details).map(([k, v]) => (
                          <div key={k} style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                            <span style={{ color: "var(--text-muted)", fontSize: 11 }}>{k}:</span>
                            <span style={{ fontWeight: 600, fontSize: 11, color: "var(--text-primary)" }}>
                              {String(v)}
                            </span>
                          </div>
                        ))}
                      </div>

                      {sub.error && (
                        <div
                          style={{
                            marginTop: 10,
                            padding: 8,
                            borderRadius: 6,
                            background: "rgba(239, 68, 68, 0.1)",
                            color: "#f87171",
                            fontSize: 11,
                          }}
                        >
                          Error: {sub.error}
                        </div>
                      )}
                    </div>

                    <div style={{ marginTop: 12, fontSize: 10, color: "var(--text-muted)", borderTop: "1px solid var(--border-soft)", paddingTop: 8 }}>
                      Checked: {new Date(sub.checked_at).toLocaleTimeString()}
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </div>
  );
}
