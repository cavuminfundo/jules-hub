/**
 * Jules Hub API Client and SSE EventSource Streaming Hooks.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import type {
  CDPResponse,
  CreatePrResponse,
  EscalateRequest,
  HealthResponse,
  HubConfig,
  OllamaInstance,
  OllamaProbeResult,
  ProjectInfo,
  PruneResponse,
  RunRequest,
  RunResponse,
  SeniorReviewResult,
  SSELogPayload,
  Suggestion,
  TaskStatus,
  TriggerSchedulerResponse,
  WorktreePruneRequest,
  WorktreeSessionInfo,
} from './types';

const BASE_URL = '';

/**
 * Custom error class for API failures
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public detail: string
  ) {
    super(`API Error ${status}: ${detail || statusText}`);
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    let detail = '';
    try {
      const errJson = await response.json();
      detail = errJson.detail || JSON.stringify(errJson);
    } catch {
      detail = await response.text();
    }
    throw new ApiError(response.status, response.statusText, detail);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getHealth: () => request<HealthResponse>('/api/health'),

  getProjects: () => request<ProjectInfo[]>('/api/projects'),

  getSuggestions: (repo?: string, mode?: string, category?: string) => {
    const params = new URLSearchParams();
    if (repo) params.set('repo', repo);
    if (mode && mode !== 'all') params.set('mode', mode);
    if (category && category !== 'all') params.set('category', category);

    const query = params.toString() ? `?${params.toString()}` : '';
    return request<Suggestion[]>(`/api/suggestions${query}`);
  },

  discardSuggestion: (suggestionId: string) =>
    request<{ success: boolean; discarded_id: string }>(
      `/api/suggestions/${encodeURIComponent(suggestionId)}/discard`,
      { method: 'POST' }
    ),

  runTask: (payload: RunRequest, background = false) => {
    const query = background ? '?background=true' : '';
    return request<RunResponse>(`/api/run${query}`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  escalateToAntigravity: (payload: EscalateRequest) =>
    request<CDPResponse>('/api/escalate', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getWorktrees: () => request<WorktreeSessionInfo[]>('/api/worktrees'),

  pruneWorktrees: (payload?: WorktreePruneRequest) =>
    request<PruneResponse>('/api/worktrees/prune', {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }),

  getConfig: () => request<HubConfig>('/api/config'),

  updateConfig: (config: HubConfig) =>
    request<HubConfig>('/api/config', {
      method: 'PUT',
      body: JSON.stringify(config),
    }),

  testOllamaInstance: (instance: OllamaInstance) =>
    request<OllamaProbeResult>('/api/ollama/test', {
      method: 'POST',
      body: JSON.stringify(instance),
    }),

  testOllama: (instance: OllamaInstance) =>
    request<OllamaProbeResult>('/api/ollama/test', {
      method: 'POST',
      body: JSON.stringify(instance),
    }),

  getOllamaModels: (instanceId: number) =>
    request<OllamaProbeResult>(`/api/ollama/instances/${instanceId}/models`),

  getCdpModels: () => request<string[]>('/api/cdp/models'),

  runSeniorReview: (taskId: string, diffText?: string) => {
    const query = diffText ? `?diff_text=${encodeURIComponent(diffText)}` : '';
    return request<SeniorReviewResult>(
      `/api/tasks/${encodeURIComponent(taskId)}/senior-review${query}`,
      {
        method: 'POST',
        body: JSON.stringify({ diff_text: diffText }),
      }
    );
  },

  seniorReview: (taskId: string, diffText?: string) => {
    const query = diffText ? `?diff_text=${encodeURIComponent(diffText)}` : '';
    return request<SeniorReviewResult>(
      `/api/tasks/${encodeURIComponent(taskId)}/senior-review${query}`,
      {
        method: 'POST',
        body: JSON.stringify({ diff_text: diffText }),
      }
    );
  },

  createPullRequest: (taskId: string) =>
    request<CreatePrResponse>(`/api/tasks/${encodeURIComponent(taskId)}/create-pr`, {
      method: 'POST',
    }),

  createPr: (taskId: string) =>
    request<CreatePrResponse>(`/api/tasks/${encodeURIComponent(taskId)}/create-pr`, {
      method: 'POST',
    }),

  triggerScheduler: (repoName: string) =>
    request<TriggerSchedulerResponse>(
      `/api/scheduler/${encodeURIComponent(repoName)}/trigger`,
      { method: 'POST' }
    ),
};

/**
 * Helper to subscribe to SSE log stream directly with callback
 */
export function subscribeToTaskLogs(
  taskId: string,
  onEvent: (data: SSELogPayload) => void,
  onError?: (error: Event) => void
): () => void {
  const es = new EventSource(`/api/stream/${encodeURIComponent(taskId)}`);

  es.onmessage = (event) => {
    try {
      const payload: SSELogPayload = JSON.parse(event.data);
      onEvent(payload);
      if (payload.done) {
        es.close();
      }
    } catch (e) {
      console.error('Failed to parse SSE event data', e);
    }
  };

  es.onerror = (err) => {
    if (onError) onError(err);
    es.close();
  };

  return () => {
    es.close();
  };
}

/**
 * React hook to listen to task SSE logs and track status
 */
export function useTaskLogs(taskId: string | null) {
  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<TaskStatus>('pending');
  const [isDone, setIsDone] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    setLogs([]);
    setStatus('pending');
    setIsDone(false);
    setError(null);
  }, []);

  useEffect(() => {
    if (!taskId) {
      reset();
      return;
    }

    setLogs([]);
    setStatus('running');
    setIsDone(false);
    setError(null);

    const es = new EventSource(`/api/stream/${encodeURIComponent(taskId)}`);
    esRef.current = es;

    es.onmessage = (event) => {
      try {
        const payload: SSELogPayload = JSON.parse(event.data);
        if (payload.log) {
          setLogs((prev) => [...prev, payload.log!]);
        }
        if (payload.status) {
          setStatus(payload.status as TaskStatus);
        }
        if (payload.done) {
          setIsDone(true);
          es.close();
        }
      } catch (e) {
        console.error('SSE JSON parse error', e);
      }
    };

    es.onerror = (err) => {
      console.warn('SSE stream error or task not found:', err);
      setError('Connection to task log stream lost or task ended.');
      es.close();
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [taskId, reset]);

  return { logs, status, isDone, error, reset };
}
