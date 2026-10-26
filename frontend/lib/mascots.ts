export type AgentRole = "researcher" | "analyst" | "planner" | "executor" | "verifier" | "critic";

export type ExecutionState = "idle" | "running" | "waiting" | "completed" | "failed" | "inconclusive";

export interface RoleMetadata {
  role: AgentRole;
  name: string;
  tagline: string;
  color: string;
  lightColor: string;
  border: string;
  borderLight: string;
  bgSubtle: string;
  glow: string;
  src: string;
  webpSrc: string;
}

export interface StatusMetadata {
  state: ExecutionState;
  label: string;
  color: string;
  glow: string;
  badgeBg: string;
  badgeBorder: string;
  dotColor: string;
}

/**
 * Canonical helper to match text against the 6 core agent personas.
 */
function matchRoleFromKeyword(raw: unknown): AgentRole | null {
  if (!raw || typeof raw !== "string") return null;
  const text = raw.trim().toLowerCase();
  if (!text) return null;

  // 1. Direct role name match
  if (text === "planner" || text === "planning") return "planner";
  if (text === "verifier" || text === "verification") return "verifier";
  if (text === "researcher" || text === "research") return "researcher";
  if (text === "analyst" || text === "analysis") return "analyst";
  if (text === "critic" || text === "critique") return "critic";
  if (text === "executor" || text === "execution") return "executor";

  // 2. Verifier: verification, validation, audit, invariant, fact-checking, guard
  if (
    text.includes("verif") ||
    text.includes("validat") ||
    text.includes("fact") ||
    text.includes("audit") ||
    text.includes("shield") ||
    text.includes("guard") ||
    text.includes("grounding") ||
    text.includes("grounded") ||
    text.includes("invariant") ||
    text.includes("compliance")
  ) {
    return "verifier";
  }

  // 3. Critic: code review, inspection, reflection, evaluation, QA, diagnostic, safety
  if (
    text.includes("critic") ||
    text.includes("review") ||
    text.includes("qa") ||
    text.includes("quality") ||
    text.includes("reflec") ||
    text.includes("diagnos") ||
    text.includes("inspect") ||
    text.includes("eval") ||
    text.includes("referee") ||
    text.includes("judge") ||
    text.includes("safety")
  ) {
    return "critic";
  }

  // 4. Planner: planning, decomposition, architecture, workflow, coordination, orchestration
  if (
    text.includes("plan") ||
    text.includes("decompos") ||
    text.includes("architect") ||
    text.includes("coordinator") ||
    text.includes("coordinat") ||
    text.includes("orchestrat") ||
    text.includes("routing") ||
    text.includes("router") ||
    text.includes("navigat") ||
    text.includes("topolog") ||
    text.includes("workflow") ||
    text.includes("designer") ||
    text.includes("strateg")
  ) {
    return "planner";
  }

  // 5. Researcher: web search, document retrieval, scraping, information gathering, data collection
  if (
    text.includes("research") ||
    text.includes("retriev") ||
    text.includes("search") ||
    text.includes("gather") ||
    text.includes("scrape") ||
    text.includes("scraper") ||
    text.includes("crawl") ||
    text.includes("collector") ||
    text.includes("browse") ||
    text.includes("document_retriever") ||
    text.includes("intelligence")
  ) {
    return "researcher";
  }

  // 6. Analyst: data analysis, reasoning, synthesis, writing, reporting, statistics, visualization
  if (
    text.includes("analy") ||
    text.includes("reason") ||
    text.includes("synthes") ||
    text.includes("report") ||
    text.includes("writer") ||
    text.includes("author") ||
    text.includes("editor") ||
    text.includes("chart") ||
    text.includes("viz") ||
    text.includes("visualiz") ||
    text.includes("insight") ||
    text.includes("statistic") ||
    text.includes("summar")
  ) {
    return "analyst";
  }

  // 7. Executor: coding, engineering, implementation, tools, runtime execution
  if (
    text.includes("execut") ||
    text.includes("coder") ||
    text.includes("coding") ||
    text.includes("code") ||
    text.includes("engineer") ||
    text.includes("developer") ||
    text.includes("programmer") ||
    text.includes("implement") ||
    text.includes("runner") ||
    text.includes("worker") ||
    text.includes("operator")
  ) {
    return "executor";
  }

  return null;
}

export function resolveAgentRole(target: unknown): AgentRole {
  if (!target) return "executor";

  // If string passed directly
  if (typeof target === "string") {
    const matched = matchRoleFromKeyword(target);
    return matched || "executor";
  }

  // If object passed: evaluate in strict hierarchy to prevent secondary objective words
  // (e.g. "gathered research data" or "according to plan") from overriding explicit roles
  if (typeof target === "object") {
    const obj = target as Record<string, unknown>;

    // Step 1: Match on specific explicit role (e.g. "Information Analyst", "Web Researcher", "Software Architect")
    if (obj.role && typeof obj.role === "string") {
      const cleanRole = obj.role.trim();
      const lower = cleanRole.toLowerCase();
      if (!["agent", "specialist", "generic", "unknown"].includes(lower)) {
        const match = matchRoleFromKeyword(cleanRole);
        if (match) return match;
      }
    }

    // Step 2: Match on explicit agent name (e.g. "Analysis Agent", "Code Reviewer", "Search Agent")
    if (obj.name && typeof obj.name === "string") {
      const match = matchRoleFromKeyword(obj.name);
      if (match) return match;
    }

    // Step 3: Match on agent ID (e.g. "analysis_agent", "planner_agent", "search_agent", "validator_agent")
    if (obj.agent_id && typeof obj.agent_id === "string") {
      const match = matchRoleFromKeyword(obj.agent_id);
      if (match) return match;
    }

    // Step 4: Fall back to matching on objective ONLY if role/name/agent_id did not yield a role
    if (obj.objective && typeof obj.objective === "string") {
      const match = matchRoleFromKeyword(obj.objective);
      if (match) return match;
    }
  }

  return "executor";
}

export function getRoleMetadata(role: AgentRole, isLight = false): RoleMetadata {
  switch (role) {
    case "planner":
      return {
        role: "planner",
        name: "Planner",
        tagline: "Task Decomposition & Graph Routing",
        color: isLight ? "#0D9488" : "#2DD4BF",
        lightColor: isLight ? "rgba(13, 148, 136, 0.12)" : "rgba(45, 212, 191, 0.12)",
        border: "rgba(45, 212, 191, 0.35)",
        borderLight: "rgba(13, 148, 136, 0.45)",
        bgSubtle: isLight ? "rgba(13, 148, 136, 0.08)" : "rgba(45, 212, 191, 0.08)",
        glow: "0 0 16px rgba(45, 212, 191, 0.35)",
        src: "/mascots/planner.png",
        webpSrc: "/mascots/planner.webp",
      };
    case "verifier":
      return {
        role: "verifier",
        name: "Verifier",
        tagline: "Fact Verification & Invariant Guard",
        color: isLight ? "#0891B2" : "#22D3EE",
        lightColor: isLight ? "rgba(8, 145, 178, 0.12)" : "rgba(34, 211, 238, 0.12)",
        border: "rgba(34, 211, 238, 0.40)",
        borderLight: "rgba(8, 145, 178, 0.45)",
        bgSubtle: isLight ? "rgba(8, 145, 178, 0.08)" : "rgba(34, 211, 238, 0.08)",
        glow: "0 0 16px rgba(34, 211, 238, 0.35)",
        src: "/mascots/verifier.png",
        webpSrc: "/mascots/verifier.webp",
      };
    case "researcher":
      return {
        role: "researcher",
        name: "Researcher",
        tagline: "Information Retrieval & Web Scraping",
        color: isLight ? "#2563EB" : "#3B82F6",
        lightColor: isLight ? "rgba(37, 99, 235, 0.12)" : "rgba(59, 130, 246, 0.12)",
        border: "rgba(59, 130, 246, 0.35)",
        borderLight: "rgba(37, 99, 235, 0.45)",
        bgSubtle: isLight ? "rgba(37, 99, 235, 0.08)" : "rgba(59, 130, 246, 0.08)",
        glow: "0 0 16px rgba(59, 130, 246, 0.35)",
        src: "/mascots/researcher.png",
        webpSrc: "/mascots/researcher.webp",
      };
    case "analyst":
      return {
        role: "analyst",
        name: "Analyst",
        tagline: "Analysis, Synthesis & Reporting",
        color: isLight ? "#7C3AED" : "#A78BFA",
        lightColor: isLight ? "rgba(124, 58, 237, 0.12)" : "rgba(167, 139, 250, 0.12)",
        border: "rgba(167, 139, 250, 0.35)",
        borderLight: "rgba(124, 58, 237, 0.45)",
        bgSubtle: isLight ? "rgba(124, 58, 237, 0.08)" : "rgba(167, 139, 250, 0.08)",
        glow: "0 0 16px rgba(167, 139, 250, 0.35)",
        src: "/mascots/analyst.png",
        webpSrc: "/mascots/analyst.webp",
      };
    case "critic":
      return {
        role: "critic",
        name: "Critic",
        tagline: "Quality Inspection & Safety Bounds",
        color: isLight ? "#DC2626" : "#F87171",
        lightColor: isLight ? "rgba(220, 38, 38, 0.12)" : "rgba(248, 113, 113, 0.12)",
        border: "rgba(248, 113, 113, 0.35)",
        borderLight: "rgba(220, 38, 38, 0.45)",
        bgSubtle: isLight ? "rgba(220, 38, 38, 0.08)" : "rgba(248, 113, 113, 0.08)",
        glow: "0 0 16px rgba(248, 113, 113, 0.35)",
        src: "/mascots/critic.png",
        webpSrc: "/mascots/critic.webp",
      };
    case "executor":
    default:
      return {
        role: "executor",
        name: "Executor",
        tagline: "Tool Invocation & Runtime Execution",
        color: isLight ? "#D97706" : "#FBBF24",
        lightColor: isLight ? "rgba(217, 119, 6, 0.12)" : "rgba(251, 191, 36, 0.12)",
        border: "rgba(251, 191, 36, 0.35)",
        borderLight: "rgba(217, 119, 6, 0.45)",
        bgSubtle: isLight ? "rgba(217, 119, 6, 0.08)" : "rgba(251, 191, 36, 0.08)",
        glow: "0 0 16px rgba(251, 191, 36, 0.35)",
        src: "/mascots/executor.png",
        webpSrc: "/mascots/executor.webp",
      };
  }
}

export function normalizeExecutionState(status?: string): ExecutionState {
  if (!status) return "waiting";
  const s = status.toLowerCase();
  if (s === "running" || s === "active" || s.includes("execut")) return "running";
  if (s === "completed" || s === "done" || s === "success") return "completed";
  if (s === "failed" || s === "error" || s.includes("fail")) return "failed";
  if (s === "idle") return "idle";
  if (s === "inconclusive" || s === "unknown") return "inconclusive";
  return "waiting";
}

export function getStatusMetadata(stateInput?: string, isLight = false): StatusMetadata {
  const state = normalizeExecutionState(stateInput);
  switch (state) {
    case "running":
      return {
        state: "running",
        label: "Running",
        color: isLight ? "#2563EB" : "#3B82F6",
        glow: "0 0 12px rgba(59, 130, 246, 0.6)",
        badgeBg: isLight ? "rgba(37, 99, 235, 0.15)" : "rgba(59, 130, 246, 0.2)",
        badgeBorder: isLight ? "#2563EB" : "#3B82F6",
        dotColor: "#38BDF8",
      };
    case "completed":
      return {
        state: "completed",
        label: "Completed",
        color: isLight ? "#059669" : "#10B981",
        glow: "0 0 10px rgba(16, 185, 129, 0.45)",
        badgeBg: isLight ? "rgba(5, 150, 105, 0.15)" : "rgba(16, 185, 129, 0.2)",
        badgeBorder: isLight ? "#059669" : "#10B981",
        dotColor: "#34D399",
      };
    case "failed":
      return {
        state: "failed",
        label: "Failed",
        color: isLight ? "#DC2626" : "#EF4444",
        glow: "0 0 12px rgba(239, 68, 68, 0.5)",
        badgeBg: isLight ? "rgba(220, 38, 38, 0.15)" : "rgba(239, 68, 68, 0.2)",
        badgeBorder: isLight ? "#DC2626" : "#EF4444",
        dotColor: "#F87171",
      };
    case "inconclusive":
      return {
        state: "inconclusive",
        label: "Inconclusive",
        color: isLight ? "#7C3AED" : "#8B5CF6",
        glow: "0 0 10px rgba(139, 92, 246, 0.4)",
        badgeBg: isLight ? "rgba(124, 58, 237, 0.15)" : "rgba(139, 92, 246, 0.2)",
        badgeBorder: isLight ? "#7C3AED" : "#8B5CF6",
        dotColor: "#C084FC",
      };
    case "idle":
      return {
        state: "idle",
        label: "Idle",
        color: isLight ? "#475569" : "#64748B",
        glow: "none",
        badgeBg: isLight ? "rgba(71, 85, 105, 0.1)" : "rgba(100, 116, 139, 0.15)",
        badgeBorder: isLight ? "#94A3B8" : "#475569",
        dotColor: "#94A3B8",
      };
    case "waiting":
    default:
      return {
        state: "waiting",
        label: "Waiting",
        color: isLight ? "#D97706" : "#F59E0B",
        glow: "0 0 8px rgba(245, 158, 11, 0.35)",
        badgeBg: isLight ? "rgba(217, 119, 6, 0.12)" : "rgba(245, 158, 11, 0.18)",
        badgeBorder: isLight ? "#D97706" : "#F59E0B",
        dotColor: "#FBBF24",
      };
  }
}
