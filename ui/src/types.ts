/**
 * TypeScript interfaces mirroring Pydantic v2 data models from hub/models.py
 */

export type EngineMode = 'antigravity_flash' | 'local' | 'hybrid';

export type TaskStatus =
  | 'pending'
  | 'running'
  | 'testing'
  | 'passed'
  | 'retry'
  | 'failed'
  | 'needs_escalation'
  | 'completed';

export type PersonaType = 'bolt' | 'palette' | 'sentinel';

export interface Suggestion {
  id: string;
  persona: string;
  category: string;
  title: string;
  file: string;
  line: number;
  issue: string;
  impact: string;
  code_snippet: string;
}

export interface WorktreeSessionInfo {
  worktree_path: string;
  branch: string;
  repo_name: string;
  persona: string;
  created_at?: string | null;
  is_active: boolean;
}

export interface RunRequest {
  repo: string;
  persona?: string;
  target_file?: string | null;
  issue_context?: string | null;
  mode?: EngineMode;
  branch?: string | null;
  dry_run?: boolean;
}

export interface RunResponse {
  task_id: string;
  status: TaskStatus;
  worktree_path?: string | null;
  branch?: string | null;
  message: string;
}

export interface EscalateRequest {
  repo: string;
  worktree_path: string;
  branch: string;
  diff_summary: string;
  test_status: string;
  instruction?: string;
}

export interface CDPResponse {
  success: boolean;
  message: string;
  response_data?: Record<string, unknown> | null;
  error?: string | null;
}

export interface WorktreePruneRequest {
  worktree_path?: string | null;
  repo_name?: string | null;
  force?: boolean;
}

export interface PruneResponse {
  success: boolean;
  message: string;
}

export interface PatchResult {
  success: boolean;
  diff?: string | null;
  lines_changed: number;
  error?: string | null;
  engine_used?: string | null;
}

export interface ProjectInfo {
  name: string;
  path: string;
  description?: string;
  active_branch?: string | null;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

export interface SSELogPayload {
  task_id: string;
  log?: string;
  status?: string;
  done?: boolean;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
}

export interface OllamaInstance {
  id: number;
  name: string;
  url: string;
  enabled: boolean;
  timeout_sec: number;
}

export interface OllamaProbeResult {
  online_status: boolean;
  latency_ms: number;
  models_list: string[];
  error?: string | null;
}

export interface RoleModelConfig {
  provider: string; // 'ollama' | 'antigravity_cli' | 'cdp'
  instance_id: number;
  model_name: string;
  fallback_provider?: string;
  fallback_instance_id?: number;
  fallback_model?: string;
}

export interface RepoScheduleConfig {
  repo_name: string;
  enabled: boolean;
  interval_hours: number;
  personas: string[];
  max_pending_worktrees: number;
  last_run_at?: string | null;
  next_run_at?: string | null;
}

export interface HubConfig {
  ollama_instances: OllamaInstance[];
  junior_config: RoleModelConfig;
  senior_config: RoleModelConfig;
  senior_mode: string; // 'in_cockpit' | 'cdp'
  cdp_host: string;
  cdp_port: number;
  max_diff_lines: number;
  repo_schedules: RepoScheduleConfig[];
}

export interface SeniorReviewResult {
  verdict: 'APPROVED' | 'REJECTED';
  simple_explanation: string;
  security_notes: string;
  reviewer_model: string;
  reviewed_at?: string;
}

export interface CreatePrResponse {
  success: boolean;
  task_id: string;
  pr_url: string;
  message: string;
}

export interface TriggerSchedulerResponse {
  repo_name: string;
  triggered: boolean;
  triggered_at?: string;
  status?: string;
}
