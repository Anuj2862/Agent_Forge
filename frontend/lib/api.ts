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
  details?: Record<string, any>;
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
  output?: any;
}

export interface TaskSubmitResponse {
  task_id: string;
  task_spec: any;
  architecture_spec: ArchitectureSpec;
  message: string;
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
  architecture_spec?: any;
  evaluation_result?: any;
  reflection_result?: any;
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

export interface TaskComparisonResponse {
  task_id: string;
  has_comparison: boolean;
  run_1: { evaluation: any; architecture: ArchitectureSpec } | null;
  run_2: { evaluation: any; architecture: ArchitectureSpec } | null;
  deltas: MetricDeltas | null;
  architecture_diff: ArchitectureDiff | null;
}

/* ── Task API ────────────────────────────────────────────────────── */

export async function submitTask(
  user_prompt: string,
  run_number = 1
): Promise<TaskSubmitResponse> {
  const r = await api.post<TaskSubmitResponse>("/tasks/submit", { user_prompt, run_number });
  return r.data;
}

export async function listTasks(): Promise<{ tasks: any[]; total: number }> {
  const r = await api.get("/tasks/");
  return r.data;
}

export async function getTask(task_id: string): Promise<any> {
  const r = await api.get(`/tasks/${task_id}`);
  return r.data;
}

/* ── Architecture API ────────────────────────────────────────────── */

export async function listArchitectures(): Promise<{ architectures: any[] }> {
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

export async function runExecution(task_id: string, run_number = 1): Promise<any> {
  const r = await api.post("/execution/run", { task_id, run_number });
  return r.data;
}

export async function listExecutions(): Promise<{ executions: any[]; total: number }> {
  const r = await api.get("/execution/");
  return r.data;
}

export async function getExecution(execution_id: string): Promise<any> {
  const r = await api.get(`/execution/${execution_id}`);
  return r.data;
}

/* ── Evaluation API ──────────────────────────────────────────────── */

export async function evaluateExecution(execution_id: string, task_id: string): Promise<any> {
  const r = await api.post("/evaluation/evaluate", { execution_id, task_id });
  return r.data;
}

export async function listEvaluations(): Promise<{ evaluations: any[]; total: number }> {
  const r = await api.get("/evaluation/");
  return r.data;
}

export async function getEvaluation(evaluation_id: string): Promise<any> {
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
): Promise<{ query: any; count: number; experiences: any[] }> {
  const r = await api.get("/memory/retrieve", {
    params: { task_type, complexity, limit },
  });
  return r.data;
}

export async function getTaskEvolutionHistory(task_id: string): Promise<{
  task_id: string;
  run_count: number;
  runs: any[];
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

/* ── Health ──────────────────────────────────────────────────────── */

export async function getHealth(): Promise<any> {
  const r = await api.get("/health");
  return r.data;
}
