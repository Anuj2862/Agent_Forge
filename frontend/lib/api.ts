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
