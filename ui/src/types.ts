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
  prompt?: string | null;
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
  diff?: string | null;
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

export type GitAuthoringMode = 'co_authored' | 'julius_only' | 'user_only';

export interface CommunitySettings {
  default_model: string;
  auto_find_issues: boolean;
  export_as_pr: boolean;
  git_commit_authoring: GitAuthoringMode;
  only_respond_to_mentions: boolean;
  open_pr_as_draft: boolean;
  cdp_url: string;
  workspaces_root: string;
  github_token_masked?: string | null;
  cloud_api_key_masked?: string | null;
  has_github_token: boolean;
  has_cloud_api_key: boolean;
}

export interface SecretsUpdateRequest {
  github_token?: string | null;
  gemini_api_key?: string | null;
  openai_api_key?: string | null;
}

export interface SessionRecord {
  task_id: string;
  repo: string;
  title: string;
  prompt?: string | null;
  persona: string;
  status: TaskStatus;
  branch?: string | null;
  worktree_path?: string | null;
  diff?: string | null;
  pr_url?: string | null;
  created_at: string;
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
  settings?: CommunitySettings;
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
