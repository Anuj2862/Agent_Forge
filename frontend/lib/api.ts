import axios from "axios";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface AgentConfig {
  agent_id: string;
  name: string;
  role: string;
  objective: string;
  system_prompt?: string;
  tools: string[];
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

export async function submitTask(
  user_prompt: string,
  run_number: number = 1
): Promise<TaskSubmitResponse> {
  const response = await api.post<TaskSubmitResponse>("/tasks/submit", {
    user_prompt,
    run_number,
  });
  return response.data;
}

export async function runExecution(
  task_id: string,
  run_number: number = 1
): Promise<any> {
  const response = await api.post("/execution/run", {
    task_id,
    run_number,
  });
  return response.data;
}

export async function evaluateExecution(
  execution_id: string,
  task_id: string
): Promise<any> {
  const response = await api.post("/evaluation/evaluate", {
    execution_id,
    task_id,
  });
  return response.data;
}

export async function getMemoryHistory(
  page: number = 1,
  page_size: number = 20
): Promise<{ records: MemoryRecord[]; total: number }> {
  const response = await api.get("/memory/history", {
    params: { page, page_size },
  });
  return response.data;
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
  run_1: {
    evaluation: any;
    architecture: ArchitectureSpec;
  } | null;
  run_2: {
    evaluation: any;
    architecture: ArchitectureSpec;
  } | null;
  deltas: MetricDeltas | null;
  architecture_diff: ArchitectureDiff | null;
}

export async function evolveArchitecture(
  task_id: string,
  architecture_id?: string,
  reflection_id?: string
): Promise<EvolveArchitectureResponse> {
  const response = await api.post<EvolveArchitectureResponse>("/architectures/evolve", {
    task_id,
    architecture_id,
    reflection_id,
  });
  return response.data;
}

export async function compareTaskRuns(
  task_id: string
): Promise<TaskComparisonResponse> {
  const response = await api.get<TaskComparisonResponse>(`/evaluation/compare/${task_id}`);
  return response.data;
}

export async function getArchitectureVersions(
  task_id: string
): Promise<{ task_id: string; current_version: string; versions: Record<string, ArchitectureSpec> }> {
  const response = await api.get(`/architectures/task/${task_id}/versions`);
  return response.data;
}
