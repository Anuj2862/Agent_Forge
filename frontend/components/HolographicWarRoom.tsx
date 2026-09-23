"use client";

import { useState, useEffect } from "react";

interface AgentDef {
  id: string;
  name: string;
  role: string;
  color: string;
  glowColor: string;
  position: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  points: string[];
  tools: string[];
  systemRole: string;
  iconSvg: string;
}

const AGENTS: AgentDef[] = [
  {
    id: "researcher",
    name: "AI AGENT RESEARCHER",
    role: "Information Retrieval Specialist",
    color: "#00f0ff",
    glowColor: "rgba(0, 240, 255, 0.45)",
    position: "top-left",
    points: [
      "Information Retrieval",
      "Data Analysis",
      "Insight Generation",
      "Knowledge Synthesis",
    ],
    tools: ["web_search", "document_retriever", "rag_engine"],
    systemRole: "Gathers external ground truth, validates multi-source references, and synthesizes raw evidence.",
    iconSvg: "M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-6h2zm0-8h-2V7h2z",
  },
  {
    id: "planner",
    name: "AI AGENT PLANNER",
    role: "Strategic Meta Controller",
    color: "#38bdf8",
    glowColor: "rgba(56, 189, 248, 0.45)",
    position: "top-right",
    points: [
      "Goal Decomposition",
      "Strategy Planning",
      "Task Assignment",
      "Scenario Modeling",
    ],
    tools: ["task_decomposer", "topology_optimizer", "flow_synthesizer"],
    systemRole: "Analyzes user intent, designs multi-agent graph topologies, and orchestrates execution routes.",
    iconSvg: "M3 3h18v18H3z M9 3v18 M15 3v18 M3 9h18 M3 15h18",
  },
  {
    id: "analyst",
    name: "AI AGENT ANALYST",
    role: "Evaluation & Reflection Critic",
    color: "#818cf8",
    glowColor: "rgba(129, 140, 248, 0.45)",
    position: "bottom-left",
    points: [
      "Data Processing",
      "Pattern Recognition",
      "Anomaly Detection",
      "Predictive Insights",
    ],
    tools: ["rubric_evaluator", "fact_checker", "reflection_engine"],
    systemRole: "Evaluates outputs across quality, completeness, and accuracy, detecting halluncinations and gaps.",
    iconSvg: "M18 20V10M12 20V4M6 20v-6",
  },
  {
    id: "executor",
    name: "AI AGENT EXECUTOR",
    role: "LangGraph Execution Engine",
    color: "#c084fc",
    glowColor: "rgba(192, 132, 252, 0.45)",
    position: "bottom-right",
    points: [
      "Action Implementation",
      "API Integration",
      "Workflow Automation",
      "Real-time Monitoring",
    ],
    tools: ["python_executor", "tool_dispatcher", "state_reducer"],
    systemRole: "Runs agent state machines in LangGraph, dispatches external tool calls, and compiles artifacts.",
    iconSvg: "M5 3l14 9-14 9V3z",
  },
];

export default function HolographicWarRoom({
  activeTask,
  isExecuting = false,
}: {
  activeTask?: string;
  isExecuting?: boolean;
}) {
  const [selectedAgent, setSelectedAgent] = useState<AgentDef>(AGENTS[0]);
  const [pulseActive, setPulseActive] = useState<boolean>(true);
  const [waveSeed, setWaveSeed] = useState<number>(0);

  // Animate waveform
  useEffect(() => {
    const timer = setInterval(() => {
      setWaveSeed((s) => (s + 1) % 100);
    }, 120);
    return () => clearInterval(timer);
  }, []);

  // Generate dynamic wave path
  const generateWave = () => {
    const points: string[] = [];
    for (let x = 0; x <= 180; x += 10) {
      const y = 20 + Math.sin((x + waveSeed * 6) * 0.08) * 12 + Math.cos((x * 0.15)) * 6;
      points.push(`${x},${y.toFixed(1)}`);
    }
    return `M 0,20 L ${points.join(" L ")}`;
  };

  return (
    <div className="holo-war-room">
      {/* Background Cybernetic Datacenter Grid */}
      <div className="holo-bg-overlay" />
      <div className="holo-perspective-grid" />

      {/* Top Hologram Title */}
      <div className="holo-header">
        <div className="holo-header-title">MULTI-AGENT AUTONOMOUS SYSTEM</div>
        <div className="holo-header-sub">
          COLLABORATE · COORDINATE · ACHIEVE MISSION
        </div>
        <div className="holo-live-tag">
          <span className="holo-live-dot" />
          <span>NEURAL NETWORK SYNCHRONIZED</span>
        </div>
      </div>

      {/* Main Holographic Battlefield Stage */}
      <div className="holo-stage">
        {/* SVG Laser Beams & Data Flow Layer */}
        <svg className="holo-laser-canvas" viewBox="0 0 1000 600" preserveAspectRatio="none">
          <defs>
            {/* Glow filters */}
            <filter id="cyan-laser-glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <linearGradient id="laser-grad-1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#38bdf8" stopOpacity="1" />
              <stop offset="100%" stopColor="#818cf8" stopOpacity="0.8" />
            </linearGradient>
            <linearGradient id="laser-grad-2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#00f0ff" stopOpacity="1" />
              <stop offset="100%" stopColor="#c084fc" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Cross connecting lasers to center nexus (500, 300) */}
          {/* Top-Left to Center */}
          <line x1="220" y1="140" x2="500" y2="300" stroke="#00f0ff" strokeWidth="1.8" strokeDasharray="6 4" className="laser-beam" />
          {/* Top-Right to Center */}
          <line x1="780" y1="140" x2="500" y2="300" stroke="#38bdf8" strokeWidth="1.8" strokeDasharray="6 4" className="laser-beam" />
          {/* Bottom-Left to Center */}
          <line x1="220" y1="440" x2="500" y2="300" stroke="#818cf8" strokeWidth="1.8" strokeDasharray="6 4" className="laser-beam" />
          {/* Bottom-Right to Center */}
          <line x1="780" y1="440" x2="500" y2="300" stroke="#c084fc" strokeWidth="1.8" strokeDasharray="6 4" className="laser-beam" />

          {/* Inter-Agent Perimeter Lasers */}
          {/* Top-Left to Top-Right */}
          <line x1="260" y1="130" x2="740" y2="130" stroke="rgba(0, 240, 255, 0.4)" strokeWidth="1.2" strokeDasharray="4 6" />
          {/* Top-Left to Bottom-Left */}
          <line x1="210" y1="180" x2="210" y2="400" stroke="rgba(0, 240, 255, 0.4)" strokeWidth="1.2" strokeDasharray="4 6" />
          {/* Top-Right to Bottom-Right */}
          <line x1="790" y1="180" x2="790" y2="400" stroke="rgba(56, 189, 248, 0.4)" strokeWidth="1.2" strokeDasharray="4 6" />
          {/* Bottom-Left to Bottom-Right */}
          <line x1="260" y1="450" x2="740" y2="450" stroke="rgba(129, 140, 248, 0.4)" strokeWidth="1.2" strokeDasharray="4 6" />

          {/* Traveling energy photon pulses */}
          <circle cx="360" cy="220" r="3" fill="#00f0ff" filter="url(#cyan-laser-glow)" className="pulse-photon" />
          <circle cx="640" cy="220" r="3" fill="#38bdf8" filter="url(#cyan-laser-glow)" className="pulse-photon-reverse" />
          <circle cx="360" cy="370" r="3" fill="#818cf8" filter="url(#cyan-laser-glow)" className="pulse-photon" />
          <circle cx="640" cy="370" r="3" fill="#c084fc" filter="url(#cyan-laser-glow)" className="pulse-photon-reverse" />
        </svg>

        {/* Central Glowing Nexus Core */}
        <div className="holo-center-nexus">
          <div className="nexus-ring ring-3" />
          <div className="nexus-ring ring-2" />
          <div className="nexus-ring ring-1" />
          <div className="nexus-core-orb">
            <div className="nexus-inner-pulse" />
            <div className="nexus-symbol">⚡</div>
          </div>
          <div className="nexus-label">META NEXUS</div>
        </div>

        {/* Laser Chip Tags (floating communication labels matching picture) */}
        <div className="holo-chip chip-top" style={{ left: "50%", top: "21%", transform: "translateX(-50%)" }}>
          <span className="chip-icon">📄</span>
          <span>PLAN TOGETHER</span>
        </div>

        <div className="holo-chip chip-left" style={{ left: "34%", top: "37%" }}>
          <span className="chip-icon">🗄️</span>
          <span>EXCHANGE DATA</span>
        </div>

        <div className="holo-chip chip-right" style={{ right: "34%", top: "37%" }}>
          <span className="chip-icon">📋</span>
          <span>ASSIGN TASKS</span>
        </div>

        <div className="holo-chip chip-bottom-left" style={{ left: "37%", bottom: "27%" }}>
          <span className="chip-icon">🔄</span>
          <span>SYNC PROGRESS</span>
        </div>

        <div className="holo-chip chip-bottom-right" style={{ right: "37%", bottom: "27%" }}>
          <span className="chip-icon">▶</span>
          <span>EXECUTE SOLUTIONS</span>
        </div>

        <div className="holo-chip chip-top-left-edge" style={{ left: "34%", top: "18%" }}>
          <span className="chip-icon">💡</span>
          <span>SHARE INSIGHTS</span>
        </div>

        {/* ── 4 Holographic Agent Nodes ────────────────────────────── */}
        {AGENTS.map((agent) => {
          const isSelected = selectedAgent.id === agent.id;
          return (
            <div
              key={agent.id}
              className={`holo-agent-pod pod-${agent.position} ${isSelected ? "selected" : ""}`}
              onClick={() => setSelectedAgent(agent)}
            >
              {/* Ground projection ring halo */}
              <div
                className="holo-ground-halo"
                style={{
                  borderColor: agent.color,
                  boxShadow: `0 0 25px ${agent.glowColor}, inset 0 0 15px ${agent.glowColor}`,
                }}
              >
                <div className="halo-spin-ring" style={{ borderColor: `${agent.color}88` }} />
              </div>

              {/* Vertical light projector beam */}
              <div
                className="holo-light-beam"
                style={{
                  background: `linear-gradient(to top, ${agent.color}44 0%, transparent 100%)`,
                }}
              />

              {/* Holographic Robot Avatar */}
              <div
                className="holo-avatar-container"
                style={{
                  borderColor: agent.color,
                  boxShadow: `0 0 20px ${agent.glowColor}`,
                }}
              >
                {/* Cyber Avatar Robot Face */}
                <div className="holo-robot-head">
                  <div className="robot-antenna" style={{ background: agent.color }} />
                  <div className="robot-visor" style={{ background: agent.color, boxShadow: `0 0 10px ${agent.color}` }}>
                    <div className="visor-scanline" />
                  </div>
                  <div className="robot-chassis" />
                  <div className="robot-ear-ring left" style={{ borderColor: agent.color }} />
                  <div className="robot-ear-ring right" style={{ borderColor: agent.color }} />
                </div>
              </div>

              {/* Hologram HUD Information Card */}
              <div
                className="holo-hud-card"
                style={{
                  borderColor: isSelected ? agent.color : "rgba(0, 240, 255, 0.25)",
                  boxShadow: isSelected ? `0 0 20px ${agent.glowColor}` : "none",
                }}
              >
                <div className="hud-card-header">
                  <span className="hud-card-title" style={{ color: agent.color }}>
                    {agent.name}
                  </span>
                </div>

                <div className="hud-card-list">
                  {agent.points.map((pt, i) => (
                    <div key={i} className="hud-card-item">
                      <span className="hud-check" style={{ color: agent.color }}>✓</span>
                      <span>{pt}</span>
                    </div>
                  ))}
                </div>

                <div className="hud-card-tools">
                  {agent.tools.map((tool) => (
                    <span
                      key={tool}
                      className="hud-tool-tag"
                      style={{
                        borderColor: `${agent.color}44`,
                        color: agent.color,
                      }}
                    >
                      {tool}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Lower Mission Command Deck (Matching Picture) ─────────── */}
      <div className="holo-command-deck">
        {/* Left: Global Agent Activity */}
        <div className="deck-card deck-activity">
          <div className="deck-title">GLOBAL AGENT ACTIVITY</div>
          <div className="deck-waveform-container">
            <svg viewBox="0 0 180 40" className="deck-waveform">
              <path
                d={generateWave()}
                fill="none"
                stroke="#00f0ff"
                strokeWidth="1.8"
                style={{ filter: "drop-shadow(0 0 4px #00f0ff)" }}
              />
            </svg>
          </div>
          <div className="deck-metrics-row">
            <div className="deck-metric">
              <span className="metric-val" style={{ color: "#00f0ff" }}>24ms</span>
              <span className="metric-lbl">LATENCY</span>
            </div>
            <div className="deck-metric">
              <span className="metric-val" style={{ color: "#38bdf8" }}>100%</span>
              <span className="metric-lbl">UPTIME</span>
            </div>
            <div className="deck-metric">
              <span className="metric-val" style={{ color: "#34d399" }}>4/4</span>
              <span className="metric-lbl">ACTIVE AGENTS</span>
            </div>
          </div>
        </div>

        {/* Center: Holographic Planetary Map / Radar Grid */}
        <div className="deck-card deck-globe">
          <div className="holographic-globe">
            <div className="globe-ring ring-a" />
            <div className="globe-ring ring-b" />
            <div className="globe-scan-line" />
            <div className="globe-coords">
              <span>LAT 37.7749° N</span>
              <span>LON 122.4194° W</span>
            </div>
          </div>
          <div className="globe-caption">AUTONOMOUS COORDINATION GRID</div>
        </div>

        {/* Right: Mission Status */}
        <div className="deck-card deck-status">
          <div className="deck-title">MISSION STATUS</div>
          <div className="status-checklist">
            <div className="status-item done">
              <span className="status-icon">✓</span>
              <span>Data Collected</span>
            </div>
            <div className="status-item done">
              <span className="status-icon">✓</span>
              <span>Analysis Complete</span>
            </div>
            <div className="status-item done">
              <span className="status-icon">✓</span>
              <span>Solutions Generated</span>
            </div>
            <div className="status-item in-progress">
              <span className="status-icon pulse-dot" />
              <span>Tasks Executing &amp; Evolving</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Active Inspected Agent Drawer ─────────────────────────── */}
      <div className="holo-agent-inspector">
        <div className="inspector-left">
          <div className="inspector-avatar" style={{ borderColor: selectedAgent.color, boxShadow: `0 0 12px ${selectedAgent.glowColor}` }}>
            <span style={{ color: selectedAgent.color }}>◈</span>
          </div>
          <div>
            <div className="inspector-name" style={{ color: selectedAgent.color }}>
              {selectedAgent.name}
            </div>
            <div className="inspector-role">{selectedAgent.role}</div>
          </div>
        </div>
        <div className="inspector-desc">{selectedAgent.systemRole}</div>
        <div className="inspector-badge">
          <span>COGNITIVE CAPABILITY: 100%</span>
        </div>
      </div>
    </div>
  );
}
