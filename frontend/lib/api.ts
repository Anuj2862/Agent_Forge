import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

/* ── Interfaces ─────────────────────────────────────────────────── */

export interface AgentConfig {
  agent_id: string;
  name: string;
  role: string;
  objective: string;
  system_prompt?: string;
  tools: string[];
  inputs?: string[];
  outputs?: string[];
}

export interface Connection {
  source: string;
  target: string;
  data_type?: string;
}

export interface ArchitectureSpec {
  architecture_id: string;
  task_id: string;
  topology: string;
  agents: AgentConfig[];
  connections: Connection[];
  meta_reasoning?: string;
}

export interface EvaluationMetrics {
  task_success: number;
  quality: number;
  completeness: number;
  execution_time_seconds: number;
  agent_count: number;
  tool_call_count: number;
  accuracy?: number;
  efficiency?: number;
  overall_score?: number;
  verification_confidence?: string;
}

export interface ReflectionIssue {
  category: string;
  description: string;
  severity: string;
  affected_component?: string;
}

export interface ArchitecturalRecommendation {
  action: string;
  reason: string;
  priority?: string;
  details?: Record<string, unknown>;
}

export interface ReflectionResult {
  reflection_id: string;
  task_id?: string;
  architecture_id?: string;
  reflection_summary: string;
  identified_issues: ReflectionIssue[];
  recommendations: ArchitecturalRecommendation[];
}

export interface ToolCallLog {
  tool: string;
  query?: string;
  output?: string;
  duration?: number;
  latency_ms?: number;
}

export interface AgentLog {
  agent_id: string;
  agent_name?: string;
  role: string;
  status: string;
  execution_time?: number;
  execution_time_seconds?: number;
  output_preview?: string;
  tool_calls?: ToolCallLog[];
  output?: unknown;
}

export interface ExecutionEvent {
  event_id: string;
  execution_id: string;
  task_id: string;
  sequence_number: number;
  event_type: string;
  timestamp: string;
  status: string;
  agent_id?: string;
  stage: string;
  message: string;
  data: Record<string, unknown>;
  error?: string;
}


export interface TaskSubmitResponse {
  task_id: string;
  task_spec: Record<string, unknown>;
  architecture_spec: ArchitectureSpec;
  message: string;
  execution_id?: string;
  stream_url?: string;
}

export interface MemoryRecord {
  record_id: string;
  task_id: string;
  user_prompt?: string;
  task_type: string;
  complexity?: string;
  topology: string;
  agent_count: number;
  tools_used?: string[];
  success_rating: number;
  run_number: number;
  timestamp: string;
  task_spec?: {
    task_id: string;
    user_prompt?: string;
    task_type?: string;
    complexity?: string;
  };
  recommendation_summary?: string;
  architecture_spec?: ArchitectureSpec | Record<string, unknown>;
  evaluation_result?: Record<string, unknown>;
  reflection_result?: ReflectionResult | Record<string, unknown>;
}

export interface EvolveArchitectureResponse {
  task_id: string;
  base_architecture_id: string;
  evolved_architecture_id: string;
  evolved_architecture: ArchitectureSpec;
  run_number: number;
  modifications_applied: string[];
  message: string;
}

export interface MetricDeltas {
  task_success: number;
  quality: number;
  accuracy: number;
  completeness: number;
  duration_seconds: number;
  agent_count: number;
  overall_score: number;
}

export interface ArchitectureDiff {
  added_agents: AgentConfig[];
  removed_agents: AgentConfig[];
  added_connections: { source: string; target: string }[];
  removed_connections: { source: string; target: string }[];
  topology_changed: boolean;
  initial_topology: string;
  evolved_topology: string;
}

export interface EvolutionDecision {
  decision_id: string;
  task_id: string;
  status: "ACCEPTED" | "REJECTED" | "INCONCLUSIVE";
  v1_architecture_id: string;
  v2_architecture_id: string;
  v1_execution_id?: string;
  v2_execution_id?: string;
  v1_evaluation_id?: string;
  v2_evaluation_id?: string;
  v1_overall_score: number;
  v2_overall_score: number;
  score_delta: number;
  metric_deltas: Record<string, number>;
  hard_constraints_satisfied: boolean;
  validation_errors: string[];
  reason_codes: string[];
  rationale: string;
  decision_timestamp?: string;
  policy_version?: string;
}

export interface TaskDetail {
  task_id: string;
  user_prompt: string;
  task_type?: string;
  complexity?: string;
  status: string;
  run_number: number;
  task_spec: Record<string, unknown>;
  architecture_spec?: ArchitectureSpec;
  architecture_versions?: Record<string, ArchitectureSpec>;
  executions?: ExecutionDetail[];
  evaluations?: Record<string, EvaluationDetail>;
  latest_evaluation?: EvaluationDetail;
  latest_evaluation_id?: string;
  evolution_decision?: EvolutionDecision | null;
  created_at?: string;
  updated_at?: string;
}

export interface ExecutionDetail {
  execution_id: string;
  task_id: string;
  run_number: number;
  status: string;
  architecture_id: string;
  results?: Record<string, unknown>;
  agent_logs: AgentLog[];
  errors?: string[];
  error?: string;
  duration_seconds: number;
  total_tool_calls?: number;
  total_steps?: number;
  agent_count?: number;
  tool_call_count?: number;
  overall_success_rate?: number;
  step_history?: unknown[];
  agent_traces?: unknown[];
  final_output?: string;
  raw_output?: string;
}

export interface EvaluationDetail {
  evaluation_id?: string;
  execution_id?: string;
  task_id?: string;
  run_number?: number;
  metrics?: EvaluationMetrics & { verification_status?: string };
  failure_diagnosis?: Record<string, unknown>;
  reflection_result?: ReflectionResult;
  success_rating?: number;
  recommendation_summary?: string;
  memory_record_id?: string;
  evaluation_result?: {
    evaluation_id?: string;
    metrics?: EvaluationMetrics & { verification_status?: string };
    feedback_summary?: string;
  };
}

export interface HealthResponse {
  status: string;
  version?: string;
  mode?: string;
  database?: string;
  error?: string;
}

export interface TaskComparisonResponse {
  task_id: string;
  has_comparison: boolean;
  run_1: { evaluation: EvaluationDetail; architecture: ArchitectureSpec } | null;
  run_2: { evaluation: EvaluationDetail; architecture: ArchitectureSpec } | null;
  deltas: MetricDeltas | null;
  architecture_diff: ArchitectureDiff | null;
  evolution_decision?: EvolutionDecision | null;
}

/* ── Task API ────────────────────────────────────────────────────── */

export interface TaskSubmitOptions {
  user_prompt: string;
  run_number?: number;
  max_agents?: number;
  forbidden_tools?: string[];
  allowed_tools?: string[];
  require_verification?: boolean;
  auto_pipeline?: boolean;
  constraints?: Record<string, unknown> | string[];
}

export async function submitTask(
  promptOrOptions: string | TaskSubmitOptions,
  run_number = 1
): Promise<TaskSubmitResponse> {
  const payload =
    typeof promptOrOptions === "string"
      ? { user_prompt: promptOrOptions, run_number }
      : { run_number: 1, ...promptOrOptions };
  const r = await api.post<TaskSubmitResponse>("/tasks/submit", payload);
  return r.data;
}

export async function listTasks(): Promise<{ tasks: TaskDetail[]; total: number }> {
  const r = await api.get("/tasks/");
  return r.data;
}

export async function getTask(task_id: string): Promise<TaskDetail> {
  const r = await api.get(`/tasks/${task_id}`);
  return r.data;
}

/* ── Architecture API ────────────────────────────────────────────── */

export async function listArchitectures(): Promise<{ architectures: ArchitectureSpec[] }> {
  const r = await api.get("/architectures/");
  return r.data;
}

export async function getArchitectureForTask(task_id: string): Promise<ArchitectureSpec> {
  const r = await api.get(`/architectures/task/${task_id}`);
  return r.data;
}

export async function getArchitectureVersions(task_id: string): Promise<{
  task_id: string;
  current_version: string;
  versions: Record<string, ArchitectureSpec>;
}> {
  const r = await api.get(`/architectures/task/${task_id}/versions`);
  return r.data;
}

export async function evolveArchitecture(
  task_id: string,
  architecture_id?: string,
  reflection_id?: string
): Promise<EvolveArchitectureResponse> {
  const r = await api.post<EvolveArchitectureResponse>("/architectures/evolve", {
    task_id,
    architecture_id,
    reflection_id,
  });
  return r.data;
}

/* ── Execution API ───────────────────────────────────────────────── */

export async function runExecution(task_id: string, run_number = 1): Promise<ExecutionDetail> {
  const r = await api.post("/execution/run", { task_id, run_number });
  return r.data;
}

export async function startExecutionAsync(
  task_id: string,
  run_number = 1,
  use_real_engine = true
): Promise<{
  execution_id: string;
  task_id: string;
  architecture_id: string;
  run_number: number;
  status: string;
  stream_url: string;
}> {
  const r = await api.post("/execution/start", { task_id, run_number, use_real_engine });
  return r.data;
}

export async function listExecutions(): Promise<{ executions: ExecutionDetail[]; total: number }> {
  const r = await api.get("/execution/");
  return r.data;
}

export async function getExecution(execution_id: string): Promise<ExecutionDetail> {
  const r = await api.get(`/execution/${execution_id}`);
  return r.data;
}

export async function getExecutionEventsHistory(
  execution_id: string,
  after_seq = 0
): Promise<{ execution_id: string; count: number; events: ExecutionEvent[] }> {
  const r = await api.get(`/execution/${execution_id}/events/history`, {
    params: { after_seq },
  });
  return r.data;
}

export function subscribeToExecutionEvents(
  execution_id: string,
  callbacks: {
    onEvent: (event: ExecutionEvent) => void;
    onError?: (error: Event) => void;
    onOpen?: () => void;
  },
  afterSeq = 0
): () => void {
  if (typeof window === "undefined") {
    return () => {};
  }

  const url = `${API_BASE_URL}/execution/${execution_id}/events${afterSeq > 0 ? `?after_seq=${afterSeq}` : ""}`;
  const es = new EventSource(url);

  if (callbacks.onOpen) {
    es.onopen = callbacks.onOpen;
  }

  es.onmessage = (e) => {
    try {
      const parsed: ExecutionEvent = JSON.parse(e.data);
      callbacks.onEvent(parsed);
    } catch {
      // Non-JSON or keepalive lines ignored
    }
  };

  // Add event listeners for all known event types in taxonomy
  const eventTypes = [
    "execution.queued",
    "execution.started",
    "execution.stage_started",
    "agent.started",
    "agent.action",
    "tool.started",
    "tool.completed",
    "tool.failed",
    "agent.completed",
    "execution.stage_completed",
    "evaluation.started",
    "evaluation.completed",
    "evolution.proposed",
    "evolution.validated",
    "evolution.accepted",
    "evolution.rejected",
    "execution.warning",
    "execution.failed",
    "execution.cancelled",
    "execution.completed",
  ];

  eventTypes.forEach((evt) => {
    es.addEventListener(evt, (e: MessageEvent) => {
      try {
        const parsed: ExecutionEvent = JSON.parse(e.data);
        callbacks.onEvent(parsed);
        if (
          parsed.event_type === "execution.completed" ||
          parsed.event_type === "execution.failed" ||
          parsed.event_type === "execution.cancelled"
        ) {
          es.close();
        }
      } catch {
        // Ignored
      }
    });
  });

  if (callbacks.onError) {
    es.onerror = callbacks.onError;
  }

  return () => {
    es.close();
  };
}

/* ── Evaluation API ──────────────────────────────────────────────── */

export async function evaluateExecution(execution_id: string, task_id: string): Promise<EvaluationDetail> {
  const r = await api.post("/evaluation/evaluate", { execution_id, task_id });
  return r.data;
}

export async function listEvaluations(): Promise<{ evaluations: EvaluationDetail[]; total: number }> {
  const r = await api.get("/evaluation/");
  return r.data;
}

export async function getEvaluation(evaluation_id: string): Promise<EvaluationDetail> {
  const r = await api.get(`/evaluation/${evaluation_id}`);
  return r.data;
}

export async function compareTaskRuns(task_id: string): Promise<TaskComparisonResponse> {
  const r = await api.get<TaskComparisonResponse>(`/evaluation/compare/${task_id}`);
  return r.data;
}

/* ── Memory API ──────────────────────────────────────────────────── */

export async function getMemoryHistory(
  page = 1,
  page_size = 20,
  task_type?: string,
  min_success_rating?: number
): Promise<{ records: MemoryRecord[]; total: number; page: number; page_size: number }> {
  const r = await api.get("/memory/history", {
    params: { page, page_size, task_type, min_success_rating },
  });
  return r.data;
}

export async function retrieveSimilarExperiences(
  task_type: string,
  complexity = "medium",
  limit = 3
): Promise<{ query: Record<string, unknown>; count: number; experiences: MemoryRecord[] }> {
  const r = await api.get("/memory/retrieve", {
    params: { task_type, complexity, limit },
  });
  return r.data;
}

export async function getTaskEvolutionHistory(task_id: string): Promise<{
  task_id: string;
  run_count: number;
  runs: Array<Record<string, unknown>>;
}> {
  const r = await api.get(`/memory/task/${task_id}/history`);
  return r.data;
}

export async function getMemoryStatus(): Promise<{
  status: string;
  module: string;
  total_records: number;
}> {
  const r = await api.get("/memory/");
  return r.data;
}

/* ── Health & Platform Diagnostics ───────────────────────────────── */

export async function getHealth(): Promise<HealthResponse> {
  const r = await api.get("/health");
  return r.data;
}

/* ── Platform Settings, Tool Registry & Model Matrix API ────────── */

export interface ToolMetadata {
  name: string;
  display_name: string;
  description: string;
  category: string;
  safety_classification: string;
  implementation_status: string;
  enabled: boolean;
  required_credentials: string[];
  credentials_configured: boolean;
  input_schema: Record<string, unknown>;
  last_tested_at?: string;
  last_test_status?: string;
  last_test_latency_ms?: number;
}

export interface ToolTestResponse {
  tool_name: string;
  status: string;
  duration_ms: number;
  output_preview: string;
  error?: string;
  tested_at: string;
}

export interface RoleModelConfig {
  role: string;
  provider: string;
  model_identifier: string;
  temperature: number;
  is_supported: boolean;
  credential_status: string;
}

export interface ModelMatrixConfig {
  roles: Record<string, RoleModelConfig>;
  supported_providers: string[];
  unsupported_providers: string[];
}

export interface ExecutionPolicyConfig {
  max_agents: number;
  max_execution_duration_seconds: number;
  max_tool_calls_per_agent: number;
  allowed_tools: string[];
  forbidden_tools: string[];
  require_verification_by_default: boolean;
  sandbox_isolation_enabled: boolean;
}

export interface SubsystemHealth {
  name: string;
  status: string;
  latency_ms?: number;
  details: Record<string, unknown>;
  error?: string;
  checked_at: string;
}

export interface SystemHealthResponse {
  overall_status: string;
  version: string;
  environment: string;
  subsystems: Record<string, SubsystemHealth>;
  checked_at: string;
}

export interface SettingsSummaryResponse {
  version: string;
  tools: ToolMetadata[];
  model_matrix: ModelMatrixConfig;
  execution_policies: ExecutionPolicyConfig;
  health_summary: SystemHealthResponse;
}

export async function getSettingsSummary(): Promise<SettingsSummaryResponse> {
  const r = await api.get<SettingsSummaryResponse>("/settings/");
  return r.data;
}

export async function listRegisteredTools(): Promise<ToolMetadata[]> {
  const r = await api.get<ToolMetadata[]>("/settings/tools");
  return r.data;
}

export async function getToolMetadata(toolName: string): Promise<ToolMetadata> {
  const r = await api.get<ToolMetadata>(`/settings/tools/${toolName}`);
  return r.data;
}

export async function toggleTool(toolName: string, enabled: boolean): Promise<ToolMetadata> {
  const r = await api.post<ToolMetadata>(`/settings/tools/${toolName}/toggle`, { enabled });
  return r.data;
}

export async function testRegisteredTool(
  toolName: string,
  testInput?: Record<string, unknown>
): Promise<ToolTestResponse> {
  const r = await api.post<ToolTestResponse>(`/settings/tools/${toolName}/test`, {
    test_input: testInput,
  });
  return r.data;
}

export async function getModelMatrix(): Promise<ModelMatrixConfig> {
  const r = await api.get<ModelMatrixConfig>("/settings/models");
  return r.data;
}

export async function updateModelMatrix(
  assignments: Record<string, Partial<RoleModelConfig>>
): Promise<ModelMatrixConfig> {
  const r = await api.put<ModelMatrixConfig>("/settings/models", { assignments });
  return r.data;
}

export async function getExecutionPolicies(): Promise<ExecutionPolicyConfig> {
  const r = await api.get<ExecutionPolicyConfig>("/settings/policies");
  return r.data;
}

export async function updateExecutionPolicies(
  update: Partial<ExecutionPolicyConfig>
): Promise<ExecutionPolicyConfig> {
  const r = await api.put<ExecutionPolicyConfig>("/settings/policies", update);
  return r.data;
}

export async function getRuntimeHealth(): Promise<SystemHealthResponse> {
  const r = await api.get<SystemHealthResponse>("/settings/health");
  return r.data;
}

